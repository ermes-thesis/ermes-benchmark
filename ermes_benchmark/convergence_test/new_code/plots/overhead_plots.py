from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import holoviews as hv
from holoviews import opts, dim
hv.extension('bokeh')
import itertools
from itertools import cycle
import bokeh.palettes
from bokeh.palettes import Category20
from typing import Dict, Tuple, Any


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
def create_chord_diagram(node_map: Dict[str, Dict[Tuple[str, str], int]]):
    """
    Crea un Chord Diagram con legenda separata per gli Alias.
    """
    records = []
    for source_node, connections in node_map.items():
        for (alias, target_node), count in connections.items():
            if count > 0:
                records.append({
                    'source': source_node,
                    'target': target_node,
                    'value': count,
                    'alias': alias
                })

    df_flows = pd.DataFrame(records)

    if df_flows.empty:
        return None
    
    all_nodes = pd.Series(df_flows['source'].tolist() + df_flows['target'].tolist()).unique()
    df_nodes = pd.DataFrame({'name': all_nodes})
    nodes = hv.Dataset(df_nodes, kdims=['name'])

    # --- 2. GENERAZIONE MAPPA COLORI (Il Fix) ---
    # Estraiamo gli alias unici ordinati
    unique_aliases = sorted(df_flows['alias'].unique())
    
    # Recuperiamo la lista dei colori esadecimali dalla palette Bokeh
    # Prendiamo la versione con più colori (20) della palette richiesta
    # Se non trovasse la palette, usa una default
    palette_colors = bokeh.palettes.all_palettes.get(ALIAS_COLOR_PALETTE, {}).get(20)
    if not palette_colors:
        palette_colors = bokeh.palettes.Category20[20] # Fallback sicuro
        
    # Creiamo il dizionario { 'AliasA': '#1f77b4', 'AliasB': '#aec7e8', ... }
    # Usiamo cycle() nel caso ci siano più di 20 alias (i colori ricominceranno)
    color_cycle = cycle(palette_colors)
    alias_color_map = {alias: next(color_cycle) for alias in unique_aliases}

    # --- 3. Chord Diagram ---
    chord = hv.Chord((df_flows, nodes), kdims=['source', 'target'], vdims=['value', 'alias'])
    CHORD_SIZE = 800
    
    chord.opts(
        opts.Chord(
            #title="Diagramma di Flusso: Flussi per Alias",
            frame_width=CHORD_SIZE, 
            frame_height=CHORD_SIZE,
            data_aspect=1, 
            
            node_color=dim('name').str(), 
            node_cmap=NODE_COLOR_PALETTE,
            node_line_width=1.5,
            labels='name',
            
            edge_color=dim('alias').str(),
            # --- MODIFICA QUI: Usiamo il dizionario invece della stringa ---
            edge_cmap=alias_color_map, 
            # --------------------------------------------------------------
            edge_line_alpha=0.6,
            show_legend=False 
        )
    )

    # --- 4. Legenda Proxy ---
    dummy_data = pd.DataFrame({'x': [0]*len(unique_aliases), 'y': [0]*len(unique_aliases), 'alias': unique_aliases})
    
    legend_proxy = hv.Points(dummy_data, kdims=['x', 'y'], vdims=['alias']).opts(
        color='alias',
        # --- MODIFICA QUI: Usiamo lo STESSO dizionario ---
        cmap=alias_color_map,
        # -------------------------------------------------
        size=0, 
        show_legend=True,
        legend_position='top_right',
        xaxis=None, yaxis=None, show_frame=False, title=""
    )
    
    return chord * legend_proxy