import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

# ---------------------------------------------------------------------
# 1. Global Setup
# ---------------------------------------------------------------------
sns.set_theme(style="whitegrid", font_scale=1.2)
PALETTE = "viridis"

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

    # Regex to capture: BenchmarkName, (Optional Suffix like /Cold), Iterations, Time
    # Supports both "BenchmarkExecutionTime_" and "Benchmark_" prefixes
    regex = r"^(?:BenchmarkExecutionTime_|Benchmark_)([A-Za-z0-9_]+)(?:/([A-Za-z0-9_]+))?-\d+\s+(\d+)\s+(\d+(?:\.\d+)?)\s+ns/op"

    records = []
    for line in lines:
        match = re.search(regex, line)
        if not match:
            continue

        full_tag = match.group(1)
        cache_type = match.group(2) # Can be None, Cold, WarmStd, WarmHybrid
        ns_op = float(match.group(4))

        # Parse the tag (Runtime_Compilation_Optimization_Algorithm)
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
            if not cache_type: cache_type = "Cold" # Default to Cold if no suffix
        else:
            continue

        # Clean up names
        if "TailFibonacci" in algorithm: algorithm = "TailFib (20k)"
        elif "Fibonacci" in algorithm: algorithm = "Fib (40)"
        elif "PrimeNumbers" in algorithm: algorithm = "Prime (2M)"
        elif "Lightweight" in algorithm: algorithm = "Lightweight"
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
    # Sanitize data for log scales
    if not df.empty and (df["ns/op"] <= 0).any():
        df.loc[df["ns/op"] <= 0, "ns/op"] = 0.1

    return df

# ---------------------------------------------------------------------
# 3. Plotting Functions
# ---------------------------------------------------------------------

def plot_standard_analysis(df, suffix, file_ext, save_individual):
    """
    Generates the standard 3 charts (Time NoOpts, Time WithOpts, Speedup Int/Opt)
    for a specific data slice (e.g., 'Cold' data or 'Hybrid' data).
    """
    if df.empty:
        print(f"Skipping analysis for {suffix}: No data.")
        return

    # --- Define X-axis Orders ---
    # 1. Speedup Order: Exclude Native (it has no Opt/NoOpt variants)
    runtimes_speedup = sorted(df[df["Runtime"] != "Native"]["X_label"].unique())

    # 2. Time Order: Include Native, forcing it to be first
    runtimes_time = sorted(df["X_label"].unique())
    if "Native" in runtimes_time:
        runtimes_time.remove("Native")
        runtimes_time.insert(0, "Native")

    algos = sorted(df["Algorithm"].unique())

    # --- 1. Average Execution Time (NO Optimizations) ---
    df_no_opts = df[df["Optimization"].isin(["NoOpts", "Native"])]
    if not df_no_opts.empty:
        plt.figure(figsize=(12, 6))
        # Use runtimes_time to include Native
        sns.barplot(data=df_no_opts, x="X_label", y="ns/op", hue="Algorithm", palette=PALETTE, hue_order=algos, order=runtimes_time)
        plt.yscale("log")
        plt.title(f"Execution Time - NoOpts ({suffix})")
        plt.ylabel("ns/op (log)")
        plt.xlabel("")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        fname = f"time_no_opts_{suffix}{file_ext}"
        plt.savefig(fname, bbox_inches='tight')
        if not save_individual: plt.close()
        print(f"- Generated: {fname}")

    # --- 2. Average Execution Time (WITH Optimizations) ---
    df_with_opts = df[df["Optimization"].isin(["WithOpts", "Native"])]
    if not df_with_opts.empty:
        plt.figure(figsize=(12, 6))
        # Use runtimes_time to include Native
        sns.barplot(data=df_with_opts, x="X_label", y="ns/op", hue="Algorithm", palette=PALETTE, hue_order=algos, order=runtimes_time)
        plt.yscale("log")
        plt.title(f"Execution Time - WithOpts ({suffix})")
        plt.ylabel("ns/op (log)")
        plt.xlabel("")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        fname = f"time_with_opts_{suffix}{file_ext}"
        plt.savefig(fname, bbox_inches='tight')
        if not save_individual: plt.close()
        print(f"- Generated: {fname}")

    # --- 3. Speedup (NoOpts / WithOpts) ---
    # Pivot to calculate speedup
    df_pivot = df.pivot_table(index=["Algorithm", "X_label"], columns="Optimization", values="ns/op").reset_index()
    if "NoOpts" in df_pivot.columns and "WithOpts" in df_pivot.columns:
        df_pivot["Speedup"] = df_pivot["NoOpts"] / df_pivot["WithOpts"]

        plt.figure(figsize=(12, 6))
        # Use runtimes_speedup to exclude Native
        sns.barplot(data=df_pivot, x="X_label", y="Speedup", hue="Algorithm", palette=PALETTE, hue_order=algos, order=runtimes_speedup)
        plt.axhline(1.0, color='red', linestyle='--')
        plt.title(f"Speedup: NoOpts vs WithOpts ({suffix})")
        plt.ylabel("Speedup Factor")
        plt.xlabel("")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        fname = f"speedup_opts_{suffix}{file_ext}"
        plt.savefig(fname, bbox_inches='tight')
        if not save_individual: plt.close()
        print(f"- Generated: {fname}")


def plot_speedup_compare_caches(df_cold, df_target, target_name, file_ext, save_individual):
    """
    Generates the specific chart: Speedup NoCache (Cold) vs Target Cache (e.g., WarmStd or Hybrid).
    """
    print(f"\nGenerating Comparison: Cold vs {target_name}...")

    # Merge datasets
    df_merged = pd.merge(
        df_cold, df_target,
        on=["Runtime", "Compilation", "Optimization", "Algorithm", "X_label"],
        suffixes=('_cold', '_target')
    )

    if df_merged.empty:
        print(f"No matching data found for Cold vs {target_name} comparison.")
        return

    # Calculate Speedup (Cold / Target)
    df_merged["Speedup"] = df_merged["ns/op_cold"] / df_merged["ns/op_target"]

    algos = sorted(df_merged["Algorithm"].unique())
    # Exclude Native from comparison plots
    runtimes = sorted(df_merged[df_merged["Runtime"] != "Native"]["X_label"].unique())

    # Generate plot for WithOpts (most relevant) and NoOpts
    for opt in ["WithOpts", "NoOpts"]:
        df_subset = df_merged[df_merged["Optimization"] == opt]
        if df_subset.empty: continue

        plt.figure(figsize=(12, 6))
        sns.barplot(data=df_subset, x="X_label", y="Speedup", hue="Algorithm", palette=PALETTE, hue_order=algos, order=runtimes)
        plt.axhline(1.0, color='red', linestyle='--', label="No Gain (1.0x)")
        plt.title(f"Impact of {target_name} Cache ({opt})\n(Speedup vs Cold Start)")
        plt.ylabel(f"Speedup (Cold / {target_name})")
        plt.xlabel("")
        plt.yscale("log")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        fname = f"speedup_cold_vs_{target_name.lower()}_{opt.lower()}{file_ext}"
        plt.savefig(fname, bbox_inches='tight')
        if not save_individual: plt.close()
        print(f"- Generated: {fname}")

# ---------------------------------------------------------------------
# 4. Main
# ---------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]

    # Configuration Flags
    file_ext = ".pdf" if "--pdf" in args else ".png"
    save_individual = "--individual" in args

    # Clean args
    if "--pdf" in args: args.remove("--pdf")
    if "--individual" in args: args.remove("--individual")

    # File Input
    target_file = args[0] if args else "results.json"

    print(f"--- Processing {target_file} ---")
    df = parse_benchmark_file(target_file)

    if df.empty:
        print("No valid data found.")
        sys.exit(1)

    print(f"Cache levels found: {df['Cache'].unique()}")

    # 1. Standard Analysis for COLD
    # Includes Native
    print("\n--- 1. Generating Standard Analysis for COLD ---")
    df_cold = df[df["Cache"].isin(["Cold", "Native"])].copy()
    plot_standard_analysis(df_cold, "Cold", file_ext, save_individual)

    # 2. Standard Analysis for WARM STANDARD
    # Modified: Now includes Native for baseline comparison
    print("\n--- 2. Generating Analysis for WARM STANDARD ---")
    df_std = df[df["Cache"].isin(["WarmStd", "Native"])].copy()
    if not df_std.empty:
        plot_standard_analysis(df_std, "WarmStd", file_ext, save_individual)
    else:
        print("No WarmStd cache data found.")

    # 3. Standard Analysis for HYBRID
    # Modified: Now includes Native for baseline comparison
    print("\n--- 3. Generating Analysis for HYBRID ---")
    df_hybrid = df[df["Cache"].isin(["WarmHybrid", "Native"])].copy()
    if not df_hybrid.empty:
        plot_standard_analysis(df_hybrid, "Hybrid", file_ext, save_individual)
    else:
        print("No Hybrid cache data found.")

    # 4. Comparison Charts (Speedups)
    # Re-fetch pure Cold/Hybrid frames without Native (optional, but cleaner for merging)
    df_cold_pure = df[df["Cache"] == "Cold"].copy()

    if not df_cold_pure.empty:
        # Cold vs Hybrid
        df_hybrid_pure = df[df["Cache"] == "WarmHybrid"].copy()
        if not df_hybrid_pure.empty:
            plot_speedup_compare_caches(df_cold_pure, df_hybrid_pure, "Hybrid", file_ext, save_individual)

        # Cold vs Standard
        df_std_pure = df[df["Cache"] == "WarmStd"].copy()
        if not df_std_pure.empty:
            plot_speedup_compare_caches(df_cold_pure, df_std_pure, "Standard", file_ext, save_individual)

    print("\nDone.")