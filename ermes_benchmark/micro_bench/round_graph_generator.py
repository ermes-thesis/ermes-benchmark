import glob
import os
import matplotlib.pyplot as plt
import pandas as pd
import sys

def process_all_round_folders():
    # Percorsi base
    base_data_dir = "data/rounds"
    base_output_dir = "output_img/rounds"

    # Creazione cartella output
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)

    # Verifica input
    if not os.path.exists(base_data_dir):
        print(f"Errore: La cartella '{base_data_dir}' non esiste.")
        return

    subfolders = [f for f in os.listdir(base_data_dir) if os.path.isdir(os.path.join(base_data_dir, f))]

    if not subfolders:
        print(f"Nessuna sottocartella trovata in {base_data_dir}")
        return

    print(f"Trovate {len(subfolders)} cartelle da elaborare.")

    for folder_name in subfolders:
        print(f"--- Elaborazione: {folder_name} ---")

        search_path = os.path.join(base_data_dir, folder_name, "*.csv")
        csv_files = glob.glob(search_path)

        if not csv_files:
            continue

        plt.figure(figsize=(10, 6))
        files_plotted = 0

        # Ordina i file per coerenza
        csv_files.sort()

        for filename in csv_files:
            try:
                df = pd.read_csv(filename)
                base_label = os.path.splitext(os.path.basename(filename))[0]

                if 'Round' in df.columns and 'AverageLatency' in df.columns:
                    df = df.sort_values('Round')

                    fname_lower = base_label.lower()

                    # --- 1. Determinazione ARCHITETTURA (Colore + Marker) ---
                    # Richiesta: Marker distingue centralized/distributed

                    if 'centralized' in fname_lower:
                        color = 'tab:orange'
                        marker = 'o'          # Cerchio per Centralized
                        arch_name = "centralized"
                    elif 'distributed' in fname_lower:
                        color = 'tab:blue'
                        marker = '^'          # Triangolo per Distributed
                        arch_name = "distributed"
                    elif 'query_cache_disabled' in fname_lower:
                        color = 'tab:green'
                        marker = 's'          # Quadrato per Query Cache Disabled
                        arch_name = "query_cache_disabled"
                    else:
                        color = 'tab:gray'
                        marker = 'd'          # Diamante per altro
                        arch_name = base_label

                    # --- 2. Determinazione CONSISTENZA (Tratteggio) ---
                    # Richiesta: Tratteggio distingue eventual/sequential

                    mode = "Unknown"
                    if 'Mode' in df.columns and not df['Mode'].dropna().empty:
                        mode = str(df['Mode'].iloc[0])

                    mode_lower = mode.lower()

                    # Fallback sul nome file
                    if mode_lower not in ['sequential', 'eventual']:
                        if 'sequential' in fname_lower: mode_lower = 'sequential'
                        elif 'eventual' in fname_lower: mode_lower = 'eventual'

                    if mode_lower == 'sequential':
                        linestyle = '-'       # Continua
                    elif mode_lower == 'eventual':
                        linestyle = '--'      # Tratteggiata
                    else:
                        linestyle = ':'       # Punteggiata (Unknown)

                    # --- 3. COSTRUZIONE LEGENDA ---
                    label_text = f"{arch_name} [{mode_lower}]"

                    # Plot
                    plt.plot(df['Round'], df['AverageLatency'],
                             marker=marker,
                             linestyle=linestyle,
                             color=color,
                             linewidth=2,
                             markersize=7,    # Leggermente più grande per vedere bene il triangolo
                             label=label_text)

                    files_plotted += 1

            except Exception as e:
                print(f"Errore leggendo {filename}: {e}")

        if files_plotted > 0:
            plt.xlabel('Round (Time)')
            plt.ylabel('Average Latency (ms)')
            plt.title(f'Latency per Round - {folder_name}')
            plt.grid(True, linestyle='--', alpha=0.4)

            # handlelength aumentato per vedere bene il tratteggio
            plt.legend(title='Configurations', loc='best', handlelength=4, handletextpad=1)

            plt.tight_layout()

            output_file = os.path.join(base_output_dir, f"{folder_name}.png")
            plt.savefig(output_file, dpi=300)
            print(f"✅ Grafico salvato: {output_file}")

        plt.close()

if __name__ == "__main__":
    process_all_round_folders()