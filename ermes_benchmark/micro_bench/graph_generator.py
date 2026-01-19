import inspect
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from scipy import stats

# Configurazione cartelle base
data_dir_name = 'data'
output_dir_name = 'output_img'

def build_aggregated_dict(df):
    """
    Converte un DataFrame (già filtrato) nella struttura dati:
    aggregated_data[users][collections] = row_dict
    """
    aggregated = {}

    for _, row in df.iterrows():
        # Gestione sicurezza tipi
        try:
            users = int(row['Users'])
            collections = int(row['Collections'])
        except ValueError:
            continue

        if users not in aggregated:
            aggregated[users] = {}

        # Converte la riga in dizionario
        row_dict = row.to_dict()

        # Assicuriamoci che i valori numerici siano float
        for key in row_dict:
            if isinstance(row_dict[key], (int, float, np.number)):
                row_dict[key] = float(row_dict[key])

        aggregated[users][collections] = row_dict

    return aggregated

def compute_confidence_intervals_from_summary(df, confidence=95):
    """
    Ricalcola l'intervallo di confidenza usando Varianza e N (CorrectRequests).
    """
    ci_data = {}
    alpha = 1 - confidence / 100.0

    if df.empty:
        return {}

    unique_collections = df['Collections'].unique()

    for collections in unique_collections:
        collections = int(collections)
        ci_data[collections] = {}

        subset = df[df['Collections'] == collections]

        for _, row in subset.iterrows():
            users = int(row['Users'])

            mean = row.get("AverageLatency", 0)
            variance = row.get("VarianceLatency", 0)
            n = int(row.get("CorrectRequests", 0))

            if n < 2:
                continue

            std = np.sqrt(variance)
            sem = std / np.sqrt(n)
            t_crit = stats.t.ppf(1 - alpha / 2, df=n - 1)

            ci_lower = mean - t_crit * sem
            ci_upper = mean + t_crit * sem

            ci_data[collections][users] = {
                "mean": mean,
                f"ci_lower_{confidence}": ci_lower,
                f"ci_upper_{confidence}": ci_upper,
                "n_samples": n
            }

    return ci_data


def print_confidence_intervals(ci_data, mode_name, confidence=95, unit="ms", max_rel_error_ok=0.25, max_rel_error_weak=0.50):
    print("\n" + "=" * 80)
    print(f" [{mode_name.upper()}] Intervalli di confidenza {confidence}% su AverageLatency")
    print("=" * 80)

    if not ci_data:
        print("Nessun dato sufficiente per il calcolo CI.")
        return

    print("Legenda: ✅ OK   ⚠️ WEAK   ❌ INVALID\n")

    for collections in sorted(ci_data.keys()):
        print(f"▶ Collections: {collections}")

        for users in sorted(ci_data[collections].keys()):
            r = ci_data[collections][users]

            mean = r["mean"]
            lower = r[f"ci_lower_{confidence}"]
            upper = r[f"ci_upper_{confidence}"]
            n = r["n_samples"]

            rel_error = (upper - lower) / (2 * mean) if mean != 0 else 0

            if lower < 0 or rel_error > max_rel_error_weak:
                status = "❌ INVALID"
            elif rel_error > max_rel_error_ok:
                status = "⚠️ WEAK"
            else:
                status = "✅ OK"

            half_width = (upper - lower) / 2

            print(
                f"  Users: {users:>5} | "
                f"mean = {mean:8.3f} {unit} | "
                f"CI{confidence}% = "
                f"[{lower:8.3f}, {upper:8.3f}] {unit} | "
                f"±{half_width:7.3f} | "
                f"rel.err = {rel_error*100:6.1f}% | "
                f"n = {n:>2} | "
                f"{status}"
            )
        print()


def plot_interaction_with_iqr_avg(aggregated_data, save_path=None):
    users_list = sorted(aggregated_data.keys())
    if not users_list: return

    collections_list = set()
    for u in aggregated_data:
        collections_list.update(aggregated_data[u].keys())
    collections_list = sorted(collections_list)

    fig, ax = plt.subplots(figsize=(10, 6))

    for collections in collections_list:
        xs, avg_vals, q1_vals, q3_vals = [], [], [], []

        for users in users_list:
            if collections in aggregated_data[users]:
                df = aggregated_data[users][collections]
                avg_vals.append(float(df["AverageLatency"]))
                q1_vals.append(float(df["Q1"]))
                q3_vals.append(float(df["Q3"]))
                xs.append(users)

        if xs:
            xs_arr = np.array(xs)
            avg_arr = np.array(avg_vals)
            q1_arr = np.array(q1_vals)
            q3_arr = np.array(q3_vals)

            ax.fill_between(xs_arr, q1_arr, q3_arr, alpha=0.18)
            line, = ax.plot(xs_arr, avg_arr, marker="o", linewidth=2, label=f"{collections} collections")
            color = line.get_color()
            line_length = (max(xs_arr) - min(xs_arr)) * 0.02 if len(xs_arr) > 1 else 1

            ax.hlines(q1_arr, xs_arr - line_length, xs_arr + line_length, linewidth=2, color=color)
            ax.hlines(q3_arr, xs_arr - line_length, xs_arr + line_length, linewidth=2, color=color)

    ax.set_xlabel("Users")
    ax.set_ylabel("Latency (ms)")
    ax.set_ylim(bottom=0)
    ax.set_title("Interaction Plot with IQR (avg)")
    ax.legend(title="Collections")
    ax.grid(True, alpha=0.4)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)
    plt.close(fig)


def plot_interaction_with_iqr_q2(aggregated_data, save_path=None):
    users_list = sorted(aggregated_data.keys())
    if not users_list: return

    collections_list = set()
    for u in aggregated_data:
        collections_list.update(aggregated_data[u].keys())
    collections_list = sorted(collections_list)

    fig, ax = plt.subplots(figsize=(10, 6))

    for collections in collections_list:
        xs, median_vals, q1_vals, q3_vals = [], [], [], []

        for users in users_list:
            if collections in aggregated_data[users]:
                df = aggregated_data[users][collections]
                median_vals.append(float(df["MedianLatency"]))
                q1_vals.append(float(df["Q1"]))
                q3_vals.append(float(df["Q3"]))
                xs.append(users)

        if xs:
            xs_arr = np.array(xs)
            median_arr = np.array(median_vals)
            q1_arr = np.array(q1_vals)
            q3_arr = np.array(q3_vals)

            ax.fill_between(xs_arr, q1_arr, q3_arr, alpha=0.18)
            line, = ax.plot(xs_arr, median_arr, marker="o", linewidth=2, label=f"{collections} collections")
            color = line.get_color()

            line_length = (max(xs_arr) - min(xs_arr)) * 0.02 if len(xs_arr) > 1 else 1

            ax.hlines(q1_arr, xs_arr - line_length, xs_arr + line_length, linewidth=2, color=color)
            ax.hlines(q3_arr, xs_arr - line_length, xs_arr + line_length, linewidth=2, color=color)

    ax.set_xlabel("Users")
    ax.set_ylabel("Latency (ms)")
    ax.set_ylim(bottom=0)
    ax.set_title("Interaction Plot with IQR (median)")
    ax.legend(title="Collections")
    ax.grid(True, alpha=0.4)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)
    plt.close(fig)


def plot_failed_requests_bar(aggregated_data, save_path=None):
    users_list = sorted(aggregated_data.keys())
    if not users_list: return

    collections_list = set()
    for u in aggregated_data:
        collections_list.update(aggregated_data[u].keys())
    collections_list = sorted(collections_list)

    if not collections_list: return

    x_indexes = np.arange(len(users_list))
    total_width = 0.5
    bar_width = total_width / len(collections_list) if collections_list else 0.5

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, collection in enumerate(collections_list):
        failed_vals = []
        for user in users_list:
            if collection in aggregated_data[user]:
                val = float(aggregated_data[user][collection]["FailedRequests"])
            else:
                val = 0
            failed_vals.append(val)

        offset = (i - (len(collections_list) - 1) / 2) * bar_width
        ax.bar(x_indexes + offset, failed_vals, width=bar_width, label=f"{collection} collections")

    ax.set_xlabel("Users (Workload)")
    ax.set_ylabel("Average Failed Requests")
    ax.set_title("Average Failed Requests vs Workload")

    ax.set_xticks(x_indexes)
    ax.set_xticklabels(users_list)

    ax.legend(title="Collections")
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)
    plt.close(fig)

# Disable pycache generation
sys.dont_write_bytecode = True

def main():
    parser = argparse.ArgumentParser(description="Process Summary CSV and generate plots by Mode.")
    parser.add_argument(
        "csv_filename",
        type=str,
        help="Nome del file CSV (incluso estensione) presente nella cartella 'data'. Es: example.csv"
    )
    args = parser.parse_args()

    # Configurazione path
    csv_filename = args.csv_filename

    current_file_path = inspect.getfile(inspect.currentframe())
    base_dir = Path(current_file_path).parent

    # Path Input: base/data/filename.csv
    input_file_path = (base_dir / data_dir_name / csv_filename).resolve()

    print(f"Reading file: {input_file_path}")

    if not input_file_path.exists():
        print(f"ERROR: File {input_file_path} does not exist.")
        exit(1)

    # Path Output: base/output_img/{nome_senza_estensione}
    output_folder_name = input_file_path.stem
    output_base_dir = (base_dir / output_dir_name / output_folder_name).resolve()

    # Pulizia/Creazione cartella output principale
    output_base_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_base_dir}")

    # Caricamento DataFrame completo
    df_global = pd.read_csv(input_file_path)

    # Identifica le modalità uniche presenti (es. eventual, sequential)
    if 'Mode' in df_global.columns:
        modes = df_global['Mode'].unique()
    else:
        print("WARNING: Colonna 'Mode' non trovata. Tratterò tutto come 'default'.")
        modes = ['default']
        df_global['Mode'] = 'default'

    for mode in modes:
        mode_str = str(mode)
        print(f"\nProcessing mode: {mode_str}...")

        # Filtra il DataFrame per la modalità corrente
        df_mode = df_global[df_global['Mode'] == mode].copy()

        if df_mode.empty:
            print(f"Skipping empty mode: {mode_str}")
            continue

        # Crea sottocartella per la modalità (es. output_img/example/eventual)
        mode_output_dir = output_base_dir / mode_str
        mode_output_dir.mkdir(parents=True, exist_ok=True)

        # Costruisce la struttura dati per i grafici
        aggregated_data = build_aggregated_dict(df_mode)

        # Calcola e stampa CI
        ci_95 = compute_confidence_intervals_from_summary(df_mode)
        print_confidence_intervals(ci_95, mode_name=mode_str)

        # Genera i grafici nella sottocartella specifica
        plot_interaction_with_iqr_avg(aggregated_data, save_path=mode_output_dir / "latency_avg.png")
        plot_interaction_with_iqr_q2(aggregated_data, save_path=mode_output_dir / "latency_median.png")
        plot_failed_requests_bar(aggregated_data, save_path=mode_output_dir / "failed_requests.png")

    print(f"\n✅ Elaborazione completata. Grafici salvati in: {output_base_dir}")

if __name__ == "__main__":
    main()