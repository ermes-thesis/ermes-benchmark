import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import sys

# Setup grafico
sns.set_theme(style="whitegrid", font_scale=1.2)

def load_data(filename="scalability_results.json"):
    data = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    except FileNotFoundError:
        print(f"Errore: File {filename} non trovato. Esegui prima il test Go.")
        sys.exit(1)
    return pd.DataFrame(data)

def plot_scalability(df):
    # Se nel dataframe c'è la colonna 'pool_size', usala per differenziare (hue o style)
    # Altrimenti usa solo workload

    has_pool_size = 'pool_size' in df.columns

    # Creiamo una figura con 2 subplot (RPS e Latency)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Parametri per il plotting
    hue_col = "workload"
    style_col = "pool_size" if has_pool_size else None

    # --- Plot 1: Throughput (RPS) ---
    sns.lineplot(
        data=df,
        x="concurrency",
        y="rps",
        hue=hue_col,
        style=style_col, # Linee diverse per pool_size diverse se presenti
        markers=True,
        dashes=False,
        linewidth=2.5,
        ax=ax1
    )
    ax1.set_title("System Throughput (Scalability)")
    ax1.set_xlabel("Concurrent Users (Goroutines)")
    ax1.set_ylabel("Requests Per Second (RPS)")
    ax1.grid(True, linestyle='--', alpha=0.7)

    # --- Plot 2: Average Latency ---
    sns.lineplot(
        data=df,
        x="concurrency",
        y="avg_latency_ms",
        hue=hue_col,
        style=style_col,
        markers=True,
        dashes=False,
        linewidth=2.5,
        ax=ax2
    )
    ax2.set_title("Average Request Latency")
    ax2.set_xlabel("Concurrent Users (Goroutines)")
    ax2.set_ylabel("Latency (ms)")
    ax2.grid(True, linestyle='--', alpha=0.7)

    # Aggiungi una linea orizzontale di riferimento se sappiamo la pool size fissa (es. 20)
    # Questo aiuta a vedere visivamente quando la concorrenza supera la pool size
    # ax1.axvline(x=20, color='red', linestyle='--', alpha=0.5, label='Pool Saturation (Size=20)')
    # ax2.axvline(x=20, color='red', linestyle='--', alpha=0.5, label='Pool Saturation (Size=20)')

    # Salva
    plt.tight_layout()
    plt.savefig("scalability_chart.png", dpi=300)
    print("Grafico generato: scalability_chart.png")

if __name__ == "__main__":
    print("Generazione grafici di scalabilità...")
    df = load_data()
    print(df.head())
    plot_scalability(df)