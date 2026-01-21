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
    """Estrae parametri dal nome della cartella principale."""
    mode_match = re.search(r'mode_([^_]+)', folder_name)
    users_match = re.search(r'users_(\d+)', folder_name)
    coll_match = re.search(r'collections_(\d+)', folder_name)

    return {
        'Mode': mode_match.group(1) if mode_match else 'unknown',
        'Users': int(users_match.group(1)) if users_match else 0,
        'Collections': int(coll_match.group(1)) if coll_match else 0
    }

def calculate_metrics(df, seed=None):
    """Calcola le metriche su un DataFrame."""
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

    metrics = {
        'AverageLatency': avg_latency,
        'MedianLatency': median_latency,
        'VarianceLatency': variance_latency,
        'Q1': Q1,
        'Q2': Q2,
        'Q3': Q3,
        'Q4': Q4,
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
        df_temp['_dt'] = df_temp[ts_col].apply(parse_timestamp)
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
        'AverageLatency', 'MedianLatency', 'VarianceLatency',
        'Q1', 'Q2', 'Q3', 'Q4',
        'TotalRequests', 'CorrectRequests', 'FailedRequests'
    ]

    final_cols = [c for c in desired_order if c in res_df.columns]
    remaining = [c for c in res_df.columns if c not in final_cols]

    return res_df[final_cols + remaining]

def main():
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    global_aggregated_data = []

    print(f"Scansione struttura cartelle in: {root_dir}")

    for root, dirs, files in os.walk(root_dir):
        folder_name = os.path.basename(root)

        # Filtra le cartelle di configurazione
        if "mode_" in folder_name and "users_" in folder_name:
            print(f"Elaborazione configurazione: {folder_name}")

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

                    csv_files = [
                        os.path.join(seed_path, f)
                        for f in os.listdir(seed_path)
                        if f.endswith('.csv') and 'aggregated' not in f
                    ]

                    if not csv_files:
                        continue

                    # Legge tutti i log del seed
                    df_seed = pd.concat((pd.read_csv(f) for f in csv_files), ignore_index=True)
                    # Converti se necessario da ms a s (assumendo ms in input se non float piccoli)
                    # NOTA: Assicurati che i tuoi CSV siano coerenti. Qui divido per 1000 come da script originale.
                    df_seed['FuncDuration'] = df_seed['FuncDuration'] / 1000.0

                    # 1. Calcola ROUNDS e conserva nel listone globale della cartella (Per file B)
                    df_rounds = calculate_metrics_by_round(df_seed, seed=seed_val, interval=ROUND_INTERVAL_SECONDS)
                    if df_rounds is not None:
                        folder_rounds_dfs.append(df_rounds)

                    # 2. Calcola SOMMARIO SEED (Per file A)
                    m = calculate_metrics(df_seed, seed=seed_val)
                    if m:
                        folder_seed_metrics_summary.append(m)

                    # 3. Conserva raw data per GLOBALE (Per file C e D)
                    dfs_for_global_calc.append(df_seed)

                except Exception as e:
                    print(f"  -> Errore elaborando {seed_dir}: {e}")

            # === SALVATAGGIO FILE ===

            # A. FILE UNICO ROUNDS (Tutti i seed insieme, ma righe separate per seed)
            if folder_rounds_dfs:
                df_all_rounds = pd.concat(folder_rounds_dfs, ignore_index=True)
                rounds_output = os.path.join(root, "aggregated_rounds_all_seeds.csv")
                df_all_rounds.to_csv(rounds_output, index=False)
                print(f"  -> Creato file rounds (dettaglio seed): {rounds_output}")

            # B. FILE SOMMARIO PER SEED (1 riga per seed)
            if folder_seed_metrics_summary:
                df_summary = pd.DataFrame(folder_seed_metrics_summary)
                cols = ['Seed'] + [c for c in df_summary.columns if c != 'Seed']
                df_summary = df_summary[cols]
                summary_output = os.path.join(root, f"aggregated_results_summary.csv")
                df_summary.to_csv(summary_output, index=False)
                print(f"  -> Creato sommario seeds: {summary_output}")

            # C. CALCOLO RIGA PER FILE GLOBALE (Sommario totale configurazione)
            if dfs_for_global_calc:
                try:
                    df_global_huge = pd.concat(dfs_for_global_calc, ignore_index=True)
                    global_metrics = calculate_metrics(df_global_huge, seed=None)
                    config_info = extract_config_from_folder(folder_name)
                    full_row = {**config_info, **global_metrics}
                    global_aggregated_data.append(full_row)
                except Exception as e:
                    print(f"  -> Errore calcolo globale per {folder_name}: {e}")

            # D. NUOVO FILE: AGGREGAZIONE GLOBALE PER ROUND (Tutti i seed normalizzati e uniti)
            # Questo crea il file richiesto dove ogni riga è un Round (1, 2, 3...) aggregando i dati di TUTTI i seed
            if dfs_for_global_calc:
                try:
                    normalized_dfs = []
                    col_ts = 'StartTime'

                    for df_raw in dfs_for_global_calc:
                        # Lavoriamo su una copia
                        d = df_raw.copy()

                        # Parsing sicuro del timestamp se non presente (potrebbe non essere stato parsato nel loop raw)
                        if '_dt' not in d.columns:
                            if col_ts in d.columns:
                                d['_dt'] = d[col_ts].apply(parse_timestamp)
                            else:
                                continue

                        # Normalizzazione temporale: Ogni seed inizia al secondo 0 relativo
                        seed_start_time = d['_dt'].min()
                        d['_rel_seconds'] = (d['_dt'] - seed_start_time).dt.total_seconds()
                        normalized_dfs.append(d)

                    if normalized_dfs:
                        # Concatena tutti i dati di tutti i seed normalizzati
                        df_global_rel = pd.concat(normalized_dfs, ignore_index=True)

                        # Assegna il Round ID basandosi sui secondi relativi (indipendentemente dall'ora reale di esecuzione)
                        df_global_rel['RoundIdx'] = (df_global_rel['_rel_seconds'] // ROUND_INTERVAL_SECONDS).astype(int)

                        global_round_rows = []

                        # Raggruppa tutti i dati per Round e calcola metriche aggregate
                        for r_idx, group in df_global_rel.groupby('RoundIdx'):
                            m = calculate_metrics(group)
                            if m:
                                m['Round'] = r_idx + 1
                                # Aggiungiamo i riferimenti temporali relativi (es. 0-15s, 15-30s)
                                m['TimeRelativeStart'] = r_idx * ROUND_INTERVAL_SECONDS
                                m['TimeRelativeEnd'] = (r_idx + 1) * ROUND_INTERVAL_SECONDS
                                global_round_rows.append(m)

                        if global_round_rows:
                            df_global_rounds = pd.DataFrame(global_round_rows)

                            # Riordina colonne per leggibilità
                            cols_order = ['Round', 'TimeRelativeStart', 'TimeRelativeEnd',
                                          'AverageLatency', 'MedianLatency', 'TotalRequests', 'CorrectRequests', 'FailedRequests']
                            existing_cols = [c for c in cols_order if c in df_global_rounds.columns]
                            other_cols = [c for c in df_global_rounds.columns if c not in existing_cols]
                            df_global_rounds = df_global_rounds[existing_cols + other_cols]

                            g_rounds_out = os.path.join(root, "aggregated_rounds_global.csv")
                            df_global_rounds.to_csv(g_rounds_out, index=False)
                            print(f"  -> Creato file rounds globale (no seed): {g_rounds_out}")

                except Exception as e:
                    print(f"  -> Errore nel calcolo del file global rounds: {e}")


    # === FILE GLOBALE FINALE ===
    if global_aggregated_data:
        df_final = pd.DataFrame(global_aggregated_data)

        first_cols = ['Mode', 'Users', 'Collections']
        other_cols = [c for c in df_final.columns if c not in first_cols]
        df_final = df_final[first_cols + other_cols]
        df_final = df_final.sort_values(by=['Mode', 'Users', 'Collections'])

        global_output = os.path.join(root_dir, "final_global_summary.csv")
        df_final.to_csv(global_output, index=False)
        print(f"\nGENERAZIONE COMPLETATA. File riassuntivo: {global_output}")
    else:
        print("\nNessun dato trovato.")

if __name__ == "__main__":
    main()