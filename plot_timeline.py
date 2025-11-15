import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
from pathlib import Path

sns.set_theme(style="whitegrid", font_scale=1.2)

def plot_timelines(csv_files, output_file="memory_timeline.png"):
    plt.figure(figsize=(16, 8))
    ax = plt.gca()

    palette = sns.color_palette("tab10", n_colors=len(csv_files))

    max_exec = 0

    for i, csv_path in enumerate(csv_files):
        if not os.path.exists(csv_path):
            print(f"Warning: File not found {csv_path}", file=sys.stderr)
            continue

        try:
            df = pd.read_csv(csv_path)
            if df.empty:
                print(f"Warning: Empty trace file {csv_path}", file=sys.stderr)
                continue

            # Estrai etichetta (es. "wasmedge")
            label = Path(csv_path).stem.replace("trace_sync_", "").replace("_", " ")

            # Grafico 1: RSS (Memoria Totale di Sistema)
            sns.lineplot(
                data=df,
                x="Execution_N",
                y="RSS_MB",
                label=label,
                linewidth=2.5,
                alpha=0.9,
                color=palette[i],
                ax=ax
            )

            if not df.empty:
                max_exec = max(max_exec, df["Execution_N"].max())

        except Exception as e:
            print(f"Error plotting {csv_path}: {e}", file=sys.stderr)

    ax.set_title("Total System Memory (RSS) after each Function Execution")
    ax.set_ylabel("RSS Memory (MB)")
    ax.set_xlabel("Number of Function Executions (Sequential)")
    ax.set_ylim(bottom=0)

    if max_exec > 0:
        ax.set_xlim(0, max_exec)

    # Legenda esterna
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)

    plt.tight_layout()

    plt.savefig(output_file, dpi=300)
    print(f"Chart saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot_timeline.py [--pdf] file1.csv file2.csv ...", file=sys.stderr)
        sys.exit(1)

    output_arg = "memory_timeline.png"
    files_to_plot = sys.argv[1:]

    if "--pdf" in files_to_plot:
        output_arg = "memory_timeline.pdf"
        files_to_plot.remove("--pdf")
        print("Output format set to PDF.")

    if not files_to_plot:
        print("Error: No CSV files provided to plot.", file=sys.stderr)
        sys.exit(1)

    plot_timelines(files_to_plot, output_arg)