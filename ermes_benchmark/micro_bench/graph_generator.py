import inspect
import argparse
from pathlib import Path
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from scipy import stats

data_dir = 'data'
output_dir_name = 'output_img'

def load_summary_data(file_path):
    """
    Legge il file final_global_summary.csv e popola la struttura dati
    aggregated_data[users][collections] = row_dict
    """
    df = pd.read_csv(file_path)

    aggregated = {}

    # Itera sulle righe del dataframe
    for _, row in df.iterrows():
        users = int(row['Users'])
        collections = int(row['Collections'])

        if users not in aggregated:
            aggregated[users] = {}

        # Converte la riga in dizionario
        row_dict = row.to_dict()

        # Assicuriamoci che i valori numerici siano float
        # (pandas lo fa già, ma per sicurezza su colonne specifiche)
        for key in row_dict:
            if isinstance(row_dict[key], (int, float, np.number)):
                row_dict[key] = float(row_dict[key])

        aggregated[users][collections] = row_dict

    return aggregated, df

def compute_confidence_intervals_from_summary(df, confidence=95):
    """
    Ricalcola l'intervallo di confidenza usando Varianza e N (CorrectRequests)
    presenti nel file summary.
    """
    ci_data = {}
    alpha = 1 - confidence / 100.0

    # Raggruppa per Collection per mantenere la struttura del vecchio script
    # ci_data[collections][users]

    unique_collections = df['Collections'].unique()

    for collections in unique_collections:
        collections = int(collections)
        ci_data[collections] = {}

        # Filtra il df per questa collection
        subset = df[df['Collections'] == collections]

        for _, row in subset.iterrows():
            users = int(row['Users'])

            mean = row.get("AverageLatency", 0)
            variance = row.get("VarianceLatency", 0)
            # Usiamo CorrectRequests come N campionario
            n = int(row.get("CorrectRequests", 0))

            if n < 2:
                continue

            # Calcolo standard error dalla varianza salvata
            std = np.sqrt(variance)
            sem = std / np.sqrt(n)

            # t di Student
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


def print_confidence_intervals(
        ci_data,
        confidence=95,
        unit="ms",
        max_rel_error_ok=0.25,
        max_rel_error_weak=0.50
):
    """
    Stampa gli intervalli di confidenza (invariata rispetto a prima).
    """

    print("\n" + "=" * 80)
    print(f" Intervalli di confidenza al {confidence}% su AverageLatency (Ricalcolati da Summary)")
    print("=" * 80)
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

            # Classificazione
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
            # Imposta larghezza linee IQR
            line_length = (max(xs_arr) - min(xs_arr)) * 0.02 if len(xs_arr) > 1 else 1

            ax.hlines(q1_arr, xs_arr - line_length, xs_arr + line_length, linewidth=2, color=color)
            ax.hlines(q3_arr, xs_arr - line_length, xs_arr + line_length, linewidth=2, color=color)

    ax.set_xlabel("Users")
    ax.set_ylabel("Latency (ms)")
    ax.set_ylim(bottom=0) # Solo limite inferiore a 0, superiore automatico
    ax.set_title("Interaction Plot with IQR (avg)")
    ax.legend(title="Collections")
    ax.grid(True, alpha=0.4)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)

    plt.close(fig)
    return fig, ax


def plot_interaction_with_iqr_q2(aggregated_data, save_path=None):
    users_list = sorted(aggregated_data.keys())

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
    return fig, ax


def plot_failed_requests_bar(aggregated_data, save_path=None):
    users_list = sorted(aggregated_data.keys())

    collections_list = set()
    for u in aggregated_data:
        collections_list.update(aggregated_data[u].keys())
    collections_list = sorted(collections_list)

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
    return fig, ax

# Disable pycache generation
sys.dont_write_bytecode = True

def main():
    parser = argparse.ArgumentParser(description="Process Summary CSV and generate plots.")
    parser.add_argument(
        "--data_folder",
        type=str,
        default="ermes_default",
        help="Nome della cartella dei dati all'interno di 'data'"
    )
    args = parser.parse_args()

    data_folder = args.data_folder

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)

    current_file_path = inspect.getfile(inspect.currentframe())
    base_dir = Path(current_file_path).parent

    data_dir_path = (base_dir / data_dir / data_folder).resolve()
    summary_file = data_dir_path / "final_global_summary.csv"

    print(f"Data directory path: {data_dir_path}")
    print(f"Looking for summary file: {summary_file}")

    if not summary_file.exists():
        print(f"ERROR: File {summary_file} does not exist.")
        exit(1)

    output_dir = (base_dir / output_dir_name / data_folder).resolve()

    # Clean and recreate output directory
    if output_dir.exists() and output_dir.is_dir():
        for item in output_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Carica i dati
    aggregated_data, df_summary = load_summary_data(summary_file)

    # 2. Calcola e stampa intervalli di confidenza (ricostruiti)
    ci_95 = compute_confidence_intervals_from_summary(df_summary)
    print_confidence_intervals(ci_95)

    # 3. Genera i grafici
    plot_interaction_with_iqr_avg(aggregated_data, save_path=output_dir / "latency_avg.png")
    plot_interaction_with_iqr_q2(aggregated_data, save_path=output_dir / "latency_median.png")
    plot_failed_requests_bar(aggregated_data, save_path=output_dir / "failed_requests.png")

    print(f"Grafici salvati in: {output_dir}")

if __name__ == "__main__":
    main()