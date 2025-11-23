import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import itertools
from collections import defaultdict

def compute_path(tree: dict, start_node: int, end_node: int) -> list[int]:
    G = nx.Graph()  # undirected graph
    for parent, children in tree.items():
        for child in children:
            G.add_edge(parent, child)

    try:
        path = nx.shortest_path(G, source=start_node, target=end_node)
        return path
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []

def plot_tree_with_sparklines(tree: dict, dfs: list[pd.DataFrame], normalization: int):

    # --- 1. Pre-elaborazione Dati per Sparklines ---
    try:
        df_combined = pd.concat(dfs, ignore_index=True)
    except ValueError:
        print("Errore: La lista di DataFrame è vuota o non è valida.")
        return

    try:
        # Pulisci host e converti in interi
        df_combined['Node_Exec'] = df_combined['ExecHost'].str.split('.').str[-1].str.split(':').str[0].astype(int)
        df_combined['Node_Entry'] = df_combined['EntryHost'].str.split('.').str[-1].str.split(':').str[0].astype(int)
    except Exception as e:
        print(f"Errore nella pulizia degli host: assicurati che siano presenti etichette numeriche. {e}")
        return
        
    all_nodes = df_combined['ExecHost'].str.split('.').str[-1].str.split(':').str[0].astype(int).unique()
    all_groups = df_combined['Group'].unique()

    all_combinations = pd.DataFrame(
        list(itertools.product(all_nodes, all_groups)),
        columns=['Node', 'Group']
    )
    all_combinations['TaskCount'] = 0
    all_combinations['indirectLoad'] = 0

    task_counts_real = df_combined.groupby(['ExecHost', 'Group']).size().reset_index(name='TaskCount')
    # Pulisci Node come prima
    task_counts_real['Node'] = task_counts_real['ExecHost'].str.split('.').str[-1].str.split(':').str[0].astype(int)

    # Merge lasciando tutte le combinazioni possibili
    task_counts = all_combinations.merge(
        task_counts_real[['Node', 'Group', 'TaskCount']],
        on=['Node', 'Group'],
        how='left',
        suffixes=('_filled', '')
    )

    # Riempie i valori mancanti con 0
    task_counts['TaskCount'] = task_counts['TaskCount'].fillna(0).astype(int)
    task_counts['TaskCount'] = task_counts['TaskCount'] / normalization # Normalizzazione
    
    paths = defaultdict(list)   
    
    # Calcola i percorsi unici tra nodi di Entry e nodi di Exec
    for _, row in df_combined.iterrows():
        entry_node = row['Node_Entry']
        exec_node = row['Node_Exec']
        short_exec_host = int(row['ExecHost'].split('.')[-1].split(':')[0])
        group = row['Group']

        if exec_node == entry_node:
            continue

        if (entry_node, exec_node) not in paths:
            paths[(entry_node,exec_node)]= compute_path(tree, entry_node, exec_node)

        path = paths[(entry_node,exec_node)]
        for node in path:
            if node == short_exec_host:
                continue
            mask = (task_counts['Node'] == node) & (task_counts['Group'] == group)
            task_counts.loc[mask, 'indirectLoad'] = task_counts.loc[mask, 'indirectLoad'] + 1

    task_counts['indirectLoad'] = task_counts['indirectLoad'] / normalization # Normalizzazione

    sparkline_data = task_counts.pivot_table(
        index='Node',
        columns='Group',
        values='TaskCount',
        fill_value=0
    )

    sparkline_data = sparkline_data.reindex(sorted(sparkline_data.columns), axis=1)
    max_count = sparkline_data.values.max()
    if max_count == 0:
        max_count = 1 
    
    # --- 2. Creazione del Grafo e Posizionamento ---
    
    G = nx.DiGraph()
    for parent, children in tree.items():
        for child in children:
            G.add_edge(parent, child)

    # *** MODIFICA PER LAYOUT GERARCHICO ***
    try:
        import pydot
        pos = nx.nx_pydot.graphviz_layout(G, prog='dot')
        print("Layout Graphviz ('dot') applicato con successo.")
    except ImportError:
        print("Avviso: 'pydot' o Graphviz non installati. Fallback a 'spring_layout' con inversione asse Y.")
        pos = nx.spring_layout(G, seed=42)
        pos = {node: (x, -y) for node, (x, y) in pos.items()}
    except Exception as e:
        print(f"Avviso: Errore nell'esecuzione di Graphviz: {e}. Fallback a 'spring_layout' con inversione asse Y.")
        pos = nx.spring_layout(G, seed=42)
        pos = {node: (x, -y) for node, (x, y) in pos.items()}

    # --- 3. Disegno del Grafico e delle Sparklines ---
    
    fig_scale = 1.3
    num_nodes = G.number_of_nodes()
    
    fig_width = max(14, num_nodes * 0.4 * fig_scale)
    fig_height = max(6, num_nodes * 0.7 * fig_scale)
    fig_size = (fig_width, fig_height)
    
    fig = plt.figure(figsize=fig_size) 
    plt.subplots_adjust(wspace=3) #spazio tra subplots
    ax = plt.gca()
    ax.set_axis_off() 

    # 3.1 Disegna gli archi
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='gray', width=1, alpha=0.3)
    
    num_groups = len(sparkline_data.columns)
    x_group_indices = np.arange(num_groups)

    x_label = "Time (Round)"
    y_label = "N. Req per experiment"
    
    for node in G.nodes():

        # --- TaskCount verde ---
        if node in sparkline_data.index:
            counts = sparkline_data.loc[node].values
            # Se counts ha meno valori di num_groups, padding con 0
            if len(counts) < num_groups:
                counts = np.pad(counts, (0, num_groups - len(counts)), 'constant')
            max_tasks_in_round = counts.max()
        else:
            counts = np.zeros(num_groups, dtype=int)
            max_tasks_in_round = 0

        # --- indirectLoad azzurro ---
        node_task_rows = task_counts[task_counts['Node'] == node].sort_values('Group')
        if not node_task_rows.empty:
            indirect_counts = node_task_rows['indirectLoad'].values
            if len(indirect_counts) < num_groups:
                indirect_counts = np.pad(indirect_counts, (0, num_groups - len(indirect_counts)), 'constant')
            max_indirect = indirect_counts.max()
        else:
            indirect_counts = np.zeros(num_groups, dtype=int)
            max_indirect = 0

        x_center, y_center = pos[node]
        spark_ax_width = 0.10 * fig_scale
        spark_ax_height = 0.08 * fig_scale

        fig.canvas.draw()
        x_norm, y_norm = ax.transData.transform((x_center, y_center))
        bbox = fig.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        fig_width_pix, fig_height_pix = bbox.width * fig.dpi, bbox.height * fig.dpi
        x_norm_fig = x_norm / fig_width_pix
        y_norm_fig = y_norm / fig_height_pix

        spark_ax = fig.add_axes([
            x_norm_fig - spark_ax_width / 2,
            y_norm_fig - spark_ax_height / 2,
            spark_ax_width,
            spark_ax_height
        ], frameon=True, zorder=3, facecolor='white')

        # Plot TaskCount verde
        spark_ax.plot(x_group_indices, counts, color='#4CAF50', linewidth=1.5)
        spark_ax.fill_between(x_group_indices, counts, color='#4CAF50', alpha=0.3)

        # Plot indirectLoad azzurro
        spark_ax.plot(x_group_indices, indirect_counts, color='#03A9F4', linewidth=1.5)
        spark_ax.fill_between(x_group_indices, indirect_counts, color='#03A9F4', alpha=0.2)

        # Linee verticali tra round
        for i in range(num_groups - 1):
            spark_ax.axvline(x=i + 0.5, color='gray', linestyle=':', linewidth=0.5, alpha=0.7)

        spark_ax.set_xticks([0, num_groups - 1])
        spark_ax.set_xticklabels([sparkline_data.columns.min(), sparkline_data.columns.max()])
        spark_ax.set_xlabel("Tempo (Round)", fontsize=6 * fig_scale / 1.5, labelpad=2)

        # Y-axis scaling: massimo tra TaskCount e indirectLoad
        local_max = max(max_tasks_in_round, max_indirect, 1)
        spark_ax.set_yticks([0, local_max])
        spark_ax.set_yticklabels([0, local_max])
        spark_ax.set_ylabel("N. Req", fontsize=6 * fig_scale / 1.5, rotation=90, labelpad=2)

        spark_ax.spines['top'].set_visible(False)
        spark_ax.spines['right'].set_visible(False)
        spark_ax.spines['left'].set_linewidth(0.5)
        spark_ax.spines['bottom'].set_linewidth(0.5)
        spark_ax.tick_params(axis='both', which='major', labelsize=6 * fig_scale / 1.5, pad=1)

        spark_ax.set_ylim(0, local_max * 1.05)
        spark_ax.set_xlim(-0.5, num_groups - 0.5)

        # Etichetta nodo
        spark_ax.text(
            0.5, 1.25,
            str(node),
            transform=spark_ax.transAxes,
            ha='center', va='center',
            fontsize=12 * fig_scale / 1.5,
            fontweight='bold',
            color='black'
        )

        # Etichetta Max TaskCount / indirectLoad
        spark_ax.text(
            0.5, -0.65,
            f"Max: {max_tasks_in_round} / {max_indirect} (req/round)",
            transform=spark_ax.transAxes,
            ha='center', va='center',
            fontsize=8 * fig_scale / 1.5,
            color='darkred',
            fontweight='bold'
        )

    return fig
