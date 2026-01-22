import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
import argparse
from pathlib import Path

sns.set_theme(style="whitegrid", font_scale=1.2)

def plot_timelines(csv_files, output_file="memory_timeline.png"):
    plt.figure(figsize=(10, 6))
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

            # Estrai etichetta (es. "trace_sync_WasmEdge_interpreter_Hybrid.csv")
            # Rimuoviamo il prefisso e l'estensione, poi puliamo
            label = Path(csv_path).stem.replace("trace_sync_", "").replace("_", " ")

            # Semplificazioni opzionali per la legenda
            label = label.replace("Hybrid", "").replace("Standard", "")

            # Grafico 1: RSS (Memoria Totale di Sistema)
            sns.lineplot(
                data=df,
                x="Execution_N",
                y="RSS_MB",
                label=label,
                alpha=0.9,
                color=palette[i],
                ax=ax
            )

            if not df.empty:
                current_max = df["Execution_N"].max()
                if current_max > max_exec:
                    max_exec = current_max

        except Exception as e:
            print(f"Error plotting {csv_path}: {e}", file=sys.stderr)

    ax.set_ylabel("RSS Memory (MB)")
    ax.set_xlabel("Number of Function Executions (Sequential)")

    if max_exec > 0:
        ax.set_xlim(0, max_exec)

        # --- MODIFICA: Aggiunta righe verticali ogni 50 funzioni ---
        # range(start, stop, step)
        step = 50
        for x_pos in range(step, int(max_exec) + 1, step):
            ax.axvline(x=x_pos, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
        # -----------------------------------------------------------

    plt.tight_layout()

    plt.savefig(output_file, bbox_inches='tight')
    print(f"Chart saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot memory timeline from CSV files.")
    parser.add_argument("--output", default="memory_timeline.png", help="Output image filename")
    parser.add_argument("--pdf", action="store_true", help="Save as PDF (overrides extension of --output if present)")
    parser.add_argument("files", nargs="+", help="CSV files to plot")

    args = parser.parse_args()

    output_filename = args.output
    if args.pdf:
        base_name = os.path.splitext(output_filename)[0]
        output_filename = base_name + ".pdf"
        print("Output format forced to PDF.")

    plot_timelines(args.files, output_filename)