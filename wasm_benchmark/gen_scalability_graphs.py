import numpy as np
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

    # Filtri opzionali
    df = df[df['concurrency'] <= 70]
    df = df[df['pool_size'] <= 64]

    if df.empty:
        return df

    # Rinomina Workloads per leggibilità
    df['workload'] = df['workload'].replace("Lightweight", "SimpleLoop")
    custom_workload_order = ["SimpleLoop", "PrimeNumbers", "Stateful"]

    if 'workload' in df.columns:
        existing_workloads = set(df['workload'].unique())
        for w in existing_workloads:
            if w not in custom_workload_order:
                custom_workload_order.append(w)

        df['workload'] = pd.Categorical(
            df['workload'],
            categories=custom_workload_order,
            ordered=True
        )

    # Normalizza nomi Runtime
    df['runtime'] = df['runtime'].replace("Wasmedge", "Wasmedge_AOT").replace("Wazero", "Wazero_AOT")

    custom_runtime_order = ["Wasmtime_JIT", "Wasmtime_AOT", "Wasmedge_AOT", "Wazero_AOT"]

    if 'runtime' in df.columns:
        existing_runtime = set(df['runtime'].unique())
        for w in existing_runtime:
            if w not in custom_runtime_order:
                custom_runtime_order.append(w)

        df['runtime'] = pd.Categorical(
            df['runtime'],
            categories=custom_runtime_order,
            ordered=True
        )

    # Conversione PoolSize in stringa categorica ordinata
    if 'pool_size' in df.columns:
        unique_sizes = sorted(df['pool_size'].astype(int).unique())
        pool_order = [str(x) for x in unique_sizes]

        df['Pool Size'] = pd.Categorical(
            df['pool_size'].astype(str),
            categories=pool_order,
            ordered=True
        )
        df.sort_values(by=['Pool Size'], inplace=True)

    return df

def move_legend_to_top(g):
    """Sposta la legenda di un FacetGrid in alto al centro."""
    if g._legend:
        g._legend.remove()

    handles, labels = g.axes.flat[0].get_legend_handles_labels()

    if not handles:
        return

    num_cols = min(len(labels), 8)
    g.fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 1),
                 ncol=num_cols, frameon=False, title="Pool Size")

def move_legend_to_right(g):
    """Sposta la legenda di un FacetGrid a destra."""
    if g._legend:
        g._legend.remove()

    handles, labels = g.axes.flat[0].get_legend_handles_labels()

    if not handles:
        return

    # Posiziona la legenda a destra esternamente ai grafici
    g.fig.legend(handles, labels, loc='center left', bbox_to_anchor=(1, 0.5),
                 ncol=1, frameon=False, title="Pool Size")

    # Aggiusta il layout per far spazio alla legenda sulla destra
    # g.fig.subplots_adjust(right=0.85)


def plot_smart_markers(data, x, y, markers, palette, **kwargs):
    """
    Piazza i marker sulla linea media aggregata.
    """
    indices_to_keep = []

    agg_data = data.groupby(['Pool Size', x], observed=True)[y].mean().reset_index()

    for group_name, group_data in agg_data.groupby("Pool Size", observed=True):
        if group_data.empty: continue

        x_targets = np.linspace(group_data[x].min(), group_data[x].max(), 4)

        for val in x_targets:
            idx = (np.abs(group_data[x] - val)).argmin()
            indices_to_keep.append(group_data.iloc[idx])

    if not indices_to_keep:
        return

    subset = pd.DataFrame(indices_to_keep)

    sns.scatterplot(
        data=subset, x=x, y=y,
        hue="Pool Size", style="Pool Size",
        palette=palette,
        zorder=10, legend=False,
        markers=markers
    )

def plot_scalability_matrix(df, file_ext=".png"):
    """
    Genera una matrice completa.
    """
    markers_list = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    num_pool_sizes = len(df['Pool Size'].unique())
    print(f"Number of pool sizes: {num_pool_sizes}")
    current_markers = markers_list[:num_pool_sizes] if num_pool_sizes <= len(markers_list) else True

    # --- 1. RPS Matrix ---
    print("Generating Scalability Matrix (RPS)...")
    rps_palette = "viridis"

    g1 = sns.relplot(
        data=df,
        x="concurrency", y="rps",
        hue="Pool Size", style="Pool Size",
        row="runtime", col="workload",
        kind="line",
        dashes=False,
        height=3.5, aspect=1.3,
        palette=rps_palette,
        linewidth=2,
        facet_kws={'sharey': 'col', 'sharex': True},
        markers=current_markers,
        markevery=-1,
    )

    g1.map_dataframe(plot_smart_markers, x="concurrency", y="rps", markers=current_markers, palette=rps_palette)
    g1.set_titles("{row_name} | {col_name}")
    g1.set_axis_labels("Users", "RPS")

    move_legend_to_top(g1)

    filename = f"scalability_rps_matrix_independent{file_ext}"
    g1.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")

    # --- 2. Latency Matrix ---
    print("Generating Scalability Matrix (Latency)...")
    latency_palette = "rocket_r"

    g2 = sns.relplot(
        data=df,
        x="concurrency", y="avg_latency_ms",
        hue="Pool Size", style="Pool Size",
        row="runtime", col="workload",
        kind="line",
        dashes=False,
        height=3.5, aspect=1.3,
        palette=latency_palette,
        linewidth=2,
        facet_kws={'sharey': 'col', 'sharex': True},
        markers=current_markers,
        markevery=-1,
    )

    g2.map_dataframe(plot_smart_markers, x="concurrency", y="avg_latency_ms", markers=current_markers, palette=latency_palette)
    g2.set_titles("{row_name} | {col_name}")
    g2.set_axis_labels("Users", "Latency (ms)")

    move_legend_to_top(g2)

    filename = f"scalability_latency_matrix_independent{file_ext}"
    g2.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")


def plot_scalability_by_runtime_row(df, file_ext=".png"):
    """
    Genera grafici divisi per runtime (righe) con i workload sulle colonne
    e la legenda posizionata a destra. Scale indipendenti per i singoli grafici.
    """
    markers_list = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    num_pool_sizes = len(df['Pool Size'].unique())
    current_markers = markers_list[:num_pool_sizes] if num_pool_sizes <= len(markers_list) else True

    runtimes = df['runtime'].unique()
    rps_palette = "viridis"
    latency_palette = "rocket_r"

    for rt in runtimes:
        print(f"Generating Row Charts for Runtime: {rt}...")
        df_rt = df[df['runtime'] == rt]

        # --- 1. RPS Row Chart ---
        g1 = sns.relplot(
            data=df_rt,
            x="concurrency", y="rps",
            hue="Pool Size", style="Pool Size",
            col="workload",
            kind="line",
            dashes=False,
            height=3.5, aspect=1.3,
            palette=rps_palette,
            linewidth=2,
            facet_kws={'sharey': False, 'sharex': True}, # Modificato da True a False
            markers=current_markers,
            markevery=-1,
        )

        g1.map_dataframe(plot_smart_markers, x="concurrency", y="rps", markers=current_markers, palette=rps_palette)
        g1.set_titles(f"{rt} | {{col_name}}")
        g1.set_axis_labels("Users", "RPS")

        move_legend_to_right(g1)

        filename = f"scalability_rps_row_{rt}{file_ext}"
        g1.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Saved: {filename}")

        # --- 2. Latency Row Chart ---
        g2 = sns.relplot(
            data=df_rt,
            x="concurrency", y="avg_latency_ms",
            hue="Pool Size", style="Pool Size",
            col="workload",
            kind="line",
            dashes=False,
            height=3.5, aspect=1.3,
            palette=latency_palette,
            linewidth=2,
            facet_kws={'sharey': False, 'sharex': True}, # Modificato da True a False
            markers=current_markers,
            markevery=-1,
        )

        g2.map_dataframe(plot_smart_markers, x="concurrency", y="avg_latency_ms", markers=current_markers, palette=latency_palette)
        g2.set_titles(f"{rt} | {{col_name}}")
        g2.set_axis_labels("Users", "Latency (ms)")

        move_legend_to_right(g2)

        filename = f"scalability_latency_row_{rt}{file_ext}"
        g2.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Saved: {filename}")


def plot_compact_scalability(df, file_ext=".png"):
    """
    Grafici compatti.
    """
    markers_list = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    num_pool_sizes = len(df['Pool Size'].unique())
    current_markers = markers_list[:num_pool_sizes] if num_pool_sizes <= len(markers_list) else True

    # --- 1. RPS Compact Chart ---
    print("Generating Compact RPS Chart...")
    g1 = sns.relplot(
        data=df,
        x="concurrency", y="rps",
        col="workload",
        hue="runtime",
        style="Pool Size",
        kind="line",
        markers=current_markers, dashes=False,
        height=5, aspect=1.2,
        palette="bright",
        linewidth=2.5,
        facet_kws={'sharey': 'col', 'sharex': True}
    )

    g1.set_titles("{col_name}")
    g1.set_axis_labels("Concurrent Users", "Throughput (RPS)")
    g1.fig.suptitle("Scalability Comparison", y=1.02, fontsize=16)

    filename = f"scalability_rps_compact{file_ext}"
    g1.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")

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
        facet_kws={'sharey': 'col', 'sharex': True}
    )

    g2.set_titles("{col_name}")
    g2.set_axis_labels("Concurrent Users", "Avg Latency (ms)")
    g2.fig.suptitle("Scalability Latency", y=1.02, fontsize=16)

    filename = f"scalability_latency_compact{file_ext}"
    g2.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")


def plot_by_runtime(df, file_ext=".png"):
    """
    Grafici separati per ogni RUNTIME.
    """
    markers_list = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    num_pool_sizes = len(df['Pool Size'].unique())
    current_markers = markers_list[:num_pool_sizes] if num_pool_sizes <= len(markers_list) else True

    runtimes = df['runtime'].unique()

    for rt in runtimes:
        print(f"Generating charts for Runtime: {rt}...")
        df_rt = df[df['runtime'] == rt]

        # --- 1. RPS Chart ---
        plt.figure(figsize=(10, 6))
        sns.lineplot(
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

        filename = f"scalability_rps_{rt}{file_ext}"
        plt.savefig(filename, dpi=300)
        plt.close()

        # --- 2. Latency Chart ---
        plt.figure(figsize=(10, 6))
        sns.lineplot(
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

        filename = f"scalability_latency_{rt}{file_ext}"
        plt.savefig(filename, dpi=300)
        plt.close()

    print(f"Generated individual charts for runtimes: {runtimes}")


if __name__ == "__main__":
    args = sys.argv[1:]

    # Gestione flag --pdf
    file_ext = ".png"
    if "--pdf" in args:
        file_ext = ".pdf"
        args.remove("--pdf")
        print("Output format set to PDF.")

    target_file = args[0] if args else "scalability_results.json"

    print(f"--- Processing {target_file} ---")
    df = load_data(target_file)

    if df.empty:
        print("Dataset vuoto.")
        sys.exit(1)

    print(f"Loaded {len(df)} records.")

    if 'repetition' in df.columns:
        rep_count = df['repetition'].max()
        print(f"Repetitions detected: {rep_count} per configuration.")

    print(f"Runtimes found: {df['runtime'].unique()}")
    print(f"Workloads found: {df['workload'].unique()}")

    # 1. Matrice Completa (RPS: viridis, Latency: rocket_r)
    plot_scalability_matrix(df, file_ext)

    # 2. Esporta le immagini per singolo runtime in formato "riga" con legenda a destra (e scale indipendenti)
    plot_scalability_by_runtime_row(df, file_ext)

    print("\nDone.")