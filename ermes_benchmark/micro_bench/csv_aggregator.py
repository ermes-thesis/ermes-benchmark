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

    # Calcolo Throughput (Richieste / Secondo) basato sulla durata effettiva del test nel chunk
    try:
        min_time = df['StartTime'].apply(parse_timestamp).min()
        max_time = df['StartTime'].apply(parse_timestamp).max()
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

        # Criterio di identificazione cartella di configurazione:
        # Deve avere "mode_" E ("users_" O "accesses_")
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

                    # 1. Rounds
                    df_rounds = calculate_metrics_by_round(df_seed, seed=seed_val, interval=ROUND_INTERVAL_SECONDS)
                    if df_rounds is not None: folder_rounds_dfs.append(df_rounds)

                    # 2. Summary Seed
                    m = calculate_metrics(df_seed, seed=seed_val)
                    if m: folder_seed_metrics_summary.append(m)

                    # 3. Global
                    dfs_for_global_calc.append(df_seed)

                except Exception as e:
                    print(f"  -> Errore seed {seed_dir}: {e}")

            # Salvataggi intermedi (Rounds e Summary per cartella)
            if folder_rounds_dfs:
                pd.concat(folder_rounds_dfs, ignore_index=True).to_csv(os.path.join(root, "aggregated_rounds_all_seeds.csv"), index=False)

            if folder_seed_metrics_summary:
                pd.DataFrame(folder_seed_metrics_summary).to_csv(os.path.join(root, "aggregated_results_summary.csv"), index=False)

            # Aggiunta al Global Summary
            if dfs_for_global_calc:
                try:
                    df_global_huge = pd.concat(dfs_for_global_calc, ignore_index=True)
                    global_metrics = calculate_metrics(df_global_huge, seed=None)
                    config_info = extract_config_from_folder(folder_name)
                    # Uniamo info config e metriche
                    global_aggregated_data.append({**config_info, **global_metrics})
                except Exception as e:
                    print(f"  -> Errore globale folder: {e}")

    # === FILE GLOBALE FINALE ===
    if global_aggregated_data:
        df_final = pd.DataFrame(global_aggregated_data)

        # Ordinamento colonne intelligente
        cols_prio = ['TestType', 'Mode', 'Users', 'Collections', 'Accesses', 'AverageLatency', 'Throughput']
        final_cols = [c for c in cols_prio if c in df_final.columns] + [c for c in df_final.columns if c not in cols_prio]
        df_final = df_final[final_cols]

        # Ordina le righe
        df_final = df_final.sort_values(by=['TestType', 'Mode', 'Users', 'Collections', 'Accesses'])

        global_output = os.path.join(root_dir, "final_global_summary.csv")
        df_final.to_csv(global_output, index=False)
        print(f"\n✅ GENERAZIONE COMPLETATA. Report: {global_output}")
    else:
        print("\n⚠️ Nessun dato trovato. Controlla che le cartelle contengano 'mode_' e 'users_'/'accesses_'.")

if __name__ == "__main__":
    main()