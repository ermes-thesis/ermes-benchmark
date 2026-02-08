import inspect
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

# Configurazione cartelle
data_rel_path = 'data/variable_accesses'
output_dir_name = 'output_img/variable_accesses'
output_filename = 'global_comparison.png'

# Nome della colonna X
X_AXIS_COL = "Accesses"

def build_aggregated_dict_global(csv_files):
    """
    Legge tutti i CSV e crea un dizionario strutturato:
    data[ (filename, mode) ][ x_val ] = row_dict
    """
    aggregated = {}
    unique_files = set()

    for file_path in csv_files:
        filename = file_path.stem
        unique_files.add(filename)

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"⚠️ Skipping {filename}: {e}")
            continue

        if X_AXIS_COL not in df.columns or 'Mode' not in df.columns:
            print(f"⚠️ Skipping {filename}: Colonne mancanti.")
            continue

        for _, row in df.iterrows():
            try:
                x_val = int(row[X_AXIS_COL])
                mode = str(row['Mode'])
            except ValueError:
                continue

            series_key = (filename, mode)

            if series_key not in aggregated:
                aggregated[series_key] = {}

            row_dict = row.to_dict()
            for k in row_dict:
                if isinstance(row_dict[k], (int, float, np.number)):
                    row_dict[k] = float(row_dict[k])

            aggregated[series_key][x_val] = row_dict

    return aggregated, sorted(list(unique_files))

def plot_global_comparison(aggregated_data, unique_files, save_path=None):
    if not aggregated_data:
        print("No data to plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    # Ordiniamo le chiavi per la legenda
    sorted_keys = sorted(aggregated_data.keys(), key=lambda k: (k[0], k[1]))

    for (filename, mode) in sorted_keys:
        xs, avg_vals = [], []

        series_data = aggregated_data[(filename, mode)]
        sorted_x = sorted(series_data.keys())

        for x in sorted_x:
            row = series_data[x]
            if "AverageLatency" in row:
                xs.append(x)
                avg_vals.append(row["AverageLatency"])

        if not xs: continue

        xs_arr = np.array(xs)
        avg_arr = np.array(avg_vals)

        # --- LOGICA DI STILE UNIFICATA ---
        fname_lower = filename.lower()
        mode_lower = mode.lower()

        # 1. Architettura -> Colore e Marker
        if 'centralized' in fname_lower:
            color = 'tab:orange'
            marker = 'o'          # Cerchio
            arch_name = "centralized"
        elif 'distributed' in fname_lower:
            color = 'tab:blue'
            marker = '^'          # Triangolo
            arch_name = "distributed"
        else:
            color = 'tab:gray'
            marker = 'd'          # Diamante (Fallback)
            arch_name = filename

        # 2. Consistenza -> Tratteggio
        # Normalizziamo mode_lower se non corrisponde esattamente
        if 'sequential' in mode_lower:
            linestyle = '-'
            clean_mode = 'sequential'
        elif 'eventual' in mode_lower:
            linestyle = '--'
            clean_mode = 'eventual'
        else:
            linestyle = ':'
            clean_mode = mode_lower

        # 3. Etichetta Legenda
        label_text = f"{arch_name} [{clean_mode}]"

        # Plot solo linea e marker
        ax.plot(xs_arr, avg_arr, marker=marker, linestyle=linestyle,
                color=color, linewidth=2, label=label_text, markersize=4)

    ax.set_xlabel(f"Number of Accesses ({X_AXIS_COL})")
    ax.set_ylabel("Average Latency (ms)")
    ax.set_ylim(bottom=0)
    ax.set_title("Global Comparison: Latency vs Accesses")

    ax.grid(True, alpha=0.3)

    # Legenda interna
    ax.legend(loc='best', title="Configurations", framealpha=0.9, handlelength=3, handletextpad=1)

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)
    plt.close(fig)

sys.dont_write_bytecode = True

def main():
    current_file_path = inspect.getfile(inspect.currentframe())
    base_dir = Path(current_file_path).parent

    input_dir = (base_dir / data_rel_path).resolve()
    output_dir = (base_dir / output_dir_name).resolve()

    print(f"Reading CSVs from: {input_dir}")

    if not input_dir.exists():
        print("❌ Input directory not found.")
        exit(1)

    csv_files = list(input_dir.glob("*.csv"))
    if not csv_files:
        print("❌ No CSV files found.")
        exit(0)

    print(f"Found {len(csv_files)} files. Aggregating data...")

    aggregated_data, unique_files = build_aggregated_dict_global(csv_files)

    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / output_filename

    plot_global_comparison(aggregated_data, unique_files, save_path=save_path)

    print(f"\n✅ Plot saved to: {save_path}")

if __name__ == "__main__":
    main()