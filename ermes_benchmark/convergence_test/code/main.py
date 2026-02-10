import argparse
import inspect
import os
import shutil
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Disable pycache generation
sys.dont_write_bytecode = True

# Custom modules
import config
import data_processor
from plots import latency, distribution, topology, overhead_plots as overhead


def main():
    # ==========================================
    # 0. Parse Command Line Arguments
    # ==========================================
    parser = argparse.ArgumentParser(description="Analyze trace logs from ZIP files.")
    parser.add_argument(
        "subfolder",
        nargs="?",
        default="",
        help="Subfolder name for input (inside data_dir) and output (inside out_dir)"
    )
    args = parser.parse_args()

    # ==========================================
    # 1. Setup Paths and Output Directory
    # ==========================================

    # Determine the directory where main.py is located
    current_file_path = inspect.getfile(inspect.currentframe())
    base_dir = Path(current_file_path).parent

    # Resolve input directory using config AND subfolder argument
    data_dir_path = (base_dir / config.data_dir / args.subfolder).resolve()

    # Search for ALL zip files in the data directory
    print(f"Searching for ZIP files in: {data_dir_path}")

    if not data_dir_path.exists():
        print(f"ERROR: Directory {data_dir_path} does not exist.")
        return

    files = [f for f in data_dir_path.glob("*.zip") if not f.name.startswith("_")]

    # Sort files to ensure consistent processing order (optional but recommended)
    files.sort()

    if not files:
        print(f"ERROR: No .zip files found in {data_dir_path}")
        return

    # Resolve output directory using config AND subfolder argument
    output_dir = (base_dir / config.out_dir / args.subfolder).resolve()

    # Concat the "_new"
    output_dir = Path(str(output_dir) + "_new")

    # Clean and recreate output directory
    if output_dir.exists() and output_dir.is_dir():
        for item in output_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_dir = output_dir / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory set to: {output_dir}")

    # ==========================================
    # 2. Data Processing Phase
    # ==========================================

    full_dfs = []

    # Initialize a global dictionary to hold nested counters
    # Structure: { node_id: Counter({ (msg_type, remote_ip): count }) }
    total_message_counter = {}

    print(f"Starting analysis for {len(files)} ZIP files...")

    for f in files:
        print(f"Processing file: {f.name}...")

        # Extract and parse logs/csv
        csv, log = data_processor.process_zip_files(f)
        parsed_log = data_processor.parse_log(log)
        print(f"  Processed {len(csv)} CSV files and {len(log)} LOG files.")

        dfs = data_processor.parse_dfs(csv, parsed_log)
        print(f"  Parsed {len(dfs)} DataFrames.")

        # Find equilibrium
        dfs, eq_timestamp = data_processor.find_equilibrium_timestamp(dfs, args.subfolder)
        print(f"  Equilibrium Timestamp: {eq_timestamp}")

        # Aggregate DataFrames (Logic: merge lists of DFs index-wise)
        if not full_dfs:
            full_dfs = dfs
        else:
            # Ensure we don't crash if different zips produce different numbers of DFs
            limit = min(len(full_dfs), len(dfs))
            for i in range(limit):
                full_dfs[i] = pd.concat([full_dfs[i], dfs[i]], ignore_index=True)

        # Accumulate Message Counts (Overhead Analysis)
        start_t = data_processor.experiment_start_time(dfs)
        end_t = data_processor.experiment_end_time(dfs)

        current_counts = data_processor.find_message_counter_from_log(
            log,
            config.messages_log_strings,
            start_t,
            end_t
        )

        # FIX: Manually merge the nested dictionaries to avoid TypeError
        # current_counts structure: { node_id: { (msg_type, remote_ip): count } }
        for node_id, inner_counts in current_counts.items():
            if node_id not in total_message_counter:
                total_message_counter[node_id] = Counter()

            # Update the inner Counter for this specific node
            total_message_counter[node_id].update(inner_counts)

    # ==========================================
    # 2.1 Post-Processing: Calculate Averages
    # ==========================================

    num_files = len(files)
    avg_message_counter = {}

    print(f"Calculating averages across {num_files} files for overhead analysis...")

    for node, counts in total_message_counter.items():
        avg_message_counter[node] = Counter()
        for key, value in counts.items():
            # Calculate average per execution
            avg_message_counter[node][key] = value / num_files

    # ==========================================
    # 3. Plotting Phase
    # ==========================================

    # 3.0 Overhead Analysis (Using avg_message_counter)

    print("Generating overhead analysis (Average per run)...")
    overhead.plot_stacked_bar_chart(avg_message_counter)
    plt.savefig(f'{output_dir}/message_counts.png', dpi=300, bbox_inches='tight')
    plt.close()

    overhead.create_chord_diagram(avg_message_counter, f'{output_dir}/messaggi_chord_diagram')

    # 3.1 Latency Analysis (Line Plot)
    print("Generating execution time analysis...")
    latency.plot_logs_avg_latency(full_dfs, args.subfolder)
    plt.savefig(f'{output_dir}/execution_time_analysis.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_dir}/pdf/execution_time_analysis.pdf')
    plt.close()

    # 3.2 Local vs Remote Executions (Bar Chart)
    print("Generating local vs remote executions chart...")
    # Passing num_files to normalize the counts in the bars if needed inside the function
    distribution.local_vs_remote_number_of_executions(full_dfs, num_files)
    plt.savefig(f'{output_dir}/local_vs_remote_executions.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3.3 Latency Boxplot (Custom)
    print("Generating latency boxplot...")
    latency.local_vs_remote_latency(full_dfs)
    plt.savefig(f'{output_dir}/local_vs_remote_latency.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3.4 Average Latency Heatmap
    print("Generating avg latency heatmap...")
    latency.plot_heatmap_avg_latency(full_dfs)
    plt.savefig(f'{output_dir}/heatmap_avg_latency_.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3.5 Task Count Heatmap
    print("Generating task count heatmap...")
    distribution.plot_heatmap_count_tasks(full_dfs, num_files)
    plt.savefig(f'{output_dir}/heatmap_count_tasks.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3.6 Latency Violin Plot
    print("Generating latency violin plot...")
    latency.local_vs_remote_latency_violin(full_dfs)
    plt.savefig(f'{output_dir}/local_vs_remote_latency_violin.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_dir}/pdf/local_vs_remote_latency_violin.pdf')
    plt.close()
    latency.local_vs_remote_latency_violin_old(full_dfs)
    plt.savefig(f'{output_dir}/local_vs_remote_latency_violin_old.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_dir}/pdf/local_vs_remote_latency_violin_old.pdf')
    plt.close()

    # 3.7 Topology Tree with Sparklines
    print("Generating topology tree...")
    fig_tree = topology.plot_tree_with_sparklines(config.tree, config.domains, full_dfs, num_files)
    if fig_tree:
        fig_tree.savefig(f'{output_dir}/tree_with_sparklines.png', dpi=300, bbox_inches='tight')
        fig_tree.savefig(f'{output_dir}/pdf/tree_with_sparklines.pdf', bbox_inches='tight')
        plt.close(fig_tree)

    print(f"All processing complete. Outputs saved to: {output_dir}")


if __name__ == "__main__":
    main()
