import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import sys
import os

# Setup grafico globale
sns.set_theme(style="whitegrid", font_scale=1.1)

def load_data(filename="scalability_results.json"):
    """Carica i dati JSON-lines generati dal test Go."""
    data = []
    if not os.path.exists(filename):
        print(f"Errore: File {filename} non trovato. Esegui prima il test Go.")
        sys.exit(1)

    with open(filename, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Skipping invalid line: {e}")

    df = pd.DataFrame(data)

    # Conversione PoolSize in stringa categorica ordinata per visualizzazione pulita
    if 'pool_size' in df.columns:
        # Troviamo i valori unici e li ordiniamo numericamente
        unique_sizes = sorted(df['pool_size'].astype(int).unique())
        pool_order = [str(x) for x in unique_sizes]

        # Creiamo la colonna 'Pool Size' come Categorical con ordine forzato
        df['Pool Size'] = pd.Categorical(
            df['pool_size'].astype(str),
            categories=pool_order,
            ordered=True
        )

        # Ordiniamo il dataframe in base a questo ordine logico
        df.sort_values(by=['Pool Size'], inplace=True)

    return df

def plot_scalability_matrix(df):
    """
    Genera una matrice completa (Runtime x Workload) con SCALE INDIPENDENTI.
    Questo permette di vedere la forma della curva anche per runtime più lenti,
    senza che vengano 'schiacciati' dalla scala di quelli più veloci.
    """

    # Definiamo marker espliciti
    markers_list = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    num_pool_sizes = len(df['Pool Size'].unique())
    current_markers = markers_list[:num_pool_sizes] if num_pool_sizes <= len(markers_list) else True

    # --- 1. RPS Matrix (Independent Scales) ---
    print("Generating Scalability Matrix (RPS) - Independent Scales...")
    g1 = sns.relplot(
        data=df,
        x="concurrency", y="rps",
        hue="Pool Size", style="Pool Size",
        row="runtime", col="workload",
        kind="line",
        markers=current_markers, dashes=False,
        height=3.5, aspect=1.3,
        palette="viridis",
        linewidth=2,
        # CRUCIALE: sharey=False permette a ogni grafico di avere la sua scala Y
        facet_kws={'sharey': False, 'sharex': True}
    )

    g1.set_titles("{row_name} | {col_name}")
    g1.set_axis_labels("Users", "RPS")
    g1.fig.suptitle("Scalability Matrix: RPS (Independent Scales)", y=1.02, fontsize=16)
    g1.savefig("scalability_rps_matrix_independent.png", dpi=300, bbox_inches='tight')
    print("Saved: scalability_rps_matrix_independent.png")

    # --- 2. Latency Matrix (Independent Scales) ---
    print("Generating Scalability Matrix (Latency) - Independent Scales...")
    g2 = sns.relplot(
        data=df,
        x="concurrency", y="avg_latency_ms",
        hue="Pool Size", style="Pool Size",
        row="runtime", col="workload",
        kind="line",
        markers=current_markers, dashes=False,
        height=3.5, aspect=1.3,
        palette="rocket_r",
        linewidth=2,
        # CRUCIALE: sharey=False
        facet_kws={'sharey': False, 'sharex': True}
    )

    g2.set_titles("{row_name} | {col_name}")
    g2.set_axis_labels("Users", "Latency (ms)")
    g2.fig.suptitle("Scalability Matrix: Latency (Independent Scales)", y=1.02, fontsize=16)
    g2.savefig("scalability_latency_matrix_independent.png", dpi=300, bbox_inches='tight')
    print("Saved: scalability_latency_matrix_independent.png")

def plot_compact_scalability(df):
    """
    Genera grafici compatti:
    - Colonne: Workload (Lightweight, Prime, etc.)
    - Colore (Hue): Runtime (Wasmtime, Wazero...) -> Confronto diretto
    - Stile (Marker): Pool Size -> Impatto risorse
    """

    # Definiamo marker espliciti per le Pool Size
    markers_list = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    num_pool_sizes = len(df['Pool Size'].unique())
    current_markers = markers_list[:num_pool_sizes] if num_pool_sizes <= len(markers_list) else True

    # --- 1. RPS Compact Chart ---
    print("Generating Compact RPS Chart...")
    g1 = sns.relplot(
        data=df,
        x="concurrency", y="rps",
        col="workload",          # Una colonna per Workload
        hue="runtime",           # Colore diverso per Runtime (CONFRONTO DIRETTO)
        style="Pool Size",       # Stile diverso per Pool Size
        kind="line",
        markers=current_markers, dashes=False,
        height=5, aspect=1.2,
        palette="bright",        # Palette brillante per distinguere bene i runtime
        linewidth=2.5,
        facet_kws={'sharey': False, 'sharex': True} # Scala Y indipendente per workload diversi
    )

    g1.set_titles("{col_name}")
    g1.set_axis_labels("Concurrent Users", "Throughput (RPS)")
    g1.fig.suptitle("Scalability Comparison: Runtime Efficiency & Pool Sizing", y=1.02, fontsize=16)

    g1.savefig("scalability_rps_compact.png", dpi=300, bbox_inches='tight')
    print("Saved: scalability_rps_compact.png")

    # --- 2. Latency Compact Chart ---
    print("Generating Compact Latency Chart...")
    g2 = sns.relplot(
        data=df,
        x="concurrency", y="avg_latency_ms",
        col="workload",
        hue="runtime",
        style="Pool Size",
        kind="line",
        markers=current_markers, dashes=False,
        height=5, aspect=1.2,
        palette="bright",
        linewidth=2.5,
        facet_kws={'sharey': False, 'sharex': True}
    )

    g2.set_titles("{col_name}")
    g2.set_axis_labels("Concurrent Users", "Avg Latency (ms)")
    # g2.set(yscale="log") # Scommenta se necessario
    g2.fig.suptitle("Scalability Latency: Runtime Stability under Load", y=1.02, fontsize=16)

    g2.savefig("scalability_latency_compact.png", dpi=300, bbox_inches='tight')
    print("Saved: scalability_latency_compact.png")

def plot_by_runtime(df):
    """
    Genera grafici separati per ogni RUNTIME:
    - Asse X: Concorrenza
    - Asse Y: RPS / Latency
    - Colore (Hue): Workload (Funzioni diverse)
    - Stile: Pool Size
    """

    # Definiamo marker espliciti
    markers_list = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    num_pool_sizes = len(df['Pool Size'].unique())
    current_markers = markers_list[:num_pool_sizes] if num_pool_sizes <= len(markers_list) else True

    # Iteriamo su ogni Runtime presente nel dataset
    runtimes = df['runtime'].unique()

    for rt in runtimes:
        print(f"Generating charts for Runtime: {rt}...")
        df_rt = df[df['runtime'] == rt]

        # --- 1. RPS Chart per questo Runtime ---
        # Usiamo relplot con col="workload" per separare le funzioni, ma tutto nello stesso file
        # Oppure un singolo plot con hue="workload".
        # Qui facciamo un singolo plot con hue="workload" per vedere tutto insieme

        plt.figure(figsize=(10, 6))
        g1 = sns.lineplot(
            data=df_rt,
            x="concurrency", y="rps",
            hue="workload",
            style="Pool Size",
            markers=current_markers, dashes=False,
            palette="viridis",
            linewidth=2.5
        )
        plt.title(f"Throughput (RPS) - Runtime: {rt}")
        plt.ylabel("RPS")
        plt.xlabel("Concurrent Users")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f"scalability_rps_{rt}.png", dpi=300)
        plt.close()

        # --- 2. Latency Chart per questo Runtime ---
        plt.figure(figsize=(10, 6))
        g2 = sns.lineplot(
            data=df_rt,
            x="concurrency", y="avg_latency_ms",
            hue="workload",
            style="Pool Size",
            markers=current_markers, dashes=False,
            palette="rocket",
            linewidth=2.5
        )
        plt.title(f"Latency - Runtime: {rt}")
        plt.ylabel("Avg Latency (ms)")
        plt.xlabel("Concurrent Users")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f"scalability_latency_{rt}.png", dpi=300)
        plt.close()

    print(f"Generated individual charts for runtimes: {runtimes}")

if __name__ == "__main__":
    target_file = "scalability_results.json"
    if len(sys.argv) > 1:
        target_file = sys.argv[1]

    print(f"--- Processing {target_file} ---")
    df = load_data(target_file)

    if df.empty:
        print("Dataset vuoto.")
        sys.exit(1)

    print(f"Loaded {len(df)} records.")
    print(f"Runtimes found: {df['runtime'].unique()}")
    print(f"Workloads found: {df['workload'].unique()}")

    # 1. Matrice Completa (RPS e Latency) con scale INDIPENDENTI (Quello che hai chiesto)
    plot_scalability_matrix(df)

    # 2. Grafici Compatti (Confronto diretto Runtime)
    plot_compact_scalability(df)

    # 3. Grafici per Runtime (Dettaglio singolo)
    plot_by_runtime(df)

    print("\nDone.")