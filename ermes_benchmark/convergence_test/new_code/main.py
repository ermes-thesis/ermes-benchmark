import os
import sys

# Disable pycache generation
sys.dont_write_bytecode = True
import holoviews as hv
import shutil
import inspect
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# Custom modules
import config
import data_processor
from plots import latency, distribution, topology, overhead_plots as overhead

def main():
    # ==========================================
    # 1. Setup Paths and Output Directory
    # ==========================================
    
    # Determine the directory where main.py is located
    current_file_path = inspect.getfile(inspect.currentframe())
    base_dir = Path(current_file_path).parent

    # Resolve input file paths using config
    files = [
        (base_dir / rel_path).resolve() 
        for rel_path in config.relative_files
    ]

    # Resolve output directory
    output_dir = os.path.join(base_dir, config.out_dir)
    output_dir = Path(output_dir).resolve()

    # Clean and recreate output directory
    if output_dir.exists() and output_dir.is_dir():
        for item in output_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)

    # ==========================================
    # 2. Data Processing Phase
    # ==========================================
    
    full_dfs = []

    print(f"Starting analysis for {len(files)} ZIP files...")

    for f in files:
        csv, log = data_processor.processa_zip_files(f)
        parsed_log = data_processor.parse_log(log)
        print(f"Processed {len(csv)} CSV files and {len(log)} LOG files from ZIP archives.")
        
        dfs = data_processor.parse_dfs(csv, parsed_log)
        print(f"Parsed {len(dfs)} DataFrames from CSV files.")
    
        dfs, eq_timestamp = data_processor.find_equilibrium_timestamp(dfs)

        print(f"Equilibrium Timestamp from file {f}: {eq_timestamp}")

        if full_dfs == []:
            full_dfs = dfs
        else:
            for i, df in enumerate(dfs):
                full_dfs[i] = pd.concat([full_dfs[i], df], ignore_index=True)
    
    # Extract message counts from logs for overhead analysis
    message_counter = data_processor.find_message_counter_from_log(log, config.messages_log_strings, data_processor.experiment_start_time(dfs), data_processor.experiment_end_time(dfs))
    # ==========================================
    # 3. Plotting Phase
    # ==========================================
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    overhead.plot_stacked_bar_chart(message_counter)
    plt.savefig(f'{output_dir}/message_counts_{timestamp_str}.png', dpi=300, bbox_inches='tight')
    plt.close()

    chord = overhead.create_chord_diagram(message_counter)
    hv.save(chord, f'{output_dir}/messaggi_chord_diagram_{timestamp_str}.html')
    
    # 3.1 Latency Analysis (Line Plot)
    print("Generating execution time analysis...")
    latency.plot_logs_avg_latency(full_dfs)
    plt.savefig(f'{output_dir}/execution_time_analysis_{timestamp_str}.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3.2 Local vs Remote Executions (Bar Chart)
    print("Generating local vs remote executions chart...")
    distribution.local_vs_remote_number_of_executions(full_dfs, len(config.relative_files))
    plt.savefig(f'{output_dir}/local_vs_remote_executions_{timestamp_str}.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3.3 Latency Boxplot (Custom)
    print("Generating latency boxplot...")
    latency.local_vs_remote_latency(full_dfs)
    plt.savefig(f'{output_dir}/local_vs_remote_latency_{timestamp_str}.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3.4 Average Latency Heatmap
    print("Generating avg latency heatmap...")
    latency.plot_heatmap_avg_latency(full_dfs)
    plt.savefig(f'{output_dir}/heatmap_avg_latency_{timestamp_str}.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3.5 Task Count Heatmap
    print("Generating task count heatmap...")
    distribution.plot_heatmap_count_tasks(full_dfs, len(config.relative_files))
    plt.savefig(f'{output_dir}/heatmap_count_tasks_{timestamp_str}.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3.6 Latency Violin Plot
    print("Generating latency violin plot...")
    latency.local_vs_remote_latency_violin(full_dfs)
    plt.savefig(f'{output_dir}/local_vs_remote_latency_violin_{timestamp_str}.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3.7 Topology Tree with Sparklines
    print("Generating topology tree...")
    fig_tree = topology.plot_tree_with_sparklines(config.tree, full_dfs, len(config.relative_files))
    if fig_tree:
        fig_tree.savefig(f'{output_dir}/tree_with_sparklines_{timestamp_str}.png', dpi=300, bbox_inches='tight')
    # Note: We don't plt.close() fig_tree immediately if we want to show it, 
    # but usually in batch scripts we close it.
    
    print(f"All processing complete. Outputs saved to: {output_dir}")
    # plt.show() # Optional: uncomment if running interactively
if __name__ == "__main__":
    main()