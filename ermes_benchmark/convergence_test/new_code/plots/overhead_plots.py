from itertools import cycle

import bokeh
import holoviews as hv
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

hv.extension('bokeh')
from typing import Dict, Tuple
from d3blocks import D3Blocks


def plot_stacked_bar_chart(node_map):
    nodes = list(node_map.keys())
    message_types = sorted({alias for sub in node_map.values() for (alias, _) in sub.keys()})

    data = {msg: [] for msg in message_types}
    for node in nodes:
        for msg in message_types:
            total_count = sum(count for (alias, _), count in node_map[node].items() if alias == msg)
            data[msg].append(total_count)

    x = np.arange(len(nodes))
    fig, ax = plt.subplots(figsize=(12, 6))

    bar_width = 0.6
    bottom = np.zeros(len(nodes))
    totals = np.zeros(len(nodes))

    for msg in message_types:
        values = np.array(data[msg])
        bars = ax.bar(x, values, bottom=bottom, label=msg, width=bar_width)

        for i, bar in enumerate(bars):
            if values[i] > 0:
                ax.text(
                    bar.get_x() - 0.05,
                    bottom[i] + values[i] / 2,
                    str(values[i]), ha='right',
                    va='center',
                    fontsize=8,
                    color=bar.get_facecolor()
                )

        bottom += values
        totals += values

    for i, total in enumerate(totals):
        ax.text(
            x[i], bottom[i] + max(totals) * 0.01,
            str(int(total)),
            ha='center', va='bottom',
            fontsize=10, fontweight='bold', color='black'
        )

    ax.set_xlabel('Node (last IP octet)')
    ax.set_ylabel('Message Count')
    ax.set_title('Stacked Bar Chart of Messages per Node')
    ax.set_xticks(x)
    ax.set_xticklabels(nodes, rotation=45, ha='right')
    ax.legend(title='Message Types', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()


NODE_COLOR_PALETTE = 'Category10'
ALIAS_COLOR_PALETTE = 'Category20'

def create_chord_diagram(node_map: Dict[str, Dict[Tuple[str, str], int]], filename: str):
    """
    Crea un Chord Diagram con legenda separata per gli Alias.
    """
    records = []
    for target_node, connections in node_map.items():
        for (alias, source_node), count in connections.items():
            if count > 0:
                records.append({
                    'node': source_node,
                    'node_target': target_node,
                    'source': source_node + "_" + alias,
                    'target': target_node + "_" + alias,
                    'weight': count,
                    'alias': alias
                })

    df_flows = pd.DataFrame(records)

    if df_flows.empty:
        return None

    # --- 2. GENERAZIONE MAPPA COLORI (Il Fix) ---
    # Estraiamo gli alias unici ordinati
    unique_aliases = sorted(df_flows['alias'].unique())
    unique_node = sorted(df_flows['node'].unique())

    # Recuperiamo la lista dei colori esadecimali dalla palette Bokeh
    # Prendiamo la versione con più colori (20) della palette richiesta
    # Se non trovasse la palette, usa una default
    palette_colors = bokeh.palettes.all_palettes.get(ALIAS_COLOR_PALETTE, {}).get(20)
    if not palette_colors:
        palette_colors = bokeh.palettes.Category20[20]  # Fallback sicuro

    palette_colors_nodes = bokeh.palettes.all_palettes.get(NODE_COLOR_PALETTE, {}).get(10)
    if not palette_colors_nodes:
        palette_colors_nodes = bokeh.palettes.Category10[10]  # Fallback sicuro

    # Creiamo il dizionario { 'AliasA': '#1f77b4', 'AliasB': '#aec7e8', ... }
    # Usiamo cycle() nel caso ci siano più di 20 alias (i colori ricominceranno)
    color_cycle = cycle(palette_colors)
    alias_color_map = {alias: next(color_cycle) for alias in unique_aliases}

    color_cycle_nodes = cycle(palette_colors_nodes)
    nodes_color_map = {node: next(color_cycle_nodes) for node in unique_node}

    df_flows['color'] = df_flows['alias'].map(alias_color_map)

    df_flows.replace(" ", "_", regex=True, inplace=True)
    print(df_flows)

    d3 = D3Blocks(chart='Chord', frame=False)
    d3.import_example("energy")
    d3.chord(df_flows, ordering='ascending', filepath=filename + ".html", showfig=False, figsize=[1000,1000], margin=200, fontsize=12)

    for _, row in df_flows.iterrows():
        d3.edge_properties.loc[(d3.edge_properties['source'] == row['source']) & (
                d3.edge_properties['target'] == row['target']), 'color'] = row['color']
        d3.edge_properties.loc[(d3.edge_properties['source'] == row['source']) & (
                d3.edge_properties['target'] == row['target']), 'opacity'] = 0.9
        d3.node_properties.get(row['source'])['color'] = nodes_color_map[row['node']]
        d3.node_properties.get(row['target'])['color'] = nodes_color_map[row['node_target']]
    d3.show()
