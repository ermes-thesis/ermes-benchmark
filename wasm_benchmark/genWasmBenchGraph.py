import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import seaborn as sns
import sys
import os

# ---------------------------------------------------------------------
# 1. Global Setup
# ---------------------------------------------------------------------
sns.set_theme(style="whitegrid", font_scale=1.2)
PALETTE = "viridis"

ALGO_ORDER = [
    "Fibonacci (40)",
    "Prime Numbers",
    "Simple Loop",
    "Tail Fibonacci (20k)",
    "Stateful"
]

def create_simple_label(row):
    """Creates a simpler X-axis label (e.g., 'Wasmedge\nAOT')"""
    if row["Runtime"].lower() == "native":
        return row["Runtime"]
    else:
        return f"{row['Runtime']}\n{row['Compilation']}"

# ---------------------------------------------------------------------
# 2. Parsing Logic
# ---------------------------------------------------------------------
def parse_benchmark_file(file_path):
    """
    Parses the new results.json format containing sub-benchmarks.
    Returns a DataFrame containing all data found.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    regex = r"^(?:BenchmarkExecutionTime_|Benchmark_)([A-Za-z0-9_]+)(?:/([A-Za-z0-9_]+))?-\d+\s+(\d+)\s+(\d+(?:\.\d+)?)\s+ns/op"

    records = []
    for line in lines:
        match = re.search(regex, line)
        if not match:
            continue

        full_tag = match.group(1)
        cache_type = match.group(2)
        ns_op = float(match.group(4))

        parts = full_tag.split("_")

        runtime = "Unknown"
        compilation = "Unknown"
        optimization = "Unknown"
        algorithm = "Unknown"

        if parts[0] == "Native":
            runtime = "Native"
            if len(parts) > 1: algorithm = parts[1]
            cache_type = "Native"
            compilation = "Native"
            optimization = "Native"
        elif len(parts) >= 4:
            runtime = parts[0]
            compilation = parts[1]
            optimization = parts[2]
            algorithm = parts[3]
            if not cache_type: cache_type = "Cold"
        else:
            continue

        if "TailFibonacci" in algorithm: algorithm = "Tail Fibonacci (20k)"
        elif "Fibonacci" in algorithm: algorithm = "Fibonacci (40)"
        elif "PrimeNumbers" in algorithm: algorithm = "Prime Numbers"
        elif "Lightweight" in algorithm: algorithm = "Simple Loop"
        elif "Stateful" in algorithm: algorithm = "Stateful"

        records.append({
            "Runtime": runtime,
            "Compilation": compilation,
            "Optimization": optimization,
            "Algorithm": algorithm,
            "Cache": cache_type,
            "ns/op": ns_op,
            "X_label": create_simple_label({"Runtime": runtime, "Compilation": compilation})
        })

    df = pd.DataFrame(records)
    if not df.empty and (df["ns/op"] <= 0).any():
        df.loc[df["ns/op"] <= 0, "ns/op"] = 0.1

    return df

# ---------------------------------------------------------------------
# 3. Plotting Functions
# ---------------------------------------------------------------------

def export_legend(handles, labels, filename, ncol=None):
    """Exports a legend (only algorithms) to a separate file."""
    if not handles:
        return

    if ncol is None:
        ncol = len(labels)

    fig_leg = plt.figure(figsize=(len(labels) * 2.5, 1))
    ax_leg = fig_leg.add_subplot(111)
    ax_leg.axis('off')

    ax_leg.legend(handles, labels, title="Algorithm", loc='center', ncol=ncol, frameon=True, borderaxespad=0.1)

    fig_leg.savefig(filename, bbox_inches='tight')
    plt.close(fig_leg)
    print(f"- Generated Legend: {filename}")

def export_legend_with_line(handles, labels, filename, ncol=None):
    """Exports a legend that includes the 'No Gain' red dashed line."""
    if not handles:
        return

    # Add the red dashed line entry manually
    line_handle = mlines.Line2D([], [], color='red', linestyle='--', label='No Speedup (1.0x)')

    # Append to lists
    handles.append(line_handle)
    labels.append('No Speedup (1.0x)')

    if ncol is None:
        ncol = len(labels)

    fig_leg = plt.figure(figsize=(len(labels) * 2.5, 1))
    ax_leg = fig_leg.add_subplot(111)
    ax_leg.axis('off')

    ax_leg.legend(handles, labels, title="Algorithm", loc='center', ncol=ncol, frameon=True, borderaxespad=0.1)

    fig_leg.savefig(filename, bbox_inches='tight')
    plt.close(fig_leg)
    print(f"- Generated Legend with Line: {filename}")

legend_algo_saved = False
legend_speedup_saved = False

def plot_standard_analysis(df, suffix, file_ext, show_ylabel=True):
    """
    Generates the standard 3 charts.
    - show_ylabel: If False, hides the Y-axis label text but keeps ticks/numbers.
    """
    global legend_algo_saved, legend_speedup_saved
    if df.empty:
        print(f"Skipping analysis for {suffix}: No data.")
        return

    # --- Define X-axis Orders ---
    runtimes_speedup = sorted(df[df["Runtime"] != "Native"]["X_label"].unique())
    runtimes_time = sorted(df["X_label"].unique())
    if "Native" in runtimes_time:
        runtimes_time.remove("Native")
        runtimes_time.insert(0, "Native")

    algos = [a for a in ALGO_ORDER if a in df["Algorithm"].unique()]

    # --- 1. Average Execution Time (NO Optimizations) ---
    df_no_opts = df[df["Optimization"].isin(["NoOpts", "Native"])]
    if not df_no_opts.empty:
        plt.figure(figsize=(9, 5))
        ax = sns.barplot(data=df_no_opts, x="X_label", y="ns/op", hue="Algorithm", palette=PALETTE, hue_order=algos, order=runtimes_time)

        handles, labels = ax.get_legend_handles_labels()
        if ax.get_legend() is not None: ax.get_legend().remove()

        plt.yscale("log")

        # APPLICAZIONE MODIFICA: Controllo show_ylabel
        if show_ylabel:
            plt.ylabel("ns/op (log)")
        else:
            plt.ylabel("")

        plt.xlabel("")
        plt.savefig(f"time_no_opts_{suffix}{file_ext}", bbox_inches='tight')
        plt.close()
        print(f"- Generated: time_no_opts_{suffix}{file_ext}")

        if not legend_algo_saved and handles:
            export_legend(handles, labels, f"legend_algorithms{file_ext}")
            legend_algo_saved = True

    # --- 2. Average Execution Time (WITH Optimizations) ---
    df_with_opts = df[df["Optimization"].isin(["WithOpts", "Native"])]
    if not df_with_opts.empty:
        plt.figure(figsize=(9, 5))
        ax = sns.barplot(data=df_with_opts, x="X_label", y="ns/op", hue="Algorithm", palette=PALETTE, hue_order=algos, order=runtimes_time)
        if ax.get_legend() is not None: ax.get_legend().remove()
        plt.yscale("log")

        # APPLICAZIONE MODIFICA: Controllo show_ylabel
        if show_ylabel:
            plt.ylabel("ns/op (log)")
        else:
            plt.ylabel("")

        plt.xlabel("")
        plt.savefig(f"time_with_opts_{suffix}{file_ext}", bbox_inches='tight')
        plt.close()
        print(f"- Generated: time_with_opts_{suffix}{file_ext}")

    # --- 3. Speedup (NoOpts / WithOpts) ---
    df_pivot = df.pivot_table(index=["Algorithm", "X_label"], columns="Optimization", values="ns/op").reset_index()
    if "NoOpts" in df_pivot.columns and "WithOpts" in df_pivot.columns:
        df_pivot["Speedup"] = df_pivot["NoOpts"] / df_pivot["WithOpts"]

        plt.figure(figsize=(8, 5))
        ax = sns.barplot(data=df_pivot, x="X_label", y="Speedup", hue="Algorithm", palette=PALETTE, hue_order=algos, order=runtimes_speedup)

        handles_sp, labels_sp = ax.get_legend_handles_labels()

        if ax.get_legend() is not None: ax.get_legend().remove()
        plt.axhline(1.0, color='red', linestyle='--')

        # APPLICAZIONE MODIFICA: Controllo show_ylabel
        if show_ylabel:
            plt.ylabel("Speedup Factor")
        else:
            plt.ylabel("")

        plt.xlabel("")
        plt.savefig(f"speedup_opts_{suffix}{file_ext}", bbox_inches='tight')
        plt.close()
        print(f"- Generated: speedup_opts_{suffix}{file_ext}")

        if not legend_speedup_saved and handles_sp:
            export_legend_with_line(handles_sp, labels_sp, f"legend_speedup{file_ext}")
            legend_speedup_saved = True


def plot_speedup_compare_caches(df_cold, df_target, target_name, file_ext, show_ylabel=True):
    """
    Generates the specific chart: Speedup NoCache (Cold) vs Target Cache (e.g., WarmStd or Hybrid).
    """
    global legend_speedup_saved
    print(f"\nGenerating Comparison: Cold vs {target_name}...")

    df_merged = pd.merge(
        df_cold, df_target,
        on=["Runtime", "Compilation", "Optimization", "Algorithm", "X_label"],
        suffixes=('_cold', '_target')
    )

    if df_merged.empty:
        print(f"No matching data found for Cold vs {target_name} comparison.")
        return

    df_merged["Speedup"] = df_merged["ns/op_cold"] / df_merged["ns/op_target"]

    algos = [a for a in ALGO_ORDER if a in df["Algorithm"].unique()]
    runtimes = sorted(df_merged[df_merged["Runtime"] != "Native"]["X_label"].unique())

    for opt in ["WithOpts", "NoOpts"]:
        df_subset = df_merged[df_merged["Optimization"] == opt]
        if df_subset.empty: continue

        plt.figure(figsize=(8, 5))
        ax = sns.barplot(data=df_subset, x="X_label", y="Speedup", hue="Algorithm", palette=PALETTE, hue_order=algos, order=runtimes)

        handles_sp, labels_sp = ax.get_legend_handles_labels()
        if ax.get_legend() is not None: ax.get_legend().remove()

        plt.axhline(1.0, color='red', linestyle='--')

        if show_ylabel:
            plt.ylabel(f"Speedup Factor")
        else:
            plt.ylabel("")

        plt.xlabel("")
        plt.yscale("log")
        plt.savefig(f"speedup_cold_vs_{target_name.lower()}_{opt.lower()}{file_ext}", bbox_inches='tight')
        plt.close()
        print(f"- Generated: speedup_cold_vs_{target_name.lower()}_{opt.lower()}{file_ext}")

        if not legend_speedup_saved and handles_sp:
            export_legend_with_line(handles_sp, labels_sp, f"legend_speedup{file_ext}")
            legend_speedup_saved = True

# ---------------------------------------------------------------------
# 4. Main
# ---------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]
    file_ext = ".pdf" if "--pdf" in args else ".png"
    if "--pdf" in args: args.remove("--pdf")
    target_file = args[0] if args else "results.json"

    print(f"--- Processing {target_file} ---")
    df = parse_benchmark_file(target_file)

    if df.empty:
        print("No valid data found.")
        sys.exit(1)

    print(f"Cache levels found: {df['Cache'].unique()}")

    # 1. Standard Analysis for COLD
    print("\n--- 1. Generating Standard Analysis for COLD ---")
    df_cold = df[df["Cache"].isin(["Cold", "Native"])].copy()
    plot_standard_analysis(df_cold, "cold", file_ext, show_ylabel=True)

    # 2. Standard Analysis for WARM STANDARD
    # ** MODIFICA: Y Label (testo) disabilitata per WarmStd **
    print("\n--- 2. Generating Analysis for WARM STANDARD ---")
    df_std = df[df["Cache"].isin(["WarmStd", "Native"])].copy()
    if not df_std.empty:
        plot_standard_analysis(df_std, "warmStd", file_ext, show_ylabel=False)
    else:
        print("No WarmStd cache data found.")

    # 3. Standard Analysis for HYBRID
    print("\n--- 3. Generating Analysis for HYBRID ---")
    df_hybrid = df[df["Cache"].isin(["WarmHybrid", "Native"])].copy()
    if not df_hybrid.empty:
        plot_standard_analysis(df_hybrid, "hybrid", file_ext, show_ylabel=True)
    else:
        print("No Hybrid cache data found.")

    # 4. Comparison Charts
    df_cold_pure = df[df["Cache"] == "Cold"].copy()
    if not df_cold_pure.empty:
        df_hybrid_pure = df[df["Cache"] == "WarmHybrid"].copy()
        if not df_hybrid_pure.empty:
            plot_speedup_compare_caches(df_cold_pure, df_hybrid_pure, "Hybrid", file_ext, show_ylabel=False)

        df_std_pure = df[df["Cache"] == "WarmStd"].copy()
        if not df_std_pure.empty:
            plot_speedup_compare_caches(df_cold_pure, df_std_pure, "Standard", file_ext)

    print("\nDone.")