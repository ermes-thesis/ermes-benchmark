import os
import sys
import pandas as pd
import re
import pytz
from datetime import datetime, timedelta

# --- CONFIGURAZIONE ---
# Codici di errore HTTP da monitorare
HTTP_ERROR_CODES = [404, 423, 500, 503, 508]
# Intervallo in secondi per il calcolo dei Round
ROUND_INTERVAL_SECONDS = 15
# Numero di round da tagliare per il file "Steady State"
WARMUP_ROUNDS = 5

def parse_timestamp(ts: str) -> datetime:
    """Converte la stringa timestamp dei log in oggetto datetime."""
    if sys.version_info >= (3, 11):
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            pass

    ts = str(ts).strip().rstrip('Z')

    if '.' in ts:
        try:
            main, frac = ts.split('.')
            frac = (frac + "000000")[:6]
            ts = f"{main}.{frac}"
            fmt = '%Y-%m-%dT%H:%M:%S.%f'
        except ValueError:
            fmt = '%Y-%m-%dT%H:%M:%S'
    else:
        fmt = '%Y-%m-%dT%H:%M:%S'

    try:
        return datetime.strptime(ts, fmt).replace(tzinfo=pytz.utc)
    except ValueError:
        return datetime.now(pytz.utc)

def extract_config_from_folder(folder_name):
    """Estrae parametri dal nome della cartella principale (Smart V2 Logic)."""
    mode_match = re.search(r'mode_([^_]+)', folder_name)
    users_match = re.search(r'users_(\d+)', folder_name)
    coll_match = re.search(r'collections_(\d+)', folder_name)
    acc_match = re.search(r'accesses_(\d+)', folder_name)

    config = {
        'Mode': mode_match.group(1) if mode_match else 'unknown',
    }

    # Se ci sono utenti/collezioni (Scalability Test)
    if users_match:
        config['Users'] = int(users_match.group(1))
    else:
        config['Users'] = 64 # Default fisso se siamo in Density test

    if coll_match:
        config['Collections'] = int(coll_match.group(1))
    else:
        config['Collections'] = 100 # Default fisso se siamo in Density test

    # Se ci sono accessi (Density Test)
    if acc_match:
        config['Accesses'] = int(acc_match.group(1))
        config['TestType'] = 'Density'
    else:
        config['Accesses'] = 1 # Default
        config['TestType'] = 'Scalability'

    return config

def calculate_metrics(df, seed=None):
    """Calcola le metriche su un DataFrame (V2 Logic con Throughput)."""
    if df is None or df.empty:
        return None

    if 'StatusCode' not in df.columns:
        df['StatusCode'] = 200

    # Metriche statistiche
    avg_latency = df['FuncDuration'].mean()
    median_latency = df['FuncDuration'].median()
    variance_latency = df['FuncDuration'].var()

    Q1 = df['FuncDuration'].quantile(0.25)
    Q2 = df['FuncDuration'].quantile(0.5)
    Q3 = df['FuncDuration'].quantile(0.75)
    Q4 = df['FuncDuration'].quantile(1.0)

    total_requests = len(df)
    correct_requests = len(df[df['StatusCode'] == 200])
    failed_requests = total_requests - correct_requests

    error_code_counts = {code: len(df[df['StatusCode'] == code]) for code in HTTP_ERROR_CODES}
    other_errors = len(df[(df['StatusCode'] != 200) & (~df['StatusCode'].isin(HTTP_ERROR_CODES))])

    # Calcolo Throughput (Richieste / Secondo) basato sulla durata effettiva del test nel chunk
    try:
        # Se i timestamp sono stringhe, li parsiamo al volo per calcolare la durata
        if pd.api.types.is_string_dtype(df['StartTime']):
            times = df['StartTime'].apply(parse_timestamp)
            min_time = times.min()
            max_time = times.max()
        else:
            # Se sono già datetime (caso aggregazione rounds o post-parsing)
            min_time = df['StartTime'].min()
            max_time = df['StartTime'].max()

        duration = (max_time - min_time).total_seconds()
        throughput = total_requests / duration if duration > 0 else 0
    except:
        throughput = 0

    metrics = {
        'AverageLatency': avg_latency,
        'MedianLatency': median_latency,
        'VarianceLatency': variance_latency,
        'Throughput': throughput,
        'Q1': Q1, 'Q2': Q2, 'Q3': Q3, 'Q4': Q4,
        'TotalRequests': total_requests,
        'CorrectRequests': correct_requests,
        'FailedRequests': failed_requests,
        **error_code_counts,
        'OtherErrors': other_errors
    }

    if seed is not None:
        return {'Seed': seed, **metrics}

    return metrics

def calculate_metrics_by_round(df, seed, interval=ROUND_INTERVAL_SECONDS):
    """Raggruppa i dati per finestre temporali e produce il formato specifico richiesto."""
    ts_col = "StartTime"

    df_temp = df.copy()

    try:
        if not pd.api.types.is_datetime64_any_dtype(df_temp[ts_col]):
            df_temp['_dt'] = df_temp[ts_col].apply(parse_timestamp)
        else:
            df_temp['_dt'] = df_temp[ts_col]
    except Exception:
        return None

    df_temp = df_temp.sort_values('_dt')
    start_time_global = df_temp['_dt'].min()

    # Calcola indice round (0, 1, 2...)
    df_temp['_seconds'] = (df_temp['_dt'] - start_time_global).dt.total_seconds()
    df_temp['RoundIdx'] = (df_temp['_seconds'] // interval).astype(int)

    grouped = df_temp.groupby('RoundIdx')

    rows = []
    for round_idx, group in grouped:
        m = calculate_metrics(group)
        if m:
            t_start = start_time_global + timedelta(seconds=round_idx * interval)
            t_end = t_start + timedelta(seconds=interval)

            m['Seed'] = seed
            m['Round'] = round_idx + 1
            m['StartInterval'] = t_start
            m['EndInterval'] = t_end

            rows.append(m)

    if not rows:
        return None

    res_df = pd.DataFrame(rows)

    desired_order = [
        'Seed', 'Round', 'StartInterval', 'EndInterval',
        'AverageLatency', 'MedianLatency', 'VarianceLatency', 'Throughput',
        'Q1', 'Q2', 'Q3', 'Q4',
        'TotalRequests', 'CorrectRequests', 'FailedRequests'
    ]

    final_cols = [c for c in desired_order if c in res_df.columns]
    remaining = [c for c in res_df.columns if c not in final_cols]

    return res_df[final_cols + remaining]

def main():
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    global_aggregated_data = []        # Include tutto
    global_aggregated_data_cut = []    # Esclude i primi 5 round (Steady State)

    print(f"Scansione struttura cartelle in: {root_dir}")

    for root, dirs, files in os.walk(root_dir):
        folder_name = os.path.basename(root)

        # Criterio di identificazione cartella (Logic V2)
        if "mode_" in folder_name and ("users_" in folder_name or "accesses_" in folder_name):

            print(f"Elaborazione: {folder_name}")
            seed_dirs = [d for d in dirs if d.startswith("seed_")]

            if not seed_dirs:
                print(f"  -> Nessuna sottocartella 'seed_X' trovata.")
                continue

            # Accumulatori per questa configurazione
            folder_seed_metrics_summary = [] # 1 riga per seed (sommario)
            folder_rounds_dfs = []           # Dettaglio rounds di TUTTI i seed
            dfs_for_global_calc = []         # Raw data per calcolo globale finale

            for seed_dir in seed_dirs:
                try:
                    seed_val = int(seed_dir.split('_')[1])
                    seed_path = os.path.join(root, seed_dir)
                    csv_files = [os.path.join(seed_path, f) for f in os.listdir(seed_path) if f.endswith('.csv') and 'aggregated' not in f]

                    if not csv_files: continue

                    df_seed = pd.concat((pd.read_csv(f) for f in csv_files), ignore_index=True)

                    # Conversione us -> ms
                    df_seed['FuncDuration'] = df_seed['FuncDuration'] / 1000.0

                    # 1. Rounds (per file seed specifici)
                    df_rounds = calculate_metrics_by_round(df_seed, seed=seed_val, interval=ROUND_INTERVAL_SECONDS)
                    if df_rounds is not None: folder_rounds_dfs.append(df_rounds)

                    # 2. Summary Seed
                    m = calculate_metrics(df_seed, seed=seed_val)
                    if m: folder_seed_metrics_summary.append(m)

                    # 3. Global Raw Data
                    dfs_for_global_calc.append(df_seed)

                except Exception as e:
                    print(f"  -> Errore seed {seed_dir}: {e}")

            # === SALVATAGGI LOCALI ===

            # A. FILE UNICO ROUNDS
            if folder_rounds_dfs:
                pd.concat(folder_rounds_dfs, ignore_index=True).to_csv(os.path.join(root, "aggregated_rounds_all_seeds.csv"), index=False)

            # B. FILE SOMMARIO PER SEED
            if folder_seed_metrics_summary:
                pd.DataFrame(folder_seed_metrics_summary).to_csv(os.path.join(root, "aggregated_results_summary.csv"), index=False)

            # C. FILE AGGREGAZIONE GLOBALE PER ROUND (Tutti i seed normalizzati)
            if dfs_for_global_calc:
                try:
                    normalized_dfs = []
                    col_ts = 'StartTime'

                    for df_raw in dfs_for_global_calc:
                        d = df_raw.copy()
                        if '_dt' not in d.columns:
                            d['_dt'] = d[col_ts].apply(parse_timestamp)

                        seed_start_time = d['_dt'].min()
                        d['_rel_seconds'] = (d['_dt'] - seed_start_time).dt.total_seconds()
                        normalized_dfs.append(d)

                    if normalized_dfs:
                        df_global_rel = pd.concat(normalized_dfs, ignore_index=True)
                        df_global_rel['RoundIdx'] = (df_global_rel['_rel_seconds'] // ROUND_INTERVAL_SECONDS).astype(int)

                        global_round_rows = []
                        for r_idx, group in df_global_rel.groupby('RoundIdx'):
                            m = calculate_metrics(group)
                            if m:
                                m['Round'] = r_idx + 1
                                m['TimeRelativeStart'] = r_idx * ROUND_INTERVAL_SECONDS
                                m['TimeRelativeEnd'] = (r_idx + 1) * ROUND_INTERVAL_SECONDS
                                global_round_rows.append(m)

                        if global_round_rows:
                            df_global_rounds = pd.DataFrame(global_round_rows)
                            cols_order = ['Round', 'TimeRelativeStart', 'TimeRelativeEnd', 'AverageLatency', 'MedianLatency', 'Throughput']
                            existing_cols = [c for c in cols_order if c in df_global_rounds.columns]
                            other_cols = [c for c in df_global_rounds.columns if c not in existing_cols]
                            df_global_rounds[existing_cols + other_cols].to_csv(os.path.join(root, "aggregated_rounds_global.csv"), index=False)

                except Exception as e:
                    print(f"  -> Errore nel calcolo del file global rounds: {e}")

            # D. GLOBAL SUMMARY ROW (Standard + Steady State)
            if dfs_for_global_calc:
                try:
                    config_info = extract_config_from_folder(folder_name)

                    # --- 1. Calcolo Completo (Standard) ---
                    df_global_huge = pd.concat(dfs_for_global_calc, ignore_index=True)
                    global_metrics = calculate_metrics(df_global_huge, seed=None)
                    global_aggregated_data.append({**config_info, **global_metrics})

                    # --- 2. Calcolo Steady State (Taglio primi N round) ---
                    # Dobbiamo filtrare OGNI seed individualmente prima di concatenare,
                    # perché ogni seed ha il suo start time relativo a 0.
                    steady_dfs = []
                    cut_seconds = WARMUP_ROUNDS * ROUND_INTERVAL_SECONDS

                    for d_raw in dfs_for_global_calc:
                        d_temp = d_raw.copy()

                        # Assicuriamoci che sia parsed
                        if not pd.api.types.is_datetime64_any_dtype(d_temp['StartTime']):
                            d_temp['StartTime'] = d_temp['StartTime'].apply(parse_timestamp)

                        start_t = d_temp['StartTime'].min()
                        cutoff_t = start_t + timedelta(seconds=cut_seconds)

                        # Filtro: tengo solo dati DOPO il cutoff
                        d_cut = d_temp[d_temp['StartTime'] > cutoff_t]

                        if not d_cut.empty:
                            steady_dfs.append(d_cut)

                    if steady_dfs:
                        df_global_steady = pd.concat(steady_dfs, ignore_index=True)
                        steady_metrics = calculate_metrics(df_global_steady, seed=None)
                        global_aggregated_data_cut.append({**config_info, **steady_metrics})
                    else:
                        print(f"  -> Warning: Tutti i dati sono stati tagliati per {folder_name} (Test troppo breve?)")

                except Exception as e:
                    print(f"  -> Errore globale folder: {e}")

    # === SALVATAGGIO FILE FINALI ===

    # Funzione helper per salvare e ordinare
    def save_final_summary(data_list, filename):
        if not data_list: return
        df_final = pd.DataFrame(data_list)
        cols_prio = ['TestType', 'Mode', 'Users', 'Collections', 'Accesses', 'AverageLatency', 'Throughput']
        final_cols = [c for c in cols_prio if c in df_final.columns] + [c for c in df_final.columns if c not in cols_prio]
        df_final = df_final[final_cols]
        df_final = df_final.sort_values(by=['TestType', 'Mode', 'Users', 'Collections', 'Accesses'])

        out_path = os.path.join(root_dir, filename)
        df_final.to_csv(out_path, index=False)
        print(f"✅ Generato: {out_path}")

    print("\n--- Generazione Report Finali ---")
    if global_aggregated_data:
        save_final_summary(global_aggregated_data, "final_global_summary.csv")
    else:
        print("⚠️ Nessun dato trovato per il summary completo.")

    if global_aggregated_data_cut:
        save_final_summary(global_aggregated_data_cut, "final_global_summary_steady_state.csv")
    else:
        print("⚠️ Nessun dato trovato per il summary steady state (cut 5 rounds).")

if __name__ == "__main__":
    main()