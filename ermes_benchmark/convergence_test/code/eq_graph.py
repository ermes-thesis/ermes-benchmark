import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import inspect
from pathlib import Path
from datetime import datetime


import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ignored_functions = ['functionCreateCollections', 'functionCreateSeqCollections']
eq_map = {
    'functionUseSeqCollections-10.10.101.51:12345': '10.10.101.51:12345',
    'functionReadSeqCollections-10.10.101.54:12345': '10.10.101.54:12345',
}

def parse_dfs(files, n):
    """
    Parse multiple CSV files into DataFrames, ensuring they have the same number of rows.
    """
    dfs = []
    reference_len = None

    for file_name in files:
        current_df = pd.read_csv(file_name, header=0)

        if 'ignored_functions' in globals() and ignored_functions:
            current_df = current_df[~current_df['FuncName'].isin(ignored_functions)]
            
        current_df = current_df.reset_index(drop=True)
            
        current_len = len(current_df)
        if reference_len is None:
            reference_len = current_len
        elif current_len != reference_len:
            raise Exception(
                    f"CRITICAL ERROR: The file '{file_name}' has {current_len} rows, "
                    f"but the first analyzed file had {reference_len}. "
                    "All files must have the same number of executions to avoid skewing the average."
            )
            
        current_df['Duration'] = current_df['FuncDuration'].astype(str).str.replace('ms', '').astype(float)
        
        current_df['StartTime'] = pd.to_datetime(current_df['StartTime'])

        current_df['Is_Local'] = current_df['EntryHost'] == current_df['ExecHost']
            
        current_df['Group'] = current_df.index // n
            
        dfs.append(current_df)
    
    return dfs

def find_equilibrium_timestamp(dfs):
    """
    Find the equilibrium timestamp across multiple DataFrames.
    """
    min_timestamps = []
    for df in dfs:
        for index, row in df.iterrows():
            if row['FuncName']+"-"+row['EntryHost'] in eq_map and row['ExecHost'] == eq_map[row['FuncName']+"-"+row['EntryHost']]:
                min_timestamps.append(row['StartTime'])
                break

    if min_timestamps:
        return max(min_timestamps)
    else:
        return None

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
                                color=colors[i], edgecolor='black', label=f'File {i+1} Local')
            
            for bar in bars_local:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=9, color='#555555')

            bars_remote = ax.bar(pos_remote, remote_vals, single_bar_width, 
                                 color=colors[i], edgecolor='black', hatch='//', alpha=0.7, label=f'File {i+1} Remote')
            
            for bar in bars_remote:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
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
        # plt.show()
        
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
        fig, ax = plt.subplots(figsize=(12, 7)) # Aumento leggermente la dimensione per far spazio alle etichette
        
        n_files = len(dfs)
        x = np.arange(n_files)
        total_width = 0.8
        single_bar_width = total_width / 1
        
        colors = plt.cm.Set1(np.linspace(0, 1, max(n_files, 3)))
        file_labels = [f'User {i+1}' for i in range(n_files)]
        
        all_durations = []
        data_to_plot = []
        
        # --- Calcolo dei limiti dell'asse Y e delle medie/min/max ---
        for df in dfs:
            durations = df['Duration'].dropna()
            if not durations.empty:
                all_durations.extend(durations.tolist())
            
            # Statistiche
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
            
        # --- Plotting e Etichettatura ---
        for i, data in enumerate(data_to_plot):
            current_x = x[i]
            user_color = colors[i]
            bar_width = single_bar_width * 0.8
            stem_line_width = 1.2
            
            # Posizione per le etichette di testo (leggermente a destra del centro della barra)
            text_x_pos = current_x + bar_width * 0.25 
            
            # 1. Barra Min/Max (Sfondo Trasparente)
            if not np.isnan(data['min']) and not np.isnan(data['max']):
                min_val = data['min']
                max_val = data['max']
                height_overall = max_val - min_val
                
                ax.bar(current_x, height_overall, bottom=min_val, width=bar_width,
                       color='grey', alpha=0.15, edgecolor=None, linewidth=0, zorder=0, label='_nolegend_')

            # 2. Barra Media Locale vs Media Remota (Il "Box") e Steli
            if not np.isnan(data['lower_mean']) and not np.isnan(data['upper_mean']):
                lower_mean = data['lower_mean']
                upper_mean = data['upper_mean']
                height_mean = upper_mean - lower_mean
                
                # Box
                ax.bar(current_x, height_mean, bottom=lower_mean, width=bar_width*0.6,
                       color=user_color, alpha=0.5, edgecolor=user_color, linewidth=1, zorder=2, label='_nolegend_')

                # Stelo inferiore (Min al bordo inferiore del box)
                if not np.isnan(data['min']):
                     ax.vlines(current_x, data['min'], lower_mean,
                              colors=[user_color], linestyle='-', linewidth=stem_line_width, zorder=1, label='_nolegend_')
                
                # Stelo superiore (bordo superiore del box al Max)
                if not np.isnan(data['max']):
                    ax.vlines(current_x, upper_mean, data['max'],
                              colors=[user_color], linestyle='-', linewidth=stem_line_width, zorder=1, label='_nolegend_')
                       
            # 3. Segni Min/Max (i "whiskers") + ETICHETTE MIN E MAX
            if not np.isnan(data['min']):
                # Whisker Min
                ax.hlines(data['min'], current_x - bar_width*0.2, current_x + bar_width*0.2,
                          colors=[user_color], linewidth=1, zorder=4, label='_nolegend_')
                # Etichetta Min
                ax.text(text_x_pos, data['min'], f'Min: {data["min"]:.2f}', 
                        ha='left', va='center', fontsize=8, color=user_color, weight='bold')
                
            if not np.isnan(data['max']):
                # Whisker Max
                 ax.hlines(data['max'], current_x - bar_width*0.2, current_x + bar_width*0.2,
                          colors=[user_color], linewidth=1, zorder=4, label='_nolegend_')
                # Etichetta Max
                 ax.text(text_x_pos, data['max'], f'Max: {data["max"]:.2f}', 
                        ha='left', va='center', fontsize=8, color=user_color, weight='bold')

            # 4. Linea Media Totale + ETICHETTA MEDIA
            if not np.isnan(data['mean_total']):
                # Linea Media Totale
                ax.hlines(data['mean_total'], current_x - bar_width*0.4, current_x + bar_width*0.4,
                          colors='black', linewidth=1.5, zorder=3, label='_nolegend_')
                # Etichetta Media Totale
                ax.text(text_x_pos, data['mean_total'], f'Avg: {data["mean_total"]:.2f}', 
                        ha='left', va='center', fontsize=9, color='black', weight='bold',
                        bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='square,pad=0.2'))
        
        # --- Legenda ---
        legend_elements = [
            Patch(facecolor='grey', alpha=0.15, edgecolor=None, linewidth=0, label=r'Overall Latency Range (Min $\leftrightarrow$ Max)'),
            Line2D([0], [0], color=colors[0], lw=stem_line_width, label='Min/Max Whisker (Stem) (Colore per Utente)'),
            Patch(facecolor=colors[0], alpha=0.5, edgecolor=colors[0], label=r'Mean Range (Local Mean $\leftrightarrow$ Remote Mean)'),
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
    
def plot_logs_avg_latency(dfs, eq_timestamp):
    """
    Plots the overall average per round alongside the average per file for that round,
    using WARM/COOL colors for equilibrium and different SHADES to distinguish files.
    """
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.lines import Line2D
        
        limit_ts = pd.to_datetime(eq_timestamp)

        full_df = pd.concat(dfs, keys=range(1, len(dfs) + 1), names=['FileID', None])
        full_df = full_df.reset_index(level=0)

        avg_all_files = full_df.groupby('Group')['Duration'].mean().rename('Avg_All')
        avg_per_file = full_df.groupby(['Group', 'FileID'])['Duration'].mean().unstack(fill_value=np.nan)

        plot_df = pd.merge(avg_all_files, avg_per_file, left_index=True, right_index=True)
        all_groups = plot_df.index.tolist()
        
        n_files = len(dfs)
        WARM_CMAP = plt.cm.Oranges
        COOL_CMAP = plt.cm.Blues

        warm_shades = WARM_CMAP(np.linspace(0.4, 1.0, n_files + 1)) 
        cool_shades = COOL_CMAP(np.linspace(0.4, 1.0, n_files + 1))
        
        group_file_min_dates = full_df.groupby(['Group', 'FileID'])['StartTime'].min()
        group_min_dates = full_df.groupby('Group')['StartTime'].min()
        
        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(14, 8))
        
        total_bars_in_group = n_files + 1
        bar_width = 0.8 / total_bars_in_group
        x = np.arange(len(all_groups))

        agg_pos = x - (total_bars_in_group / 2 - 0.5) * bar_width 
        
        agg_colors = []
        for g in all_groups:
            if limit_ts is not None and group_min_dates[g] > limit_ts:
                agg_colors.append(cool_shades[0])
            else:
                agg_colors.append(warm_shades[0])

        ax.bar(
            agg_pos,
            plot_df['Avg_All'],
            bar_width,
            color=agg_colors,
            edgecolor='black',
            alpha=0.9,
            label='_nolegend_'
        )

        for j in range(1, n_files + 1):
            file_col_name = j 
            file_pos = agg_pos + j * bar_width
            
            file_bar_colors = []
            for g in all_groups:
                try:
                    min_date = group_file_min_dates[(g, j)]
                except KeyError:
                    min_date = pd.NaT 
                
                if pd.notna(min_date) and limit_ts is not None and min_date > limit_ts:
                    file_bar_colors.append(cool_shades[j])
                else:
                    file_bar_colors.append(warm_shades[j])

            
            ax.bar(
                file_pos,
                plot_df[file_col_name],
                bar_width,
                color=file_bar_colors,
                edgecolor='black',
                alpha=0.7,
                label='_nolegend_'
            )

        global_mean = plot_df['Avg_All'].mean()
        ax.axhline(global_mean, linestyle='--', linewidth=2, color='black', zorder=3)

        for i, v in enumerate(plot_df['Avg_All']):
            ax.text(agg_pos[i], v + 0.5, f'{v:.1f}', ha='center', fontsize=9, fontweight='bold')
            
        for j in range(1, n_files + 1):
            file_col_name = j 
            file_pos = agg_pos + j * bar_width
            
            for i, v in enumerate(plot_df[file_col_name]):
                if pd.notna(v):
                    ax.text(file_pos[i], v + 0.5, f'{v:.1f}', ha='center', fontsize=9)

        equilibrium_legend = [
            Line2D([0], [0], color=WARM_CMAP(0.8), lw=4, label='Round avg Time Before Eq. (Warm Tones)'),
            Line2D([0], [0], color=COOL_CMAP(0.8), lw=4, label='Round avg Time After Eq. (Cool Tones)'),
        ]
        
        file_legend_elements = []
        for j in range(1, n_files + 1):
            file_legend_elements.append(
                Line2D([0], [0], color=warm_shades[j], lw=4, alpha=0.7, label=f'User {j} avg Time Before Eq.')
            )
            file_legend_elements.append(
                Line2D([0], [0], color=cool_shades[j], lw=4, alpha=0.7, label=f'User {j} avg Time After Eq.')
            )

        legend_elements = equilibrium_legend + file_legend_elements + [Line2D([0], [0], color='black', lw=2, linestyle='--', label=f'Global Mean: {global_mean:.2f} ms')]
        
        ax.legend(
            handles=legend_elements, 
            loc='lower center', 
            bbox_to_anchor=(0.5, 1.05), 
            ncol=3, 
            frameon=False,
            fontsize=10
        )

        ax.set_xlabel('Round number', fontsize=12)
        ax.set_ylabel('Average Time (ms)', fontsize=12)
        ax.set_xticks(x + (bar_width * total_bars_in_group / 2) - (bar_width / 2) ) 
        ax.set_xticklabels(all_groups, rotation=0, fontsize=10)
        plt.yticks(fontsize=10)

        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)

        plt.tight_layout()
        
        print(f"Analysis completed for {len(all_groups)} groups using {len(dfs)} files.")
        print(f"Global average (Aggregated): {global_mean:.2f} ms")
        
        return avg_all_files

    except Exception as e:
        print(f"Errore nel plotting: {e}")
        import traceback
        traceback.print_exc()
        return None

def plot_heatmap_count_tasks(dfs, n):
    """
    Genera una heatmap che mostra il numero totale di esecuzioni (task) 
    per ogni nodo di esecuzione (ExecHost) su ogni round (Group).
    (ExecHost sull'asse Y, Round sull'asse X)
    """
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    
    try:
        df_combined = pd.concat(dfs, ignore_index=True)

        heatmap_data = df_combined.groupby(['Group', 'ExecHost']).size().reset_index(name='TaskCount')

        heatmap_data['Host_Label'] = heatmap_data['ExecHost'].str.split('.').str[-1].str.split(':').str[0]
        
        pivot_table = heatmap_data.pivot_table(
            index='Host_Label', # Host sull'asse Y
            columns='Group',    # Round sull'asse X
            values='TaskCount', # Numero di task
            fill_value=0
        )
        
        pivot_table = pivot_table.reindex(sorted(pivot_table.index, key=lambda x: int(x)), axis=0)

        
        num_rows = len(pivot_table.index)    # Numero di Host (altezza)
        num_cols = len(pivot_table.columns)  # Numero di Round (larghezza)
        
        cell_size = 0.5 
        padding_width = 4  
        padding_height = 4 
        
        figure_width = max(6, num_cols * cell_size + padding_width)
        figure_height = max(6, num_rows * cell_size + padding_height)

        plt.figure(figsize=(figure_width, figure_height)) 
        
        cax = plt.imshow(pivot_table, cmap='magma', aspect='auto', interpolation='nearest')
        
        ax = plt.gca()
        

        # Griglia per separare visivamente le celle
        ax.set_xticks(np.arange(num_cols + 1) - .5, minor=True)
        ax.set_yticks(np.arange(num_rows + 1) - .5, minor=True)
        
        ax.grid(which="minor", color="w", linestyle='-', linewidth=2)
        ax.tick_params(which='major', length=0)
        
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

def plot_heatmap_avg_latency(dfs, n):
    """
    Genera una heatmap che mostra il tempo medio di esecuzione (Duration) 
    per ogni nodo di esecuzione (ExecHost) su ogni round (Group).
    (ExecHost sull'asse Y, Round sull'asse X)
    """
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    
    try:
        df_combined = pd.concat(dfs, ignore_index=True)

        heatmap_data = df_combined.groupby(['Group', 'ExecHost'])['Duration'].mean().reset_index()

        heatmap_data['Host_Label'] = heatmap_data['ExecHost'].str.split('.').str[-1].str.split(':').str[0]
        
        pivot_table = heatmap_data.pivot_table(
            index='Host_Label', # Host sull'asse Y
            columns='Group',    # Round sull'asse X
            values='Duration', 
            fill_value=0
        )
        
        pivot_table = pivot_table.reindex(sorted(pivot_table.index, key=lambda x: int(x)), axis=0)

        
        num_rows = len(pivot_table.index)    # Numero di Host (altezza)
        num_cols = len(pivot_table.columns)  # Numero di Round (larghezza)
        
        cell_size = 0.5 
        padding_width = 4  
        padding_height = 4 
        
        figure_width = max(6, num_cols * cell_size + padding_width)
        figure_height = max(6, num_rows * cell_size + padding_height)

        plt.figure(figsize=(figure_width, figure_height)) 
        
        cax = plt.imshow(pivot_table, cmap='magma', aspect='auto', interpolation='nearest')
        
        ax = plt.gca()
        

        ax.set_xticks(np.arange(num_cols + 1) - .5, minor=True)
        ax.set_yticks(np.arange(num_rows + 1) - .5, minor=True)
        
        ax.grid(which="minor", color="w", linestyle='-', linewidth=2)
        ax.tick_params(which='major', length=0)
        
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

n = 50 # Numero di funzioni per round
relative_files = [
    '../data/results_log_54321_2025_11_19_17_40_57.csv', 
    '../data/results_log_12345_2025_11_19_17_40_55.csv'
]


current_file_path = inspect.getfile(inspect.currentframe())
base_dir = Path(current_file_path).parent

files = [
    (base_dir / rel_path).resolve() 
    for rel_path in relative_files
]



dfs = parse_dfs(files, n)

find_equilibrium_timestamp(dfs)
eq_timestamp = find_equilibrium_timestamp(dfs)
print(f"Equilibrium Timestamp: {eq_timestamp}")

plot_logs_avg_latency(dfs, eq_timestamp)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
plt.savefig(f'{base_dir}/../output_img/execution_time_analysis_{timestamp}.png', dpi=300, bbox_inches='tight')

local_vs_remote_number_of_executions(dfs)
plt.savefig(f'{base_dir}/../output_img/local_vs_remote_executions_{timestamp}.png', dpi=300, bbox_inches='tight')

local_vs_remote_latency(dfs)
plt.savefig(f'{base_dir}/../output_img/local_vs_remote_latency_{timestamp}.png', dpi=300, bbox_inches='tight')

plot_heatmap_avg_latency(dfs, n)
plt.savefig(f'{base_dir}/../output_img/heatmap_avg_latency_{timestamp}.png', dpi=300, bbox_inches='tight')

plot_heatmap_count_tasks(dfs, n)
plt.savefig(f'{base_dir}/../output_img/heatmap_count_tasks_{timestamp}.png', dpi=300, bbox_inches='tight')

plt.show()