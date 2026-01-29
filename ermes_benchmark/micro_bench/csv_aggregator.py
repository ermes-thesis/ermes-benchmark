import os
import sys
import pandas as pd
import re
import pytz
from datetime import datetime, timedelta

# --- CONFIGURAZIONE ---
HTTP_ERROR_CODES = [404, 423, 500, 503, 508]
ROUND_INTERVAL_SECONDS = 15
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
    """Estrae parametri dal nome della cartella principale."""
    mode_match = re.search(r'mode_([^_]+)', folder_name)
    users_match = re.search(r'users_(\d+)', folder_name)
    coll_match = re.search(r'collections_(\d+)', folder_name)
    acc_match = re.search(r'accesses_(\d+)', folder_name)

    config = {'Mode': mode_match.group(1) if mode_match else 'unknown'}
    if users_match:
        config['Users'] = int(users_match.group(1))
    else:
        config['Users'] = 64
    if coll_match:
        config['Collections'] = int(coll_match.group(1))
    else:
        config['Collections'] = 100
    if acc_match:
        config['Accesses'] = int(acc_match.group(1))
        config['TestType'] = 'Density'
    else:
        config['Accesses'] = 1
        config['TestType'] = 'Scalability'
    return config

def calculate_metrics(df, seed=None):
    """Calcola le metriche su un DataFrame."""
    if df is None or df.empty:
        return None
    if 'StatusCode' not in df.columns:
        df['StatusCode'] = 200

    avg_latency = df['FuncDuration'].mean()
    median_latency = df['FuncDuration'].median()
    variance_latency = df['FuncDuration'].var()
    qs = df['FuncDuration'].quantile([0.25, 0.5, 0.75, 1.0])

    total_requests = len(df)
    correct_requests = len(df[df['StatusCode'] == 200])
    failed_requests = total_requests - correct_requests
    error_code_counts = {code: len(df[df['StatusCode'] == code]) for code in HTTP_ERROR_CODES}
    other_errors = len(df[(df['StatusCode'] != 200) & (~df['StatusCode'].isin(HTTP_ERROR_CODES))])

    try:
        if pd.api.types.is_string_dtype(df['StartTime']):
            times = df['StartTime'].apply(parse_timestamp)
        else:
            times = df['StartTime']
        duration = (times.max() - times.min()).total_seconds()
        throughput = total_requests / duration if duration > 0 else 0
    except:
        throughput = 0

    metrics = {
        'AverageLatency': avg_latency, 'MedianLatency': median_latency, 'VarianceLatency': variance_latency,
        'Throughput': throughput, 'Q1': qs[0.25], 'Q2': qs[0.5], 'Q3': qs[0.75], 'Q4': qs[1.0],
        'TotalRequests': total_requests, 'CorrectRequests': correct_requests, 'FailedRequests': failed_requests,
        **error_code_counts, 'OtherErrors': other_errors
    }
    return {'Seed': seed, **metrics} if seed is not None else metrics

def calculate_metrics_by_round(df, seed, interval=ROUND_INTERVAL_SECONDS):
    ts_col = "StartTime"
    df_temp = df.copy()
    try:
        if not pd.api.types.is_datetime64_any_dtype(df_temp[ts_col]):
            df_temp['_dt'] = df_temp[ts_col].apply(parse_timestamp)
        else:
            df_temp['_dt'] = df_temp[ts_col]
    except:
        return None

    df_temp = df_temp.sort_values('_dt')
    start_time_global = df_temp['_dt'].min()
    df_temp['RoundIdx'] = ((df_temp['_dt'] - start_time_global).dt.total_seconds() // interval).astype(int)

    rows = []
    for round_idx, group in df_temp.groupby('RoundIdx'):
        m = calculate_metrics(group)
        if m:
            m.update({'Seed': seed, 'Round': round_idx + 1})
            rows.append(m)
    return pd.DataFrame(rows) if rows else None

def main():
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    global_aggregated_data = []
    global_aggregated_data_cut = []
    global_rounds_accumulator = [] # <--- NUOVO: Accumulatore per tutti i round globali

    print(f"Scansione in: {root_dir}")

    for root, dirs, files in os.walk(root_dir):
        folder_name = os.path.basename(root)
        if "mode_" in folder_name and ("users_" in folder_name or "accesses_" in folder_name):
            print(f"Elaborazione: {folder_name}")
            config_info = extract_config_from_folder(folder_name)
            seed_dirs = [d for d in dirs if d.startswith("seed_")]
            if not seed_dirs: continue

            folder_seed_metrics_summary = []
            folder_rounds_dfs = []
            dfs_for_global_calc = []

            for seed_dir in seed_dirs:
                try:
                    seed_val = int(seed_dir.split('_')[1])
                    seed_path = os.path.join(root, seed_dir)
                    csv_files = [os.path.join(seed_path, f) for f in os.listdir(seed_path) if f.endswith('.csv') and 'aggregated' not in f]
                    if not csv_files: continue

                    df_seed = pd.concat((pd.read_csv(f) for f in csv_files), ignore_index=True)
                    df_seed['FuncDuration'] = df_seed['FuncDuration'] / 1000.0

                    df_rounds = calculate_metrics_by_round(df_seed, seed=seed_val)
                    if df_rounds is not None: folder_rounds_dfs.append(df_rounds)

                    m = calculate_metrics(df_seed, seed=seed_val)
                    if m: folder_seed_metrics_summary.append(m)
                    dfs_for_global_calc.append(df_seed)
                except Exception as e:
                    print(f"  -> Errore seed {seed_dir}: {e}")

            # Salvataggi locali e accumulo globale per round
            if dfs_for_global_calc:
                try:
                    normalized_dfs = []
                    for df_raw in dfs_for_global_calc:
                        d = df_raw.copy()
                        if not pd.api.types.is_datetime64_any_dtype(d['StartTime']):
                            d['StartTime'] = d['StartTime'].apply(parse_timestamp)
                        d['_rel_seconds'] = (d['StartTime'] - d['StartTime'].min()).dt.total_seconds()
                        normalized_dfs.append(d)

                    df_global_rel = pd.concat(normalized_dfs, ignore_index=True)
                    df_global_rel['RoundIdx'] = (df_global_rel['_rel_seconds'] // ROUND_INTERVAL_SECONDS).astype(int)

                    global_round_rows = []
                    for r_idx, group in df_global_rel.groupby('RoundIdx'):
                        m = calculate_metrics(group)
                        if m:
                            m.update({'Round': r_idx + 1, 'TimeRelativeStart': r_idx * ROUND_INTERVAL_SECONDS})
                            global_round_rows.append(m)

                    if global_round_rows:
                        df_folder_global_rounds = pd.DataFrame(global_round_rows)
                        # Salva file locale alla cartella
                        df_folder_global_rounds.to_csv(os.path.join(root, "aggregated_rounds_global.csv"), index=False)

                        # Aggiungi all'accumulatore globale con info configurazione
                        for row in global_round_rows:
                            global_rounds_accumulator.append({**config_info, **row})

                    # Summary standard e Steady State
                    df_huge = pd.concat(normalized_dfs, ignore_index=True)
                    global_aggregated_data.append({**config_info, **calculate_metrics(df_huge)})

                    cutoff = WARMUP_ROUNDS * ROUND_INTERVAL_SECONDS
                    steady_dfs = [d[d['_rel_seconds'] > cutoff] for d in normalized_dfs if not d[d['_rel_seconds'] > cutoff].empty]
                    if steady_dfs:
                        global_aggregated_data_cut.append({**config_info, **calculate_metrics(pd.concat(steady_dfs))})

                except Exception as e:
                    print(f"  -> Errore folder: {e}")

            if folder_rounds_dfs:
                pd.concat(folder_rounds_dfs, ignore_index=True).to_csv(os.path.join(root, "aggregated_rounds_all_seeds.csv"), index=False)
            if folder_seed_metrics_summary:
                pd.DataFrame(folder_seed_metrics_summary).to_csv(os.path.join(root, "aggregated_results_summary.csv"), index=False)

    # --- GENERAZIONE REPORT FINALI ---
    def save_final(data, filename, priority_cols):
        if not data: return
        df = pd.DataFrame(data)
        cols = [c for c in priority_cols if c in df.columns] + [c for c in df.columns if c not in priority_cols]
        df = df[cols].sort_values(by=['TestType', 'Mode', 'Users', 'Collections', 'Accesses'] + (['Round'] if 'Round' in df.columns else []))
        path = os.path.join(root_dir, filename)
        df.to_csv(path, index=False)
        print(f"✅ Generato: {path}")

    print("\n--- Report Finali ---")
    config_cols = ['TestType', 'Mode', 'Users', 'Collections', 'Accesses']
    save_final(global_aggregated_data, "final_global_summary.csv", config_cols + ['AverageLatency'])
    save_final(global_aggregated_data_cut, "final_global_summary_steady_state.csv", config_cols + ['AverageLatency'])
    # Salvataggio del nuovo file globale per round
    save_final(global_rounds_accumulator, "final_global_rounds.csv", config_cols + ['Round', 'AverageLatency'])

if __name__ == "__main__":
    main()