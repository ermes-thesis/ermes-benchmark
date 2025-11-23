import inspect
import itertools
import os
import re
import shutil
import sys
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import pytz  # pydot
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

relative_files = [
    '../data/full_traversal.zip',
    '../data/full_traversal.zip',
]

out_dir = 'full_traversal_analysis'

log_search_key = 'DEFAULT-STRONG-POLICY, transition to idle state'  # 'DEFAULT-STRONG-POLICY, transition to decision state'

ignored_functions = ['functionCreateCollections', 'functionCreateSeqCollections']
default_address = '10.10.101.'
default_port = ':12345'

eq_map = {
    'functionUseSeqCollections-10.10.101.51:12345': '10.10.101.51:12345',
    'functionReadSeqCollections-10.10.101.54:12345': '10.10.101.54:12345',
}

tree = {
    57: [56, 55],
    56: [52, 53, 54],
    55: [50, 51],
}


def processa_zip_files(zip_path):
    """
    Legge un file ZIP contenente file .csv e .log e restituisce due dizionari.

    Args:
        zip_path (str): Il percorso completo del file ZIP.

    Returns:
        tuple: Una tupla contenente (dati_csv, dati_log).
               - dati_csv (dict): Chiave=nome_file, Valore=pandas.DataFrame.
               - dati_log (dict): Chiave=nome_file, Valore=contenuto_stringa.
    """
    dati_csv = {}
    dati_log = {}

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for filename in zf.namelist():
                if filename.endswith('/') or filename.startswith('__MACOSX'):
                    continue

                nome_base, estensione = os.path.splitext(filename)

                if estensione.lower() == '.csv':
                    with zf.open(filename) as file_obj:
                        try:
                            df = pd.read_csv(file_obj)
                            dati_csv[filename] = df
                        except Exception as e:
                            print(f"Errore nella lettura del CSV {filename}: {e}")

                elif estensione.lower() == '.log':
                    with zf.open(filename, 'r') as file_obj:
                        try:
                            # Assumiamo la codifica UTF-8
                            content = file_obj.read().decode('utf-8')
                            filename = filename.replace('.log', '')
                            filename = filename.split('_')[-1]
                            filename = default_address + filename + default_port
                            dati_log[filename] = content
                        except Exception as e:
                            print(f"Errore nella lettura del LOG {filename}: {e}")

    except FileNotFoundError:
        print(f"Errore: File ZIP non trovato al percorso specificato: {zip_path}")
        return {}, {}
    except zipfile.BadZipFile:
        print(f"Errore: Il file non è un archivio ZIP valido o è corrotto: {zip_path}")
        return {}, {}
    except Exception as e:
        print(f"Si è verificato un errore inatteso: {e}")
        return {}, {}

    return dati_csv, dati_log


def parse_log(dati_log_input):
    """
    Analizza i contenuti dei file di log, cercando una stringa specifica, 'DEFAULT-STRONG-POLICY, transition to decision state'.
    Estrae i timestamp dalle righe che contengono tale stringa.

    Args:
        dati_log_input (dict): Dizionario con Chiave=nome_file, Valore=contenuto_stringa del log.

    Returns:
        dict: Dizionario con Chiave=nome_file, Valore=Lista di timestamp (stringhe).
    """
    timestamp_data = {}

    TIMESTAMP_PATTERN = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)'

    for nome_file, content_log in dati_log_input.items():
        list_timestamp = []

        righe = content_log.splitlines()

        for riga in righe:
            if log_search_key in riga:
                match = re.search(TIMESTAMP_PATTERN, riga)

                if match:
                    timestamp = match.group(1)
                    list_timestamp.append(timestamp)

        timestamp_data[nome_file] = list_timestamp

    return timestamp_data


def parse_dfs(dati_csv: Dict[str, pd.DataFrame], dati_timestamp_per_ip: Dict[str, List[str]]):
    """
    Elabora i DataFrame CSV assegnando a ciascuna riga un gruppo basato sui timestamp di transizione estratti dai log.
    """
    elaborated_dfs = []

    utc = pytz.utc
    ip_windows: Dict[str, List[datetime]] = {}

    for ip, timestamps in dati_timestamp_per_ip.items():
        try:
            sorted_dt = sorted([
                datetime.fromisoformat(ts)
                for ts in timestamps
            ])
            ip_windows[ip] = sorted_dt
        except ValueError as e:
            print(f"Skipping IP {ip}: Errore nel parsing del formato dei timestamp di log. Errore: {e}")
            ip_windows[ip] = []

    for filename, current_df in dati_csv.items():

        if 'ignored_functions' in globals() and ignored_functions:
            current_df = current_df[~current_df['FuncName'].isin(ignored_functions)]

        current_df = current_df.reset_index(drop=True)

        if 'ExecHost' not in current_df.columns or 'StartTime' not in current_df.columns:
            elaborated_dfs[filename] = current_df
            continue

        try:
            current_df['StartTime_dt'] = pd.to_datetime(current_df['StartTime'], format='ISO8601', utc=True)
        except Exception as e:
            print(f"\033[91mError: Skipping {filename}: Errore nel parsing del formato 'StartTime'.\033[0m Errore: {e}")
            elaborated_dfs[filename] = current_df
            continue

        def get_window_group(row):
            exec_host = row['ExecHost']
            start_time = row['StartTime_dt']

            if exec_host not in ip_windows or not ip_windows[exec_host]:
                print(f"\033[91mError: ExecHost {row['ExecHost']} has no defined windows. Assigned to Group -1.\033[0m")
                return -1  # Nessuna finestra definita per questo host

            windows = ip_windows[exec_host]

            # Confronto tra datetimes AWARE in UTC
            for i, window_ts in enumerate(windows):
                if start_time < window_ts:
                    return i

            print(
                f"\033[93mWarning: ExecHost {row['ExecHost']} assigned after last window. {row['StartTime']} - {row['FuncName']} on {row['EntryHost']}\033[0m")
            return len(windows)

        current_df['Group'] = current_df.apply(get_window_group, axis=1)

        current_df['Duration'] = current_df['FuncDuration'].astype(str).str.replace('ms', '').astype(float)
        current_df['StartTime'] = pd.to_datetime(current_df['StartTime'])
        current_df['Is_Local'] = current_df['EntryHost'] == current_df['ExecHost']
        current_df = current_df.drop(columns=['StartTime_dt'])

        current_df = current_df.sort_values(by=['Group', 'StartTime']).reset_index(drop=True)

        elaborated_dfs.append(current_df)
    return elaborated_dfs


def find_equilibrium_timestamp(dfs):
    """
    Find the equilibrium timestamp across multiple DataFrames.
    """
    min_timestamps = []
    for df in dfs:
        for index, row in df.iterrows():
            if row['FuncName'] + "-" + row['EntryHost'] in eq_map and row['ExecHost'] == eq_map[
                row['FuncName'] + "-" + row['EntryHost']]:
                min_timestamps.append(row['StartTime'])
                break

    if not min_timestamps:
        for df in dfs:
            df['BeforeEq'] = False
        return dfs, None

    equilibrium_ts = pd.to_datetime(max(min_timestamps))

    group_max_s = set()
    for df in dfs:
        df['StartTime'] = pd.to_datetime(df['StartTime'])

        group_max = df.groupby('Group')['StartTime'].transform('min')
        group_max_s.update(group_max)

        df['BeforeEq'] = group_max <= equilibrium_ts

    return dfs, equilibrium_ts


def local_vs_remote_number_of_executions(dfs):
    """
    Clustered Bar Chart.
    """
    try:
        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(14, 7))

        all_groups = sorted(list(set().union(*[df['Group'].unique() for df in dfs])))
        x = np.arange(len(all_groups))

        n_files = len(dfs)
        total_width = 0.8
        single_bar_width = total_width / (n_files * 2)

        colors = plt.cm.Set1(np.linspace(0, 1, max(n_files, 3)))

        for i, df in enumerate(dfs):
            counts = df.groupby(['Group', 'Is_Local']).size().unstack(fill_value=0)
            counts = counts / len(relative_files)

            if True not in counts.columns: counts[True] = 0
            if False not in counts.columns: counts[False] = 0

            counts = counts.reindex(all_groups, fill_value=0)

            local_vals = counts[True]
            remote_vals = counts[False]

            num_bars_total = n_files * 2
            idx_local = 2 * i
            idx_remote = 2 * i + 1

            pos_local = x + (idx_local - (num_bars_total - 1) / 2) * single_bar_width
            pos_remote = x + (idx_remote - (num_bars_total - 1) / 2) * single_bar_width

            bars_local = ax.bar(pos_local, local_vals, single_bar_width,
                                color=colors[i], edgecolor='black', label=f'File {i + 1} Local')

            for bar in bars_local:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{height}',
                        ha='center', va='bottom', fontsize=9, color='#555555')

            bars_remote = ax.bar(pos_remote, remote_vals, single_bar_width,
                                 color=colors[i], edgecolor='black', hatch='//', alpha=0.7,
                                 label=f'File {i + 1} Remote')

            for bar in bars_remote:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{height}',
                        ha='center', va='bottom', fontsize=9, color='#555555')

        # Estetica
        ax.set_title('Local vs Remote Executions per Round')
        ax.set_xlabel('Round Number')
        ax.set_ylabel('Count')
        ax.set_xticks(x)
        ax.set_xticklabels(all_groups)

        # Aumentiamo il limite Y per far stare le etichette sopra le barre più alte
        ax.set_ylim(top=ax.get_ylim()[1] * 1.05)

        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=n_files, frameon=False)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()

        return fig

    except Exception as e:
        print(f"Errore plotting: {e}")
        import traceback
        traceback.print_exc()
        return None


def local_vs_remote_latency(dfs):
    """
    Custom Latency Plot with Min, Max, and Avg values displayed as text labels.
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.patches import Patch
        from matplotlib.lines import Line2D

        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(12, 7))

        n_files = len(dfs)
        x = np.arange(n_files)
        total_width = 0.8
        single_bar_width = total_width / 1

        colors = plt.cm.Set1(np.linspace(0, 1, max(n_files, 3)))
        file_labels = [f'User {i + 1}' for i in range(n_files)]

        all_durations = []
        data_to_plot = []

        for df in dfs:
            durations = df['Duration'].dropna()
            if not durations.empty:
                all_durations.extend(durations.tolist())

            min_overall = durations.min() if not durations.empty else np.nan
            max_overall = durations.max() if not durations.empty else np.nan
            mean_total = durations.mean() if not durations.empty else np.nan

            local_data = df[df['Is_Local'] == True]['Duration'].dropna()
            mean_local = local_data.mean() if not local_data.empty else np.nan

            remote_data = df[df['Is_Local'] == False]['Duration'].dropna()
            mean_remote = remote_data.mean() if not remote_data.empty else np.nan

            lower_mean = min(mean_local, mean_remote) if not (np.isnan(mean_local) or np.isnan(mean_remote)) else np.nan
            upper_mean = max(mean_local, mean_remote) if not (np.isnan(mean_local) or np.isnan(mean_remote)) else np.nan

            data_to_plot.append({
                'min': min_overall,
                'max': max_overall,
                'mean_total': mean_total,
                'lower_mean': lower_mean,
                'upper_mean': upper_mean
            })

        if all_durations:
            min_all = np.nanmin(all_durations)
            max_all = np.nanmax(all_durations)

            y_min = max(0, min_all * 0.95)
            y_max = max_all * 1.05

            ax.set_ylim(bottom=y_min, top=y_max)

        for i, data in enumerate(data_to_plot):
            current_x = x[i]
            user_color = colors[i]
            bar_width = single_bar_width * 0.8
            stem_line_width = 1.5

            text_x_pos = current_x + bar_width * 0.25

            if not np.isnan(data['min']) and not np.isnan(data['max']):
                min_val = data['min']
                max_val = data['max']
                height_overall = max_val - min_val

                ax.bar(current_x, height_overall, bottom=min_val, width=bar_width,
                       color='grey', alpha=0.15, edgecolor=None, linewidth=0, zorder=0, label='_nolegend_')

            if not np.isnan(data['lower_mean']) and not np.isnan(data['upper_mean']):
                lower_mean = data['lower_mean']
                upper_mean = data['upper_mean']
                height_mean = upper_mean - lower_mean

                # Box
                ax.bar(current_x, height_mean, bottom=lower_mean, width=bar_width * 0.6,
                       color=user_color, alpha=0.5, edgecolor=user_color, linewidth=1, zorder=2, label='_nolegend_')

                # Stelo inferiore (Min al bordo inferiore del box)
                if not np.isnan(data['min']):
                    ax.vlines(current_x, data['min'], lower_mean,
                              colors=[user_color], alpha=0.8, linestyle=':', linewidth=stem_line_width, zorder=1,
                              label='_nolegend_')

                # Stelo superiore (bordo superiore del box al Max)
                if not np.isnan(data['max']):
                    ax.vlines(current_x, upper_mean, data['max'],
                              colors=[user_color], alpha=0.8, linestyle=':', linewidth=stem_line_width, zorder=1,
                              label='_nolegend_')
            elif not np.isnan(data['mean_total']):
                # Stelo inferiore (Min al bordo inferiore del box)
                if not np.isnan(data['min']):
                    ax.vlines(current_x, data['min'], data['mean_total'],
                              colors=[user_color], alpha=0.8, linestyle=':', linewidth=stem_line_width, zorder=1,
                              label='_nolegend_')

                # Stelo superiore (bordo superiore del box al Max)
                if not np.isnan(data['max']):
                    ax.vlines(current_x, data['mean_total'], data['max'],
                              colors=[user_color], alpha=0.8, linestyle=':', linewidth=stem_line_width, zorder=1,
                              label='_nolegend_')

            # 3. Segni Min/Max (i "whiskers") + ETICHETTE MIN E MAX
            if not np.isnan(data['min']):
                ax.hlines(data['min'], current_x - bar_width * 0.2, current_x + bar_width * 0.2,
                          colors=[user_color], linewidth=2, zorder=4, label='_nolegend_')
                # Etichetta Min
                ax.text(text_x_pos, data['min'], f'Min: {data["min"]:.2f}',
                        ha='left', va='center', fontsize=8, color=user_color, weight='bold')

            if not np.isnan(data['max']):
                ax.hlines(data['max'], current_x - bar_width * 0.2, current_x + bar_width * 0.2,
                          colors=[user_color], linewidth=2, zorder=4, label='_nolegend_')
                ax.text(text_x_pos, data['max'], f'Max: {data["max"]:.2f}',
                        ha='left', va='center', fontsize=8, color=user_color, weight='bold')

            # 4. Linea Media Totale + ETICHETTA MEDIA
            if not np.isnan(data['mean_total']):
                ax.hlines(data['mean_total'], current_x - bar_width * 0.4, current_x + bar_width * 0.4,
                          colors=[user_color], linewidth=2, zorder=3, label='_nolegend_')
                ax.text(text_x_pos, data['mean_total'], f'Avg: {data["mean_total"]:.2f}',
                        ha='left', va='center', fontsize=9, color='black', weight='bold',
                        bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='square,pad=0.2'))

        # --- Legenda ---
        legend_elements = [
            Patch(facecolor='grey', alpha=0.15, edgecolor=None, linewidth=0,
                  label=r'Overall Latency Range (Min $\leftrightarrow$ Max)'),
            Line2D([0], [0], color=colors[0], lw=stem_line_width, label='Min/Max Whisker (Stem) (Colore per Utente)'),
            Patch(facecolor=colors[0], alpha=0.5, edgecolor=colors[0],
                  label=r'Mean Range (Local Mean $\leftrightarrow$ Remote Mean)'),
            Line2D([0], [0], color='black', lw=1.5, label='Overall User Mean (Linea Mediana)')
        ]

        ax.legend(handles=legend_elements, loc='upper right')

        # --- Etichette e Titolo ---
        ax.set_title('User Latency Analysis: Custom Boxplot con Valori Etichettati')
        ax.set_xlabel('User')
        ax.set_ylabel('Latency (ms)')
        ax.set_xticks(x)
        ax.set_xticklabels(file_labels)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()

        return fig

    except Exception as e:
        print(f"Errore plotting latenza aggregata: {e}")
        import traceback
        traceback.print_exc()
        return None


def plot_logs_avg_latency(dfs, show_if_remote=True):
    """
    Plots the overall average per round alongside the average per file for that round,
    using WARM/COOL colors for equilibrium and different SHADES to distinguish files.
    """
    try:

        # Concatenazione dei DataFrame
        full_df = pd.concat(dfs, keys=range(1, len(dfs) + 1), names=['FileID', None])
        full_df = full_df.reset_index(level=0)

        avg_all_files = full_df.groupby('Group')['Duration'].mean().rename('Avg_All')
        avg_per_file = full_df.groupby(['Group', 'FileID'])['Duration'].mean().unstack(fill_value=np.nan)

        plot_df = pd.merge(avg_all_files, avg_per_file, left_index=True, right_index=True)
        all_groups = plot_df.index.tolist()

        # Colore WARM/COOL basato su BeforeEq
        group_before_eq = full_df.groupby('Group')['BeforeEq'].first()  # True/False per gruppo

        # 2. Setup Plot
        n_files = len(dfs)
        WARM_CMAP = plt.cm.Oranges
        COOL_CMAP = plt.cm.Blues

        warm_shades = WARM_CMAP(np.linspace(0.4, 1.0, n_files + 1))
        cool_shades = COOL_CMAP(np.linspace(0.4, 1.0, n_files + 1))

        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(14, 8))

        total_bars_in_group = n_files + 1
        bar_width = 0.8 / total_bars_in_group
        x = np.arange(len(all_groups))

        agg_pos = x - (total_bars_in_group / 2 - 0.5) * bar_width

        # 3. Barre Aggregate (Avg_All)
        agg_colors = []
        for g in all_groups:
            if group_before_eq[g]:
                agg_colors.append(warm_shades[0])
            else:
                agg_colors.append(cool_shades[0])

        ax.bar(
            agg_pos,
            plot_df['Avg_All'],
            bar_width,
            color=agg_colors,
            edgecolor='black',
            alpha=0.9,
            label='_nolegend_'
        )

        # 4. Barre per File
        for j in range(1, n_files + 1):
            file_col_name = j
            file_pos = agg_pos + j * bar_width

            file_bar_colors = []
            file_bar_hatches = []

            for g in all_groups:
                # Colore basato su BeforeEq
                if group_before_eq[g]:
                    file_bar_colors.append(warm_shades[j])
                else:
                    file_bar_colors.append(cool_shades[j])

                # Hatch se presente operazione non locale
                if 'Is_Local' in full_df.columns:
                    has_non_local = full_df[(full_df['Group'] == g) & (full_df['FileID'] == j)]['Is_Local'].apply(
                        lambda x: not x).any()
                    file_bar_hatches.append('//') if has_non_local and show_if_remote else file_bar_hatches.append(None)
                else:
                    file_bar_hatches.append(None)

            bars = ax.bar(
                file_pos,
                plot_df[file_col_name],
                bar_width,
                color=file_bar_colors,
                edgecolor='black',
                alpha=0.7,
                label='_nolegend_'
            )

            for bar, hatch_pattern in zip(bars, file_bar_hatches):
                if hatch_pattern:
                    bar.set_hatch(hatch_pattern)

        # 5. Linea media globale
        global_mean = plot_df['Avg_All'].mean()
        ax.axhline(global_mean, linestyle='--', linewidth=2, color='black', zorder=3)

        # 6. Etichette valori
        for i, v in enumerate(plot_df['Avg_All']):
            ax.text(agg_pos[i], v + 0.5, f'{v:.1f}', ha='center', fontsize=9, fontweight='bold')

        for j in range(1, n_files + 1):
            file_col_name = j
            file_pos = agg_pos + j * bar_width
            for i, v in enumerate(plot_df[file_col_name]):
                if pd.notna(v):
                    ax.text(file_pos[i], v + 0.5, f'{v:.1f}', ha='center', fontsize=9)

        # 7. Legenda
        equilibrium_legend = [
            Line2D([0], [0], color=WARM_CMAP(0.8), lw=4, label='Round avg Before Eq. (Warm Tones)'),
            Line2D([0], [0], color=COOL_CMAP(0.8), lw=4, label='Round avg After Eq. (Cool Tones)'),
        ]

        file_legend_elements = []
        hatch_legend_added = False
        for j in range(1, n_files + 1):
            file_legend_elements.append(
                Line2D([0], [0], color=warm_shades[j], lw=4, alpha=0.7, label=f'User {j} avg Before Eq.')
            )
            file_legend_elements.append(
                Line2D([0], [0], color=cool_shades[j], lw=4, alpha=0.7, label=f'User {j} avg After Eq.')
            )
            if 'Is_Local' in full_df.columns and not hatch_legend_added and show_if_remote:
                file_legend_elements.append(
                    Rectangle((0, 0), 1, 1, facecolor='white', edgecolor='black', hatch='//',
                              label='Non-Local Operation Present')
                )
                hatch_legend_added = True

        legend_elements = equilibrium_legend + file_legend_elements + [
            Line2D([0], [0], color='black', lw=2, linestyle='--', label=f'Global Mean: {global_mean:.2f} ms')
        ]

        ax.legend(
            handles=legend_elements,
            loc='lower center',
            bbox_to_anchor=(0.5, 1.05),
            ncol=3,
            frameon=False,
            fontsize=10
        )

        # 8. Asse e ticks
        ax.set_xlabel('Round number', fontsize=12)
        ax.set_ylabel('Average Time (ms)', fontsize=12)
        ax.set_xticks(x + (bar_width * total_bars_in_group / 2) - (bar_width / 2))
        ax.set_xticklabels(all_groups, rotation=0, fontsize=10)
        plt.yticks(fontsize=10)

        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)

        plt.tight_layout()

        # 9. Output
        print(f"Analysis completed for {len(all_groups)} groups using {len(dfs)} files.")
        print(f"Global average (Aggregated): {global_mean:.2f} ms")

        return avg_all_files

    except Exception as e:
        print(f"Errore nel plotting: {e}")
        import traceback
        traceback.print_exc()
        return None


def local_vs_remote_latency_violin(dfs):
    """
    Violin Plot personalizzato con Min, Max, Avg, Avg Local e Avg Remote.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(12, 7))

    n_files = len(dfs)
    x = np.arange(n_files)
    colors = plt.cm.Set1(np.linspace(0, 1, max(n_files, 3)))
    file_labels = [f'User {i + 1}' for i in range(n_files)]

    data_list = []
    stats = []

    for df in dfs:
        durations = df['Duration'].dropna()
        local_data = df[df['Is_Local'] == True]['Duration'].dropna()
        remote_data = df[df['Is_Local'] == False]['Duration'].dropna()

        data_list.append(durations.values)

        stats.append({
            'min': durations.min(),
            'max': durations.max(),
            'avg': durations.mean(),
            'avg_local': local_data.mean() if not local_data.empty else np.nan,
            'avg_remote': remote_data.mean() if not remote_data.empty else np.nan,
        })

    vp = ax.violinplot(
        data_list,
        positions=x,
        showmeans=False,
        showmedians=False,
        showextrema=False
    )

    for i, b in enumerate(vp['bodies']):
        b.set_facecolor(colors[i])
        b.set_alpha(0.4)

    for i, stat in enumerate(stats):
        current_x = x[i]
        user_color = colors[i]

        # Min e Max
        ax.vlines(current_x, stat['min'], stat['max'], color=user_color, linestyle=':', linewidth=1.5)
        ax.hlines(stat['min'], current_x - 0.1, current_x + 0.1, color=user_color, linewidth=2)
        ax.hlines(stat['max'], current_x - 0.1, current_x + 0.1, color=user_color, linewidth=2)

        # Avg totale
        ax.hlines(stat['avg'], current_x - 0.15, current_x + 0.15, color='black', linewidth=2)
        ax.text(current_x + 0.2, stat['avg'], f'Avg: {stat["avg"]:.2f}', fontsize=9, color='black',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

        # Avg Local
        if not np.isnan(stat['avg_local']):
            if int(stat['avg_local']) != int(stat['avg']):
                ax.hlines(stat['avg_local'], current_x - 0.12, current_x + 0.12,
                          color=user_color, linestyle='--', linewidth=2)
                ax.text(current_x + 0.2, stat['avg_local'], f'Loc: {stat["avg_local"]:.2f}',
                        fontsize=8, color=user_color)

        # Avg Remote
        if not np.isnan(stat['avg_remote']):
            if int(stat['avg_remote']) != int(stat['avg']):
                ax.hlines(stat['avg_remote'], current_x - 0.12, current_x + 0.12,
                          color=user_color, linestyle='-.', linewidth=2)
                ax.text(current_x + 0.2, stat['avg_remote'], f'Rem: {stat["avg_remote"]:.2f}',
                        fontsize=8, color=user_color)

    legend_elements = [
        Line2D([0], [0], color='black', lw=2, label='Avg Totale'),
        Line2D([0], [0], color='grey', lw=2, linestyle='--', label='Avg Local'),
        Line2D([0], [0], color='grey', lw=2, linestyle='-.', label='Avg Remote'),
        Line2D([0], [0], color='grey', lw=1.5, linestyle=':', label='Min/Max (Linea verticale)')
    ]
    ax.legend(handles=legend_elements, loc='upper right')

    ax.set_title('User Latency Analysis: Violin Plot con Distribuzione e Valori Statistici')
    ax.set_xlabel('User')
    ax.set_ylabel('Latency (ms)')
    ax.set_xticks(x)
    ax.set_xticklabels(file_labels)

    plt.tight_layout()
    return fig


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


def plot_tree_with_sparklines(tree: dict, dfs: list[pd.DataFrame]):
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
    task_counts['TaskCount'] = task_counts['TaskCount'] / len(relative_files)  # Normalizzazione

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
            paths[(entry_node, exec_node)] = compute_path(tree, entry_node, exec_node)

        path = paths[(entry_node, exec_node)]
        for node in path:
            if node == short_exec_host:
                continue
            mask = (task_counts['Node'] == node) & (task_counts['Group'] == group)
            task_counts.loc[mask, 'indirectLoad'] = task_counts.loc[mask, 'indirectLoad'] + 1

    task_counts['indirectLoad'] = task_counts['indirectLoad'] / len(relative_files)  # Normalizzazione

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
    plt.subplots_adjust(wspace=3)  # spazio tra subplots
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


def plot_heatmap_count_tasks(dfs):
    """
    Genera una heatmap che mostra il numero totale di esecuzioni (task)
    per ogni nodo di esecuzione (ExecHost) su ogni round (Group).
    (ExecHost sull'asse Y, Round sull'asse X)
    """

    try:
        df_combined = pd.concat(dfs, ignore_index=True)

        heatmap_data = df_combined.groupby(['Group', 'ExecHost']).size().reset_index(name='TaskCount')
        heatmap_data['TaskCount'] = heatmap_data['TaskCount'] / len(relative_files)  # Normalizzazione
        heatmap_data['Host_Label'] = heatmap_data['ExecHost'].str.split('.').str[-1].str.split(':').str[0]

        pivot_table = heatmap_data.pivot_table(
            index='Host_Label',  # Host sull'asse Y
            columns='Group',  # Round sull'asse X
            values='TaskCount',  # Numero di task
            fill_value=0
        )

        pivot_table = pivot_table.reindex(sorted(pivot_table.index, key=lambda x: int(x)), axis=0)

        num_rows = len(pivot_table.index)  # Numero di Host (altezza)
        num_cols = len(pivot_table.columns)  # Numero di Round (larghezza)

        cell_size = 0.5
        padding_width = 4
        padding_height = 4

        figure_width = max(6, num_cols * cell_size + padding_width)
        figure_height = max(6, num_rows * cell_size + padding_height)

        plt.figure(figsize=(figure_width, figure_height))

        cax = plt.imshow(pivot_table, cmap='magma', aspect='auto', interpolation='nearest')

        ax = plt.gca()

        threshold = pivot_table.values.max() / 2.0

        for i in range(num_rows):
            for j in range(num_cols):
                val = pivot_table.iloc[i, j]

                # Opzionale: Non stampare se il valore è 0 per mantenere il grafico pulito
                if val > 0:
                    # Colore testo: Nero se sfondo chiaro, Bianco se sfondo scuro
                    text_color = "black" if val > threshold else "white"

                    # Formattazione: .1f per un decimale, .0f per intero
                    # Uso .1f visto che nel tuo codice fai una divisione (normalizzazione)
                    label_text = f"{val:.1f}"

                    ax.text(j, i, label_text,
                            ha="center", va="center",
                            color=text_color, fontsize=8, fontweight='bold')

        # Griglia per separare visivamente le celle
        ax.set_xticks(np.arange(num_cols + 1) - .5, minor=True)
        ax.set_yticks(np.arange(num_rows + 1) - .5, minor=True)

        ax.grid(which="minor", color="w", linestyle='-', linewidth=2)
        ax.tick_params(which='major', length=0)
        ax.grid(which='major', visible=False)

        # Titoli e etichette
        plt.title(f'Tasks executed heatmap per node', fontsize=16)
        plt.xlabel('Round (Gruppo)', fontsize=14)
        plt.ylabel('ExecHost', fontsize=14)

        plt.xticks(ticks=np.arange(len(pivot_table.columns)), labels=pivot_table.columns, rotation=90)
        plt.yticks(ticks=np.arange(len(pivot_table.index)), labels=pivot_table.index)

        # Colorbar
        cbar = plt.colorbar(cax, label='Tasks executed (count)')

        plt.tight_layout()

    except Exception as e:
        print(f"Errore nel plotting della heatmap: {e}")
        import traceback
        traceback.print_exc()
        return None


def plot_heatmap_avg_latency(dfs):
    """
    Genera una heatmap che mostra il tempo medio di esecuzione (Duration) 
    per ogni nodo di esecuzione (ExecHost) su ogni round (Group).
    (ExecHost sull'asse Y, Round sull'asse X)
    """

    try:
        df_combined = pd.concat(dfs, ignore_index=True)

        heatmap_data = df_combined.groupby(['Group', 'ExecHost'])['Duration'].mean().reset_index()

        heatmap_data['Host_Label'] = heatmap_data['ExecHost'].str.split('.').str[-1].str.split(':').str[0]

        pivot_table = heatmap_data.pivot_table(
            index='Host_Label',  # Host sull'asse Y
            columns='Group',  # Round sull'asse X
            values='Duration',
            fill_value=0
        )

        pivot_table = pivot_table.reindex(sorted(pivot_table.index, key=lambda x: int(x)), axis=0)

        num_rows = len(pivot_table.index)  # Numero di Host (altezza)
        num_cols = len(pivot_table.columns)  # Numero di Round (larghezza)

        cell_size = 0.5
        padding_width = 4
        padding_height = 4

        figure_width = max(6, num_cols * cell_size + padding_width)
        figure_height = max(6, num_rows * cell_size + padding_height)

        plt.figure(figsize=(figure_width, figure_height))

        cax = plt.imshow(pivot_table, cmap='magma', aspect='auto', interpolation='nearest')

        ax = plt.gca()
        threshold = pivot_table.values.max() / 2.0

        for i in range(num_rows):
            for j in range(num_cols):
                val = pivot_table.iloc[i, j]

                # Opzionale: Non stampare se il valore è 0 per mantenere il grafico pulito
                if val > 0:
                    # Colore testo: Nero se sfondo chiaro, Bianco se sfondo scuro
                    text_color = "black" if val > threshold else "white"

                    # Formattazione: .1f per un decimale, .0f per intero
                    # Uso .1f visto che nel tuo codice fai una divisione (normalizzazione)
                    label_text = f"{val:.1f}"

                    ax.text(j, i, label_text,
                            ha="center", va="center",
                            color=text_color, fontsize=8, fontweight='bold')

        ax.set_xticks(np.arange(num_cols + 1) - .5, minor=True)
        ax.set_yticks(np.arange(num_rows + 1) - .5, minor=True)

        ax.grid(which="minor", color="w", linestyle='-', linewidth=2)
        ax.tick_params(which='major', length=0)
        ax.grid(which='major', visible=False)

        plt.title(f'avg execution time heatmap per node', fontsize=16)
        plt.xlabel('Round (Gruppo)', fontsize=14)
        plt.ylabel('ExecHost', fontsize=14)

        plt.xticks(ticks=np.arange(len(pivot_table.columns)), labels=pivot_table.columns, rotation=90)
        plt.yticks(ticks=np.arange(len(pivot_table.index)), labels=pivot_table.index)

        cbar = plt.colorbar(cax, label='avg execution time (ms)')

        plt.tight_layout()

    except Exception as e:
        print(f"Errore nel plotting della heatmap: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============== MAIN EXECUTION ==============

current_file_path = inspect.getfile(inspect.currentframe())
base_dir = Path(current_file_path).parent

files = [
    (base_dir / rel_path).resolve()
    for rel_path in relative_files
]

output_dir = os.path.join(base_dir, '..', 'output_img', out_dir)
output_dir = Path(output_dir).resolve()

if output_dir.exists() and output_dir.is_dir():
    for item in output_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

output_dir.mkdir(parents=True, exist_ok=True)

full_dfs = []
for f in files:
    csv, log = processa_zip_files(f)
    parsed_log = parse_log(log)
    print(f"Processed {len(csv)} CSV files and {len(log)} LOG files from ZIP archives.")

    dfs = parse_dfs(csv, parsed_log)
    print(f"Parsed {len(dfs)} DataFrames from CSV files.")

    dfs, eq_timestamp = find_equilibrium_timestamp(dfs)

    if full_dfs == []:
        full_dfs = dfs
    else:
        for i, df in enumerate(dfs):
            full_dfs[i] = pd.concat([full_dfs[i], df], ignore_index=True)

print(f"Equilibrium Timestamp: {eq_timestamp}")

plot_logs_avg_latency(full_dfs)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
plt.savefig(f'{output_dir}/execution_time_analysis_{timestamp}.png', dpi=300, bbox_inches='tight')

local_vs_remote_number_of_executions(full_dfs)
plt.savefig(f'{output_dir}/local_vs_remote_executions_{timestamp}.png', dpi=300, bbox_inches='tight')

local_vs_remote_latency(full_dfs)
plt.savefig(f'{output_dir}/local_vs_remote_latency_{timestamp}.png', dpi=300, bbox_inches='tight')

plot_heatmap_avg_latency(full_dfs)
plt.savefig(f'{output_dir}/heatmap_avg_latency_{timestamp}.png', dpi=300, bbox_inches='tight')

plot_heatmap_count_tasks(full_dfs)
plt.savefig(f'{output_dir}/heatmap_count_tasks_{timestamp}.png', dpi=300, bbox_inches='tight')

local_vs_remote_latency_violin(full_dfs)
plt.savefig(f'{output_dir}/local_vs_remote_latency_violin_{timestamp}.png', dpi=300, bbox_inches='tight')

fig_tree = plot_tree_with_sparklines(tree, full_dfs)
fig_tree.savefig(f'{output_dir}/tree_with_sparklines_{timestamp}.png', dpi=300, bbox_inches='tight')

if len(sys.argv) <= 1 or sys.argv[1] != '--hide':
    plt.show()
