import glob
import os
import matplotlib.pyplot as plt
import pandas as pd

def process_all_round_folders():
    # Percorsi base
    base_data_dir = "data/rounds"
    base_output_dir = "output_img/rounds"

    # Assicurati che la cartella di output esista
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)
        print(f"Creata cartella di output: {base_output_dir}")

    # Verifica che la cartella dati esista
    if not os.path.exists(base_data_dir):
        print(f"Errore: La cartella '{base_data_dir}' non esiste.")
        return

    # Trova tutte le sottocartelle in data/rounds
    # os.listdir elenca tutto, quindi filtriamo solo le directory
    subfolders = [f for f in os.listdir(base_data_dir) if os.path.isdir(os.path.join(base_data_dir, f))]

    if not subfolders:
        print(f"Nessuna sottocartella trovata in {base_data_dir}")
        return

    print(f"Trovate {len(subfolders)} cartelle da elaborare.")

    # Cicla attraverso ogni sottocartella
    for folder_name in subfolders:
        print(f"--- Elaborazione cartella: {folder_name} ---")

        # Costruisce il pattern per trovare i csv in QUESTA specifica sottocartella
        # os.path.join gestisce automaticamente gli slash corretti per il sistema operativo
        search_path = os.path.join(base_data_dir, folder_name, "*.csv")
        csv_files = glob.glob(search_path)

        if not csv_files:
            print(f"Nessun file CSV trovato in {folder_name}, salto.")
            continue

        # Crea una nuova figura per questa cartella
        plt.figure(figsize=(10, 6))

        files_plotted = 0

        # Loop per ogni CSV nella cartella corrente
        for filename in csv_files:
            try:
                # Leggi il CSV
                df = pd.read_csv(filename)

                # Pulisce il nome del file per usarlo come etichetta nella legenda
                label = os.path.splitext(os.path.basename(filename))[0]

                # Controlla colonne richieste
                if 'Round' in df.columns and 'AverageLatency' in df.columns:
                    # Ordina per Round per sicurezza
                    df = df.sort_values('Round')

                    # Aggiungi la riga al grafico
                    plt.plot(df['Round'], df['AverageLatency'], marker='o', label=label)
                    files_plotted += 1
                else:
                    print(f"Skipping {filename}: colonne 'Round' o 'AverageLatency' mancanti.")

            except Exception as e:
                print(f"Errore leggendo {filename}: {e}")

        # Se abbiamo aggiunto almeno un grafico, salviamo l'immagine
        if files_plotted > 0:
            # Formattazione del grafico
            plt.xlabel('Round (Time)')
            plt.ylabel('Average Latency (ms)')
            plt.title(f'Average Latency - {folder_name}') # Titolo dinamico con il nome cartella
            plt.legend(title='Files')
            plt.grid(True, linestyle='--', alpha=0.7)

            # Definisce il nome del file di output
            output_file = os.path.join(base_output_dir, f"{folder_name}.png")

            # Salva
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Grafico salvato in: {output_file}")
        else:
            print(f"Nessun dato valido trovato per il grafico in {folder_name}.")

        plt.close()

if __name__ == "__main__":
    process_all_round_folders()