import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys

# ---------------------------------------------------------------------
# 1. Global Setup
# ---------------------------------------------------------------------

# Set theme and palette globally
sns.set_theme(style="whitegrid", font_scale=1.2)
palette = "Set2"

# Helper function moved to global scope
def create_simple_label(row):
    """Creates a simpler X-axis label (e.g., 'Wasmedge\nAOT')"""
    if row["Runtime"].lower() == "native":
        return row["Runtime"]
    else:
        return f"{row['Runtime']}\n{row['Compilation']}"

# ---------------------------------------------------------------------
# 2. Main Function for Parsing and Plotting
# ---------------------------------------------------------------------

def run_and_plot(file_path, out_suffix="", master_order=None, master_algos=None):
    """
    Parses a single benchmark file, generates its plots, and returns its average data.
    If master_order and master_algos are provided, uses them for plot consistency.
    If not, it generates them from its own data.
    """
    # Open the file safely
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            benchmark_data = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
        return None, None, None # Return None on failure

    # --- Parse the Go benchmark data ---
    pattern = re.compile(
        # Search for lines starting with "BenchmarkExecutionTime_" and containing "ns/op"
        r"^(BenchmarkExecutionTime_([A-Za-z0-9_]+)-\d+)\s+(\d+)\s+(\d+(?:\.\d+)?)\s+ns/op"
    )

    records = []
    for line in benchmark_data.splitlines():
        match = pattern.search(line)
        if not match:
            continue

        full_tag = match.group(2)
        num_executions = int(match.group(3))
        ns_per_op = round(float(match.group(4)))

        # Extract B/op and allocs/op if present
        b_op_match = re.search(r"(\d+)\s+B/op", line)
        allocs_op_match = re.search(r"(\d+)\s+allocs/op", line)

        bytes_per_op = int(b_op_match.group(1)) if b_op_match else 0
        allocs_per_op = int(allocs_op_match.group(1)) if allocs_op_match else 0

        parts = full_tag.split("_")
        runtime = parts[0].capitalize()
        compilation = "None"
        optimization = "None"
        algorithm_name = "Unknown"

        if len(parts) == 2: # E.g.: Native_Fibonacci
            algorithm_name = parts[1]
            compilation = "Native" # Clearer label
            optimization = "Native" # Clearer label
        elif len(parts) == 4: # E.g.: Wasmedge_AOT_NoOpts_Fibonacci
            compilation = parts[1].capitalize()
            optimization = parts[2] # No .capitalize() to preserve "NoOpts" and "WithOpts"
            algorithm_name = parts[3]
        else:
            print(f"Warning: Skipping unrecognized tag format: {full_tag}")
            continue

        # Add suffixes to algorithm names
        if "TailFibonacci" == algorithm_name:
            algorithm_name = algorithm_name + " (20k)"
        if "Fibonacci" == algorithm_name:
            algorithm_name = algorithm_name + " (40)"

        records.append({
            "Runtime": runtime,
            "Compilation": compilation,
            "Algorithm": algorithm_name,
            "Optimization": optimization,
            "Iterations": num_executions,
            "ns/op": ns_per_op,
            "B/op": bytes_per_op,
            "allocs/op": allocs_per_op,
        })

    if not records:
        print(f"Error: No benchmark data found in '{file_path}'. Skipping this file.")
        return None, None, None # Return None on failure

    df = pd.DataFrame(records)
    print(f"--- Benchmark Data Analyzed ({out_suffix}) ---")
    print(df.head())
    print("-----------------------------------\n")

    # --- Create Labels and Sorting for plots ---

    # Original and complete X label (for the memory plot)
    df["X_label_original"] = df["Runtime"] + "\n" + df["Compilation"] + "\n" + df["Optimization"]
    # Use master order if provided, otherwise generate it
    xaxis_order_original = master_order['original'] if master_order else df['X_label_original'].unique()


    # Simpler X label (for time and speedup plots)
    df["X_label_simple"] = df.apply(create_simple_label, axis=1)
    # Use master order if provided, otherwise generate it
    xaxis_order_simple = master_order['simple'] if master_order else df['X_label_simple'].unique()


    # Sort algorithms uniquely to force color consistency
    all_algorithms = master_algos if master_algos else sorted(df['Algorithm'].unique())

    # --- Create Combined Figure (Custom 2x2 Layout) ---
    fig = plt.figure(figsize=(20, 16))
    fig.suptitle(f"Execution time analysis ({out_suffix} start)", fontsize=18, y=0.98) # y=0.98 to make space for the legend

    ax1 = plt.subplot2grid((2, 2), (0, 0)) # Row 0, Col 0
    ax2 = plt.subplot2grid((2, 2), (0, 1)) # Row 0, Col 1
    ax3 = plt.subplot2grid((2, 2), (1, 0), colspan=2) # Row 1, Col 0, spanning 2 columns

    # --- Plot 1: Average Execution Time (NO Optimizations) ---
    df_no_opts = df[df["Optimization"].isin(["NoOpts", "Native"])]

    sns.barplot(
        data=df_no_opts,
        x="X_label_simple",
        y="ns/op",
        hue="Algorithm",
        palette=palette,
        ax=ax1,
        hue_order=all_algorithms, # Force color consistency
        order=xaxis_order_simple  # Force X-axis order
    )

    ax1.set_yscale("log")
    ax1.set_title("Average Execution Time - NO Optimizations (log scale)")
    ax1.set_ylabel("ns/op (log scale)")
    ax1.set_xlabel("") # Remove X label
    ax1.tick_params(axis="x", labelsize=12)
    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend_.remove() # Remove legend to merge later

    # --- Plot 2: Average Execution Time (WITH Optimizations) ---
    df_with_opts = df[df["Optimization"].isin(["WithOpts", "Native"])]

    sns.barplot(
        data=df_with_opts,
        x="X_label_simple",
        y="ns/op",
        hue="Algorithm",
        palette=palette,
        ax=ax2,
        hue_order=all_algorithms, # Force color consistency
        order=xaxis_order_simple  # Force X-axis order
    )

    ax2.set_yscale("log")
    ax2.set_title("Average Execution Time - WITH Optimizations (log scale)")
    ax2.set_ylabel("") # Remove Y label
    ax2.set_xlabel("") # Remove X label
    ax2.tick_params(axis="x", labelsize=12)
    ax2.legend_.remove() # Remove legend

    # --- Plot 3: Speedup (NoOpts / WithOpts) ---
    # Aggregate data before pivot to get the mean
    df_avg = df.groupby(["Algorithm", "Runtime", "Compilation", "Optimization"])["ns/op"].mean().reset_index()

    df_pivot = df_avg.pivot_table(
        index=["Algorithm", "Runtime", "Compilation"],
        columns="Optimization",
        values="ns/op"
    ).reset_index()

    if "NoOpts" in df_pivot.columns and "WithOpts" in df_pivot.columns:
        df_pivot["Speedup"] = df_pivot["NoOpts"] / df_pivot["WithOpts"]
        df_pivot["X_label_simple"] = df_pivot.apply(create_simple_label, axis=1)
        df_speedup = df_pivot.dropna(subset=["Speedup"])

        sns.barplot(
            data=df_speedup,
            x="X_label_simple",
            y="Speedup",
            hue="Algorithm",
            palette=palette,
            ax=ax3,
            hue_order=all_algorithms, # Force color consistency
            order=xaxis_order_simple  # Force X-axis order
        )

        line = ax3.axhline(y=1.0, color='k', linestyle='--', label='No Speedup (1.0x)')
        ax3.set_title("Speedup (Time NoOpts / Time WithOpts)")
        ax3.set_ylabel("Speedup (Higher is better)")
        ax3.set_xlabel("Runtime")
        ax3.tick_params(axis="x", labelsize=12)
        ax3.legend_.remove()
        handles.append(line)
        labels.append(line.get_label())
        print(f"Speedup plot generated as part of combined_time_plots_{out_suffix}{file_ext}")
    else:
        print("Warning: 'NoOpts' or 'WithOpts' columns not found after pivot. Skipping speedup plot.")
        ax3.set_title("Speedup (Data not available)")
        ax3.text(0.5, 0.5, "Could not calculate speedup (missing data)",
                 horizontalalignment='center', verticalalignment='center',
                 transform=ax3.transAxes, color='red')

    # --- Global Legend and Saving ---
    num_labels = len(labels)
    ncol = min(num_labels, 6)
    fig.legend(
        handles=handles,
        labels=labels,
        title="Algorithm",
        loc='upper center',
        bbox_to_anchor=(0.5, 0.95),
        borderaxespad=0.1,
        ncol=ncol
    )
    plt.subplots_adjust(
        top=0.88,
        bottom=0.05,
        left=0.05,
        right=0.98,
        hspace=0.20,
        wspace=0.1
    )
    plt.savefig(f"combined_time_plots_{out_suffix}{file_ext}")
    plt.close(fig)

    # --- Plot 4: Memory Usage ---
    plt.figure(figsize=(15, 6))
    sns.barplot(
        data=df,
        x="X_label_original",
        y="B/op",
        hue="Algorithm",
        palette=palette,
        hue_order=all_algorithms,
        order=xaxis_order_original
    )
    plt.yscale("log")
    plt.title(f"Average Memory Usage per Runtime ({out_suffix} start)")
    plt.ylabel("Bytes per Operation (log scale)")
    plt.xlabel("Runtime Configuration")
    plt.xticks(fontsize=10)
    plt.legend(
        title="Algorithm",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        borderaxespad=0
    )
    plt.tight_layout()
    #plt.savefig(f"memory_{out_suffix}{file_ext}")
    plt.close()

    print(f"\n--- Process completed ({out_suffix}) ---")
    print("Generated plots:")
    print(f"- combined_time_plots_{out_suffix}{file_ext}")
    print(f"- memory_{out_suffix}{file_ext}")
    print("------------------------------")

    # Pack order and algo lists to return
    master_order_out = {'simple': xaxis_order_simple, 'original': xaxis_order_original}

    # Return the average data and the generated order/algo lists
    return df_avg, master_order_out, all_algorithms


# ---------------------------------------------------------------------
# 3. Main Execution Block
# ---------------------------------------------------------------------


# === CONFIG ===
# Imposta l'estensione predefinita
file_ext = ".png"
args = sys.argv[1:] # Copia gli argomenti

# Controlla il flag --pdf
if "--pdf" in args:
    file_ext = ".pdf"
    args.remove("--pdf") # Rimuovi il flag dalla lista degli argomenti
    print("Output format set to PDF.")
else:
    print("Output format set to PNG (default).")

# Get file paths
if len(sys.argv) < 3:
    print("Warning: File paths not provided. Using defaults 'results_cold.json' and 'results_warm.json'")
    file_path_cold = "results_cold.json"
    file_path_warm = "results_warm.json"
else:
    file_path_cold = sys.argv[1]
    file_path_warm = sys.argv[2]

# --- Run for COLD (This establishes the "master" order) ---
print("--- Starting COLD process ---")
df_avg_cold, master_order, master_algos = run_and_plot(file_path_cold, "cold")

# --- Run for WARM (This uses the "master" order) ---
print("\n--- Starting WARM process ---")
if master_order and master_algos:
    df_avg_warm, _, _ = run_and_plot(file_path_warm, "warm", master_order, master_algos)
else:
    print("Skipping WARM run because COLD run failed or produced no data.")
    df_avg_warm = None

# --- Generate NEW Speedup Plot (Cold vs Warm) ---
if df_avg_cold is not None and df_avg_warm is not None:
    print("\n--- Starting COLD vs WARM speedup plot generation ---")

    # Merge the average dataframes
    df_merged = pd.merge(
        df_avg_cold,
        df_avg_warm,
        on=["Algorithm", "Runtime", "Compilation", "Optimization"],
        suffixes=('_cold', '_warm')
    )

    # --- Create VERTICAL plot (2 rows, 1 col) ---
    fig, (ax1, ax2) = plt.subplots(
        2, 1, # 2 rows, 1 column
        figsize=(20, 16), # Tall figure
        sharex=True # Share the X-axis
    )
    fig.suptitle("Speedup (Time Cold Start / Time Warm Start)", fontsize=18, y=0.98)

    # --- Plot 1: NO Optimizations ---
    df_speedup_no_opts = df_merged[df_merged["Optimization"] == "NoOpts"].dropna(subset=["ns/op_cold", "ns/op_warm"])
    if not df_speedup_no_opts.empty:
        df_speedup_no_opts["Speedup_ColdWarm"] = df_speedup_no_opts["ns/op_cold"] / df_speedup_no_opts["ns/op_warm"]
        df_speedup_no_opts["X_label_simple"] = df_speedup_no_opts.apply(create_simple_label, axis=1)

        sns.barplot(
            data=df_speedup_no_opts,
            x="X_label_simple",
            y="Speedup_ColdWarm",
            hue="Algorithm",
            palette=palette,
            hue_order=master_algos,
            order=master_order['simple'],
            ax=ax1
        )
        ax1.axhline(y=1.0, color='k', linestyle='--', label='No Speedup (1.0x)')
        ax1.set_title("Speedup - NO Optimizations")
        ax1.set_ylabel("Speedup (log)")
        ax1.set_xlabel("") # Remove X label from top plot
        handles, labels = ax1.get_legend_handles_labels() # Get handles from this plot
        ax1.legend_.remove() # Remove individual legend
        ax1.set_yscale("log")
    else:
        ax1.set_title("Speedup - NO Optimizations (Data not available)")
        ax1.text(0.5, 0.5, "No data for NoOpts", horizontalalignment='center', verticalalignment='center', transform=ax1.transAxes, color='red')
        handles, labels = [], [] # Empty lists if no data

    # --- Plot 2: WITH Optimizations ---
    df_speedup_with_opts = df_merged[df_merged["Optimization"] == "WithOpts"].dropna(subset=["ns/op_cold", "ns/op_warm"])
    if not df_speedup_with_opts.empty:
        df_speedup_with_opts["Speedup_ColdWarm"] = df_speedup_with_opts["ns/op_cold"] / df_speedup_with_opts["ns/op_warm"]
        df_speedup_with_opts["X_label_simple"] = df_speedup_with_opts.apply(create_simple_label, axis=1)

        sns.barplot(
            data=df_speedup_with_opts,
            x="X_label_simple",
            y="Speedup_ColdWarm",
            hue="Algorithm",
            palette=palette,
            hue_order=master_algos,
            order=master_order['simple'],
            ax=ax2
        )
        ax2.axhline(y=1.0, color='k', linestyle='--', label='No Speedup (1.0x)')
        ax2.set_title("Speedup - WITH Optimizations")
        ax2.set_ylabel("Speedup (log)")
        ax2.set_xlabel("Runtime") # Keep X label on bottom plot
        ax2.tick_params(axis="x", labelsize=12)
        ax2.legend_.remove() # Remove individual legend
        ax2.set_yscale("log")
    else:
        ax2.set_title("Speedup - WITH Optimizations (Data not available)")
        ax2.text(0.5, 0.5, "No data for WithOpts", horizontalalignment='center', verticalalignment='center', transform=ax2.transAxes, color='red')

    # Add 'No Speedup' line to handles if not already there
    if "No Speedup (1.0x)" not in labels:
        handles.append(plt.Line2D([0], [0], color='k', linestyle='--', label='No Speedup (1.0x)'))
        labels.append('No Speedup (1.0x)')

    # --- Add Global Legend (Top) ---
    if handles: # Only add legend if we have handles
        num_labels = len(labels)
        ncol = min(num_labels, 6)
        fig.legend(
            handles=handles,
            labels=labels,
            title="Algorithm",
            loc='upper center',
            bbox_to_anchor=(0.5, 0.95), # Below suptitle
            borderaxespad=0.1,
            ncol=ncol
        )

    # Adjust layout
    plt.subplots_adjust(
        top=0.88,    # Make room for title and legend
        bottom=0.05,
        left=0.05,
        right=0.98,
        hspace=0.20 # Space between vertical plots
    )

    plt.savefig(f"speedup_cold_vs_warm{file_ext}")
    plt.close()

    print(f"Generated plot: speedup_cold_vs_warm{file_ext}")
    print("---------------------------------------------------\n")

else:
    print("\n--- Skipping COLD vs WARM speedup plot (missing data from cold or warm run) ---")