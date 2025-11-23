import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

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
        file_labels = [f'User {i+1}' for i in range(n_files)]
        
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
                ax.bar(current_x, height_mean, bottom=lower_mean, width=bar_width*0.6,
                       color=user_color, alpha=0.5, edgecolor=user_color, linewidth=1, zorder=2, label='_nolegend_')

                # Stelo inferiore (Min al bordo inferiore del box)
                if not np.isnan(data['min']):
                    ax.vlines(current_x, data['min'], lower_mean,
                            colors=[user_color], alpha=0.8, linestyle=':', linewidth=stem_line_width, zorder=1, label='_nolegend_')

                # Stelo superiore (bordo superiore del box al Max)
                if not np.isnan(data['max']):
                    ax.vlines(current_x, upper_mean, data['max'],
                            colors=[user_color], alpha=0.8, linestyle=':', linewidth=stem_line_width, zorder=1, label='_nolegend_')
            elif not np.isnan(data['mean_total']):
                # Stelo inferiore (Min al bordo inferiore del box)
                if not np.isnan(data['min']):
                    ax.vlines(current_x, data['min'], data['mean_total'],
                            colors=[user_color], alpha=0.8, linestyle=':', linewidth=stem_line_width, zorder=1, label='_nolegend_')

                # Stelo superiore (bordo superiore del box al Max)
                if not np.isnan(data['max']):
                    ax.vlines(current_x, data['mean_total'], data['max'],
                            colors=[user_color], alpha=0.8, linestyle=':', linewidth=stem_line_width, zorder=1, label='_nolegend_')
                       
            # 3. Segni Min/Max (i "whiskers") + ETICHETTE MIN E MAX
            if not np.isnan(data['min']):
                ax.hlines(data['min'], current_x - bar_width*0.2, current_x + bar_width*0.2,
                          colors=[user_color], linewidth=2, zorder=4, label='_nolegend_')
                # Etichetta Min
                ax.text(text_x_pos, data['min'], f'Min: {data["min"]:.2f}', 
                        ha='left', va='center', fontsize=8, color=user_color, weight='bold')
                
            if not np.isnan(data['max']):
                 ax.hlines(data['max'], current_x - bar_width*0.2, current_x + bar_width*0.2,
                          colors=[user_color], linewidth=2, zorder=4, label='_nolegend_')
                 ax.text(text_x_pos, data['max'], f'Max: {data["max"]:.2f}', 
                        ha='left', va='center', fontsize=8, color=user_color, weight='bold')

            # 4. Linea Media Totale + ETICHETTA MEDIA
            if not np.isnan(data['mean_total']):
                ax.hlines(data['mean_total'], current_x - bar_width*0.4, current_x + bar_width*0.4,
                          colors=[user_color], linewidth=2, zorder=3, label='_nolegend_')
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
    file_labels = [f'User {i+1}' for i in range(n_files)]

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

def plot_logs_avg_latency(dfs, show_if_remote = True):
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
                    has_non_local = full_df[(full_df['Group'] == g) & (full_df['FileID'] == j)]['Is_Local'].apply(lambda x: not x).any()
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
                    Rectangle((0,0),1,1, facecolor='white', edgecolor='black', hatch='//', label='Non-Local Operation Present')
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
