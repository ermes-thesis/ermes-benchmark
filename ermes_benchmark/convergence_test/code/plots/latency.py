import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.patches import Patch


def local_vs_remote_latency(dfs):
    """
    Custom Latency Plot with Min, Max, and Avg values displayed as text labels.
    """
    try:

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

        ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, 1.05), ncol=2, frameon=False,
                  fontsize=10)

        # --- Etichette e Titolo ---
        # ax.set_title('User Latency Analysis: Custom Boxplot con Valori Etichettati')
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
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(8, 5))

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
        widths=0.8,
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
        ax.hlines(stat['min'], current_x - 0.1, current_x + 0.1, color=user_color, linewidth=1)
        ax.hlines(stat['max'], current_x - 0.1, current_x + 0.1, color=user_color, linewidth=1)
        ax.text(current_x - 0.35, stat['min'], f'Min: {stat["min"]:.2f}',
                ha='left', va='center', fontsize=8, color=user_color,
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
        ax.text(current_x - 0.35, stat['max'], f'Max: {stat["max"]:.2f}',
                ha='left', va='center', fontsize=8, color=user_color,
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

        # Avg totale
        ax.hlines(stat['avg'], current_x - 0.15, current_x + 0.15, color='black', linewidth=2)
        ax.text(current_x + 0.17, stat['avg'], f'Avg: {stat["avg"]:.2f}', fontsize=8, color='black',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

        # Avg Local
        if not np.isnan(stat['avg_local']) and int(stat['avg_local']) != int(stat['avg']):
            ax.hlines(stat['avg_local'], current_x - 0.12, current_x + 0.12,
                      color=user_color, linestyle='--', linewidth=2)
            ax.text(current_x + 0.17, stat['avg_local'], f'Local: {stat["avg_local"]:.2f}',
                    fontsize=8, color=user_color, bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

        # Avg Remote
        if not np.isnan(stat['avg_remote']) and int(stat['avg_remote']) != int(stat['avg']):
            ax.hlines(stat['avg_remote'], current_x - 0.12, current_x + 0.12,
                      color=user_color, linestyle='-.', linewidth=2)
            ax.text(current_x + 0.17, stat['avg_remote'], f'Remote: {stat["avg_remote"]:.2f}',
                    fontsize=8, color=user_color, bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

    legend_elements = [
        Line2D([0], [0], color='black', lw=2, label='Global Avg'),
        Line2D([0], [0], color='grey', lw=2, linestyle='--', label='Local Avg'),
        Line2D([0], [0], color='grey', lw=2, linestyle='-.', label='Remote Avg'),
        # Line2D([0], [0], color='grey', lw=1.5, linestyle=':', label='Min/Max (Vertical Line)'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', facecolor='white')

    # ax.set_title('User Latency Analysis: Violin Plot con Distribuzione e Valori Statistici')
    ax.set_xlabel('User')
    ax.set_ylabel('Latency (ms)')
    ax.set_xticks(x)
    ax.set_xticklabels(file_labels)

    plt.tight_layout()
    return fig


def plot_logs_avg_latency(dfs, scenario, show_if_remote=True):
    """
    Plots the overall average per round alongside the average per file for that round.
    The bar is split: the hatched portion represents the % of non-local executions.
    """
    try:
        # 1. Concatenate all files
        full_df = pd.concat(dfs, keys=range(1, len(dfs) + 1), names=['FileID', None])
        full_df = full_df.reset_index(level=0)

        # Calcolo medie (Altezza totale delle barre)
        avg_all_files = full_df.groupby('Group')['Duration'].mean().rename('Avg_All')
        avg_per_file = full_df.groupby(['Group', 'FileID'])['Duration'].mean().unstack(fill_value=np.nan)

        plot_df = pd.merge(avg_all_files, avg_per_file, left_index=True, right_index=True)
        all_groups = plot_df.index.tolist()

        # ----------------------------
        # PRE-CALCOLO RATIO NON-LOCAL
        # ----------------------------
        # Calcoliamo la % di righe con Is_Local=False per ogni Gruppo/File
        if 'Is_Local' in full_df.columns:
            # (~x).mean() calcola la percentuale di False (cioè non-local)
            non_local_ratio = full_df.groupby(['Group', 'FileID'])['Is_Local'].apply(lambda x: (~x).mean()).unstack(
                fill_value=0)
        else:
            non_local_ratio = pd.DataFrame(0, index=plot_df.index, columns=avg_per_file.columns)

        # ----------------------------
        # 2. warm / cool / mixed logic
        # ----------------------------
        group_status = {}
        for g, subdf in full_df.groupby('Group')['BeforeEq']:
            if subdf.all():
                group_status[g] = "warm"
            elif (~subdf).all():
                group_status[g] = "cool"
            else:
                group_status[g] = "mixed"

        # Colormaps
        n_files = len(dfs)
        WARM_CMAP = plt.cm.Oranges
        COOL_CMAP = plt.cm.Blues

        warm_shades = WARM_CMAP(np.linspace(0.4, 1.0, n_files + 1))
        cool_shades = COOL_CMAP(np.linspace(0.4, 1.0, n_files + 1))

        # Gray shades for mixed
        gray_shades = np.linspace(0.35, 0.75, n_files + 1)
        gray_colors = [(g, g, g, 0.9) for g in gray_shades]
        gray_colors_file = [(g, g, g, 0.7) for g in gray_shades]

        # ----------------------------
        # 3. Setup Plot
        # ----------------------------
        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(10, 6))

        total_bars_in_group = n_files + 1
        bar_width = 0.8 / total_bars_in_group
        x = np.arange(len(all_groups))
        agg_pos = x - (total_bars_in_group / 2 - 0.5) * bar_width

        # ----------------------------
        # 4. Aggregate bars (Avg_All) - Nessuna modifica qui (o logica simile se volessi split anche qui)
        # ----------------------------
        agg_colors = []
        for g in all_groups:
            if group_status[g] == "warm":
                agg_colors.append(warm_shades[0])
            elif group_status[g] == "cool":
                agg_colors.append(cool_shades[0])
            else:
                agg_colors.append(gray_colors[0])

        ax.bar(
            agg_pos,
            plot_df['Avg_All'],
            bar_width,
            color=agg_colors,
            edgecolor='black',
            linewidth=1.3,
            alpha=0.9,
            label='_nolegend_'
        )

        # ----------------------------
        # 5. Per-file bars (STACKED LOGIC)
        # ----------------------------
        gray_hatch_color = (0.2, 0.2, 0.2, 0.5)  # Grigio scuro per le righe dell'hatch

        for j in range(1, n_files + 1):
            file_pos = agg_pos + j * bar_width

            # Liste per i colori e le altezze di questo specifico Client (FileID j)
            bar_colors = []
            total_heights = []
            ratios = []

            for g in all_groups:
                # Determina colore base
                if group_status[g] == "warm":
                    bar_colors.append(warm_shades[j])
                elif group_status[g] == "cool":
                    bar_colors.append(cool_shades[j])
                else:
                    bar_colors.append(gray_colors_file[j])

                # Ottieni altezza totale e ratio
                h = plot_df.loc[g, j]
                r = non_local_ratio.loc[g, j] if j in non_local_ratio.columns else 0

                # Gestione NaN
                if pd.isna(h): h = 0
                if pd.isna(r): r = 0

                total_heights.append(h)
                ratios.append(r)

            # Convertiamo in numpy array per calcoli vettoriali facili
            total_heights = np.array(total_heights)
            ratios = np.array(ratios)

            # Calcolo altezze parziali
            if show_if_remote:
                height_hatched = total_heights * ratios  # Parte NON locale
                height_solid = total_heights - height_hatched  # Parte locale
            else:
                height_hatched = np.zeros_like(total_heights)
                height_solid = total_heights

            # Disegna la parte SOLIDA (Base)
            ax.bar(
                file_pos,
                height_solid,
                bar_width,
                bottom=height_hatched,
                color=bar_colors,
                edgecolor='black',  # o None se preferisci meno bordi interni
                alpha=0.7,
                label='_nolegend_'
            )

            # Disegna la parte HATCHED (Top) - usa bottom=height_solid
            # Disegniamo solo se c'è altezza > 0 per evitare warning o artefatti
            if np.any(height_hatched > 0):
                ax.bar(
                    file_pos,
                    height_hatched,
                    bar_width,
                    color=bar_colors,  # Stesso colore di sfondo
                    edgecolor=gray_hatch_color,  # Colore delle righe diagonali
                    hatch='////',  # Hatch più denso
                    linewidth=0,  # Rimuove bordo esterno del rettangolo superiore (opzionale)
                    alpha=0.7,
                    label='_nolegend_'
                )

            # Opzionale: ridisegnare un bordo nero attorno all'intera barra (totale)
            # per dare un aspetto "unito"
            ax.bar(
                file_pos,
                total_heights,
                bar_width,
                color='none',  # Trasparente
                edgecolor='black',
                label='_nolegend_',
                alpha=0.7,
            )

        max_data_height = plot_df.max().max()

        if pd.notna(max_data_height):
            ax.set_ylim(0, max_data_height * 1.07)

        # ----------------------------
        # 6. Global mean line
        # ----------------------------
        global_mean = plot_df['Avg_All'].mean()
        ax.axhline(global_mean, linestyle='--', linewidth=2, color='black', zorder=3)

        # ----------------------------
        # 7. Labels over bars
        # ----------------------------
        # Avg All Labels
        fontsize = 7
        if scenario == "full_traversal":
            fontsize = 9
        elif scenario == "top_down" or scenario == "bottom_up":
            fontsize = 4

        for i, v in enumerate(plot_df['Avg_All']):
            if pd.notna(v):
                ax.text(agg_pos[i], v + 0.5, f'{v:.1f}', ha='center', rotation=45, fontsize=fontsize, fontweight='bold')

        # Per-File Labels
        for j in range(1, n_files + 1):
            file_pos = agg_pos + j * bar_width
            # Qui usiamo total_heights ricalcolato o preso dal df
            series_vals = plot_df[j].values
            for i, v in enumerate(series_vals):
                if pd.notna(v) and v > 0:
                    ax.text(file_pos[i], v + 0.2, f'{v:.1f}', ha='center', rotation=45, fontsize=fontsize)

        # ----------------------------
        # 8. Legend
        # ----------------------------
        equilibrium_legend = [
            Line2D([0], [0], color=WARM_CMAP(0.8), lw=4, label='Epoch avg Before Eq. (Warm)'),
            Line2D([0], [0], color=COOL_CMAP(0.8), lw=4, label='Epoch avg After Eq. (Cool)'),
            Line2D([0], [0], color=gray_colors[0], lw=4, label='Epoch avg Mixed (Gray)')
        ]

        file_legend_elements = []
        if show_if_remote and 'Is_Local' in full_df.columns:
            file_legend_elements.append(
                Rectangle((0, 0), 1, 1, facecolor='white', edgecolor=gray_hatch_color, hatch='////',
                          label='% Non-Local Execution')
            )

        legend_elements = equilibrium_legend + file_legend_elements + [
            Line2D([0], [0], color='black', lw=2, linestyle='--',
                   label=f'Global Mean: {global_mean:.2f} ms')
        ]

        ax.legend(
            handles=legend_elements,
            facecolor='white'
        )

        # ----------------------------
        # 9. Axis setup
        # ----------------------------
        ax.set_xlabel('Epoch number')
        ax.set_ylabel('Average Time (ms)')
        ax.set_xticks(x)
        ax.set_xticklabels(all_groups, rotation=0)

        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)

        plt.tight_layout()

        print(f"Analysis completed for {len(all_groups)} groups.")
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
        plt.xlabel('Epoch', fontsize=14)
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
