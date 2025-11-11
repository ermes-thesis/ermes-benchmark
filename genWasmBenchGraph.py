import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys

# ---------------------------------------------------------------------
# 1. Load benchmark data
# ---------------------------------------------------------------------

# Check if arguments were provided
if len(sys.argv) < 3:
    print("Warning: File paths not provided. Using defaults 'results_cold.json' and 'results_warm.json'")
    file_path_cold = "results_cold.json"
    file_path_warm = "results_warm.json"
else:
    file_path_cold = sys.argv[1]
    file_path_warm = sys.argv[2]

def run(file_path, out_suffix=""):
    # Open the file safely
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            benchmark_data = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
        return # Exits the run() function but allows the script to continue (if the other file exists)

    # ---------------------------------------------------------------------
    # 2. Parse the Go benchmark data
    # ---------------------------------------------------------------------
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
        return

    df = pd.DataFrame(records)
    print(f"--- Benchmark Data Analyzed ({out_suffix}) ---")
    print(df.head())
    print("-----------------------------------\n")

    # ---------------------------------------------------------------------
    # 3. Create Labels and Sorting for plots
    # ---------------------------------------------------------------------

    # Original and complete X label (for the memory plot)
    df["X_label_original"] = df["Runtime"] + "\n" + df["Compilation"] + "\n" + df["Optimization"]
    # Save the original order to force plot sorting
    xaxis_order_original = df['X_label_original'].unique()


    # Simpler X label (for time and speedup plots)
    def create_simple_label(row):
        if row["Runtime"].lower() == "native":
            return row["Runtime"]
        else:
            return f"{row['Runtime']}\n{row['Compilation']}"
    df["X_label_simple"] = df.apply(create_simple_label, axis=1)
    # Save the original order to force plot sorting
    xaxis_order_simple = df['X_label_simple'].unique()


    # Sort algorithms uniquely to force color consistency
    all_algorithms = sorted(df['Algorithm'].unique())

    # ---------------------------------------------------------------------
    # 4. Visualization setup
    # ---------------------------------------------------------------------
    sns.set_theme(style="whitegrid", font_scale=1.2)
    palette = "Set2"

    # ---------------------------------------------------------------------
    # 5. Create Combined Figure (Custom 2x2 Layout)
    # ---------------------------------------------------------------------
    # figsize wider (20) and a bit shorter (16)
    fig = plt.figure(figsize=(20, 16))
    # Add suffix to title
    fig.suptitle(f"Execution time analysis ({out_suffix} start)", fontsize=18, y=0.98) # y=0.98 to make space for the legend

    # 2x2 Grid: 2 plots on top, 1 plot spanning the bottom
    ax1 = plt.subplot2grid((2, 2), (0, 0)) # Row 0, Col 0
    ax2 = plt.subplot2grid((2, 2), (0, 1)) # Row 0, Col 1
    ax3 = plt.subplot2grid((2, 2), (1, 0), colspan=2) # Row 1, Col 0, spanning 2 columns

    # --- Plot 1: Average Execution Time (NO Optimizations) ---
    # Filter for NoOpts + baselines (Native)
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
    # Save legend handles from the first plot (which includes "Native")
    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend_.remove() # Remove legend to merge later

    # --- Plot 2: Average Execution Time (WITH Optimizations) ---
    # Filter for WithOpts + baselines (Native)
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

    # Pivot table to get NoOpts and WithOpts side-by-side
    df_pivot = df_avg.pivot_table(
        index=["Algorithm", "Runtime", "Compilation"],
        columns="Optimization",
        values="ns/op"
    ).reset_index()

    # Calculate speedup only if both columns exist
    if "NoOpts" in df_pivot.columns and "WithOpts" in df_pivot.columns:
        df_pivot["Speedup"] = df_pivot["NoOpts"] / df_pivot["WithOpts"]

        # Create simple label for pivot data
        df_pivot["X_label_simple"] = df_pivot.apply(create_simple_label, axis=1)

        # Filter only rows where speedup was calculated
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

        # Add a line at y=1.0 for reference
        line = ax3.axhline(y=1.0, color='k', linestyle='--', label='No Speedup (1.0x)')

        ax3.set_title("Speedup (Time NoOpts / Time WithOpts)")
        ax3.set_ylabel("Speedup (Higher is better)")
        ax3.set_xlabel("Runtime")
        ax3.tick_params(axis="x", labelsize=12)

        # Remove ax3's specific legend
        ax3.legend_.remove()

        # Add the speedup line to the saved handles
        handles.append(line)
        labels.append(line.get_label())

        print(f"Speedup plot generated as part of combined_time_plots_{out_suffix}.pdf")
    else:
        print("Warning: 'NoOpts' or 'WithOpts' columns not found after pivot. Skipping speedup plot.")
        ax3.set_title("Speedup (Data not available)")
        ax3.text(0.5, 0.5, "Could not calculate speedup (missing data)",
                 horizontalalignment='center', verticalalignment='center',
                 transform=ax3.transAxes, color='red')

    # --- Global Legend and Saving ---

    # Calculate number of columns for the legend
    num_labels = len(labels)
    # Try to put a maximum of 6 items per row
    ncol = min(num_labels, 6)

    # Add the global legend at the TOP of the FIGURE
    fig.legend(
        handles=handles,
        labels=labels,
        title="Algorithm",
        loc='upper center',          # Position at top center
        bbox_to_anchor=(0.5, 0.95),  # (0.5=center X, 0.95=near top Y)
        borderaxespad=0.1,
        ncol=ncol                    # Number of columns
    )

    # Adjust layout to make space for the legend at the TOP and the title
    plt.subplots_adjust(
        top=0.88,    # Space for suptitle and legend at top
        bottom=0.05, # Reclaim space at bottom
        left=0.05,
        right=0.98,
        hspace=0.20, # Vertical space between plot rows
        wspace=0.1   # Horizontal space between side-by-side plots
    )

    plt.savefig(f"combined_time_plots_{out_suffix}.pdf")
    plt.close(fig) # Close the combined figure


    # ---------------------------------------------------------------------
    # 8. Plot 4: Memory Usage (Like original fig2.png) - SEPARATE
    # ---------------------------------------------------------------------
    plt.figure(figsize=(15, 6)) # Increased width for labels
    sns.barplot(
        data=df,
        x="X_label_original", # Use the original full X label
        y="B/op",
        hue="Algorithm",
        palette=palette,
        hue_order=all_algorithms, # Force color consistency
        order=xaxis_order_original # Force X-axis order
    )
    plt.yscale("log")
    plt.title(f"Average Memory Usage per Runtime ({out_suffix} start)") # Added suffix
    plt.ylabel("Bytes per Operation (log scale)")
    plt.xlabel("Runtime Configuration") # Updated label
    plt.xticks(fontsize=10) # Shrunk font to avoid overlap
    plt.legend(
        title="Algorithm",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        borderaxespad=0
    )
    plt.tight_layout()
    plt.savefig(f"memory_{out_suffix}.pdf")
    plt.close()

    print(f"\n--- Process completed ({out_suffix}) ---")
    print("Generated plots:")
    print(f"- combined_time_plots_{out_suffix}.pdf (Combined time and speedup plots)")
    print(f"- memory_{out_suffix}.pdf (Memory usage)")
    print("------------------------------")

# Run for both files
print("--- Starting COLD process ---")
run(file_path_cold, "cold")
print("\n--- Starting WARM process ---")
run(file_path_warm, "warm")