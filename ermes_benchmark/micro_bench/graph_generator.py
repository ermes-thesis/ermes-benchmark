import inspect
import argparse
from pathlib import Path
import shutil
import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt
import sys
from scipy import stats

data_dir = 'data'
output_dir_name = 'output_img'


def process_csv_files(files):
    data = {}
    for file in files:

        match = re.search(r"users_(\d+)_collections_(\d+)", file.name)
        if not match:
            print(f"WARNING: impossibile estrarre users/collections da {file.name}")
            continue

        users = int(match.group(1))
        collections = int(match.group(2))
        #print(f"Processing file with {users} users and {collections} collections")

        df = pd.read_csv(file)

        if collections not in data:
            data[collections] = {}

        data[collections][users] = df

    return data

def compute_confidence_intervals(data, confidence=95):
    """
    Calcola l'intervallo di confidenza (t di Student) sulla colonna
    AverageLatency per ogni DataFrame prodotto da process_csv_files.
    """
    ci_data = {}

    alpha = 1 - confidence / 100.0

    for collections, users_dict in data.items():
        ci_data[collections] = {}

        for users, df in users_dict.items():
            if "AverageLatency" not in df.columns:
                continue

            values = df["AverageLatency"].dropna().to_numpy()
            n = len(values)

            if n < 2:
                continue

            mean = np.mean(values)
            std = np.std(values, ddof=1)
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
    Stampa gli intervalli di confidenza segnalando visivamente
    quelli problematici, senza imporre un numero minimo di sample.
    """

    print("\n" + "=" * 80)
    print(f" Intervalli di confidenza al {confidence}% su AverageLatency")
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

            rel_error = (upper - lower) / (2 * mean)

            # Classificazione (NO vincoli su n)
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

    print(
        "Note:\n"
        " - OK     : CI plausibile e sufficientemente stretto\n"
        " - WEAK   : alta incertezza, usare con cautela\n"
        " - INVALID: CI non interpretabile o fisicamente implausibile\n"
    )

def aggregate_experiments(data):
    aggregated = {}

    for collections, users_dict in data.items():
        for users, df in users_dict.items():
            if users not in aggregated:
                aggregated[users] = {}

            # Calcolo la media su tutte le righe del CSV
            mean_values = df.mean(numeric_only=True).to_dict()

            # Salvo come dizionario semplice (non DataFrame)
            aggregated[users][collections] = {k: float(v) for k, v in mean_values.items()}

    return aggregated


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
            half_width = 0.1
            factor = 1.05
            ax.hlines(q1_arr, xs_arr / factor, xs_arr * factor, linewidth=2, color=color)
            ax.hlines(q3_arr, xs_arr / factor, xs_arr * factor, linewidth=2, color=color)

    ax.set_xlabel("Users")
    ax.set_ylabel("Latency (ms)")
    ax.set_yscale("log")
    ax.set_xscale("log")
    ax.set_title("Interaction Plot with IQR (avg)")
    ax.legend(title="Collections")
    ax.grid(True, alpha=0.4)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)
        #print(f"Saved figure to {save_path}")

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
            factor = 1.05
            ax.hlines(q1_arr, xs_arr / factor, xs_arr * factor, linewidth=2, color=color)
            ax.hlines(q3_arr, xs_arr / factor, xs_arr * factor, linewidth=2, color=color)

    ax.set_xlabel("Users")
    ax.set_ylabel("Latency (ms)")
    ax.set_yscale("log")
    ax.set_xscale("log")
    ax.set_title("Interaction Plot with IQR (median)")
    ax.legend(title="Collections")
    ax.grid(True, alpha=0.4)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)
        #print(f"Saved figure to {save_path}")

    plt.close(fig)
    return fig, ax


def plot_failed_requests_bar(aggregated_data, save_path=None):
    users_list = sorted(aggregated_data.keys())
    collections_list = set()
    for u in aggregated_data:
        collections_list.update(aggregated_data[u].keys())
    collections_list = sorted(collections_list)

    width = 0.8 / len(collections_list)

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, collections in enumerate(collections_list):
        xs, failed_vals = [], []

        for users in users_list:
            if collections in aggregated_data[users]:
                df = aggregated_data[users][collections]
                failed_vals.append(float(df["FailedRequests"]))
                xs.append(users)

        if xs:
            xs_offset = np.array(xs) - 0.4 + i * width + width / 2
            ax.bar(xs_offset, failed_vals, width=width, label=f"{collections} collections")

    ax.set_xlabel("Users (Workload)")
    ax.set_ylabel("Average Failed Requests")
    ax.set_title("Average Failed Requests vs Workload")
    ax.set_xticks(users_list)
    ax.legend(title="Collections")
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)
        #print(f"Saved figure to {save_path}")

    plt.close(fig)
    return fig, ax


# Disable pycache generation
sys.dont_write_bytecode = True

#python3 graph_generator.py --data_folder ermes_default
def main():
    parser = argparse.ArgumentParser(description="Process CSV data and generate plots.")
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

    print(f"Data directory path: {data_dir_path}")

    if not data_dir_path.exists():
        print(f"ERROR: Directory {data_dir_path} does not exist.")
        exit(1)


    files = [f for f in data_dir_path.glob("*.csv") if f.name.startswith("aggregated_")]
        
    # Sort files to ensure consistent processing order (optional but recommended)
    files.sort()

    if not files:
        print(f"ERROR: No .csv files found in {data_dir_path}")
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

    data = process_csv_files(files)
    ci_95 = compute_confidence_intervals(data)
    print_confidence_intervals(ci_95)
    aggregated_data = aggregate_experiments(data)

    #from pprint import pprint
    #pprint(aggregated_data)

    plot_interaction_with_iqr_avg(aggregated_data, save_path=output_dir / "latency_avg.png")
    plot_interaction_with_iqr_q2(aggregated_data, save_path=output_dir / "latency_median.png")
    plot_failed_requests_bar(aggregated_data, save_path=output_dir / "failed_requests.png")


if __name__ == "__main__":
    main()
