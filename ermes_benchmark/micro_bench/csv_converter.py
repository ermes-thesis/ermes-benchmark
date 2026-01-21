import pandas as pd
import sys
import os

def convert_seed_csv_to_aggregated(input_file, interval_seconds=15):
    # Controllo se il file esiste
    if not os.path.isfile(input_file):
        print(f"Errore: Il file '{input_file}' non esiste.")
        return

    print(f"Elaborazione di {input_file}...")

    try:
        # Carica il file originale
        df = pd.read_csv(input_file)

        # Lista delle colonne numeriche su cui fare la media
        # Escludiamo 'Round' (chiave di raggruppamento) e 'Seed'
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if 'Seed' in numeric_cols: numeric_cols.remove('Seed')
        if 'Round' in numeric_cols: numeric_cols.remove('Round')

        # Raggruppa per Round e calcola la media
        df_grouped = df.groupby('Round')[numeric_cols].mean().reset_index()

        # Ricostruisce le colonne temporali relative
        df_grouped['TimeRelativeStart'] = (df_grouped['Round'] - 1) * interval_seconds
        df_grouped['TimeRelativeEnd'] = df_grouped['Round'] * interval_seconds

        # Definisce l'ordine delle colonne come nel nuovo formato target
        target_columns = [
            'Round', 'TimeRelativeStart', 'TimeRelativeEnd',
            'AverageLatency', 'MedianLatency',
            'TotalRequests', 'CorrectRequests', 'FailedRequests',
            'VarianceLatency',
            'Q1', 'Q2', 'Q3', 'Q4',
            '404', '423', '500', '503', '508', 'OtherErrors'
        ]

        # Se mancano colonne (es. errori che erano a 0), le aggiungiamo
        for col in target_columns:
            if col not in df_grouped.columns:
                df_grouped[col] = 0

        # Riordina le colonne
        df_final = df_grouped[target_columns]

        # Crea il nome del file di output
        filename_root, filename_ext = os.path.splitext(input_file)
        output_file = f"{filename_root}_converted{filename_ext}"

        # Salva
        df_final.to_csv(output_file, index=False)
        print(f"Completato! File salvato come: {output_file}")

    except Exception as e:
        print(f"Si è verificato un errore durante la conversione: {e}")

if __name__ == "__main__":
    # Controlla se è stato passato un argomento da riga di comando
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        # Se non ci sono argomenti, chiedi all'utente
        file_name = input("Inserisci il nome del file CSV da convertire: ").strip()

    # Rimuovi eventuali virgolette se l'utente ha fatto drag-and-drop del file nel terminale
    file_name = file_name.replace('"', '').replace("'", "")

    convert_seed_csv_to_aggregated(file_name)