import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.patches import Rectangle


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

        cmap = plt.get_cmap('tab10')
        colors = [cmap(i % 10) for i in range(n_files)]
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

def local_vs_remote_latency_violin_old(dfs):
    """
    Violin Plot personalizzato con Min, Max, Avg, Avg Local e Avg Remote.
    """
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(12, 7))

    n_files = len(dfs)
    x = np.arange(n_files)
    cmap = plt.get_cmap('tab10')
    colors = [cmap(i % 10) for i in range(n_files)]
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
        # Line2D([0], [0], color='grey', lw=1.5, linestyle=':', label='Min/Max (Vertical Line)'),
    ]
    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, 1.05), ncol=4, frameon=False,
              fontsize=10)

    # ax.set_title('User Latency Analysis: Violin Plot con Distribuzione e Valori Statistici')
    ax.set_xlabel('User')
    ax.set_ylabel('Latency (ms)')
    ax.set_xticks(x)
    ax.set_xticklabels(file_labels)

    plt.tight_layout()
    return fig

def local_vs_remote_latency_violin(dfs, scenario, domains):
    """
    Violin Plot personalizzato con Min, Max, Avg, Avg Local e Avg Remote.
    Include la risoluzione dei domini nella legenda e nelle etichette.
    """
    plt.style.use('ggplot')

    if "conflict" in scenario:
        fig, ax = plt.subplots(figsize=(6, 5))
    else:
        fig, ax = plt.subplots(figsize=(8, 5))

    n_files = len(dfs)
    x = np.arange(n_files)
    cmap = plt.get_cmap('tab10')
    colors = [cmap(i % 10) for i in range(n_files)]

    # ---------------------------------------------------------
    # 1. LOGICA ETICHETTE BASE (Scenario-based)
    # ---------------------------------------------------------
    base_labels = [f'User {i + 1}' for i in range(n_files)]

    if scenario == "bottom_up":
        # Assicuriamoci che la lista abbia la lunghezza giusta per evitare errori
        custom_labels = ["Doctor", "Patient 1", "Patient 2", "Patient 3", "Patient 4", "Patient 5"]
        base_labels = custom_labels[:n_files]
    elif scenario == "full_traversal":
        base_labels = ["Patient", "Doctor"]
    elif scenario == "conflict_1" or scenario == "conflict_eventual":
        base_labels = ["Doctor 1", "Doctor 2"]
    elif scenario == "replication":
        base_labels = ["Patient", "Doctor 1", "Doctor 2", "Doctor 3", "Doctor 4"]

    # ---------------------------------------------------------
    # 2. RISOLUZIONE DOMINI E CREAZIONE ETICHETTE FINALI
    # ---------------------------------------------------------
    final_labels = []

    for i, df in enumerate(dfs):
        # Estrai EntryHost (prendi il primo valore non nullo o la stringa vuota)
        host_name = "Unknown"
        if 'EntryHost' in df.columns and not df['EntryHost'].dropna().empty:
            host_name = df['EntryHost'].dropna().iloc[0]

        # Risolvi Dominio usando il dizionario 'domains' e l'ultimo ottetto IP
        try:
            ip_part = host_name.split(':')[0]
            last_octet = int(ip_part.split('.')[-1])
            domain = domains.get(last_octet, host_name)
        except:
            domain = host_name

        # Combina Nome Base + Dominio
        base_name = base_labels[i] if i < len(base_labels) else f"User {i+1}"
        final_labels.append(f"{base_name}\n({domain})")

    # ---------------------------------------------------------
    # 3. CALCOLO DATI E STATISTICHE
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # 4. PLOTTING VIOLIN
    # ---------------------------------------------------------
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
        # b.set_edgecolor('black')

    # Logica disegno linee (Min, Max, Avg, ecc)
    # Ho unificato i due blocchi if/else del tuo codice originale per pulizia,
    # mantenendo la logica di visualizzazione.
    for i, stat in enumerate(stats):
        current_x = x[i]
        user_color = colors[i]

        # Larghezza linee orizzontali
        hw = 0.15 # half width

        # Min e Max
        ax.vlines(current_x, stat['min'], stat['max'], color=user_color, linestyle=':', linewidth=1.5)
        ax.hlines(stat['min'], current_x - hw, current_x + hw, color=user_color, linewidth=1)
        ax.hlines(stat['max'], current_x - hw, current_x + hw, color=user_color, linewidth=1)

        # Avg totale (Linea Nera Solida)
        ax.hlines(stat['avg'], current_x - hw, current_x + hw, color='black', linewidth=2)

        # Avg Local (Linea Tratteggiata --)
        if not np.isnan(stat['avg_local']) and abs(stat['avg_local'] - stat['avg']) > 0.1:
            ax.hlines(stat['avg_local'], current_x - hw, current_x + hw,
                      color=user_color, linestyle='--', linewidth=2)

        # Avg Remote (Linea Punto-Tratto -.)
        if not np.isnan(stat['avg_remote']) and abs(stat['avg_remote'] - stat['avg']) > 0.1:
            ax.hlines(stat['avg_remote'], current_x - hw, current_x + hw,
                      color=user_color, linestyle='-.', linewidth=2)

    # ---------------------------------------------------------
    # 5. COSTRUZIONE LEGENDA COMPLETA
    # ---------------------------------------------------------

    # Parte A: Identificazione Client (Colore -> Nome + Dominio)
    client_legend_patches = []
    for i in range(n_files):
        # Ripuliamo la label per la legenda (rimuoviamo il new line se presente per estetica)
        label_clean = final_labels[i].replace('\n', ' ')
        client_legend_patches.append(
            Patch(facecolor=colors[i], edgecolor='black', alpha=0.6, label=label_clean)
        )

    # Parte B: Significato Linee Statistiche
    stats_legend_lines = [
        Line2D([0], [0], color='black', lw=2, label='Global average'),
        Line2D([0], [0], color='grey', lw=2, linestyle='--', label='Local executions average'),
        Line2D([0], [0], color='grey', lw=2, linestyle='-.', label='Remote executions average'),
    ]

    # Unione Legende
    full_legend = stats_legend_lines

    ax.legend(
        handles=full_legend,
        loc='best',
        edgecolor='gray',
        facecolor='white',
    )

    # ---------------------------------------------------------
    # 6. AXIS SETUP
    # ---------------------------------------------------------
    ax.set_ylabel('Latency (ms)')
    ax.set_xticks(x)
    # Usiamo le label con il dominio anche sull'asse X
    ax.set_xticklabels(final_labels)

    plt.tight_layout()
    return fig





def plot_logs_avg_latency(dfs, scenario, domains, show_if_remote=True, max_rounds=7):
    """
    Plots the average per file using 'tab10' colormap.
    Legend logic: 'Patient (Domain)' and 'Doctor X (Domain)'.
    - Includes Global Average Line.
    - Limits x-axis to 'max_rounds'.
    - Parses EntryHost IP to find domain name using 'domains' dict.
    """
    try:
        # 1. Concatenate all files
        full_df = pd.concat(dfs, keys=range(1, len(dfs) + 1), names=['FileID', None])
        full_df = full_df.reset_index(level=0)

        # Calcolo medie
        avg_all_files = full_df.groupby('Group')['Duration'].mean().rename('Avg_All')
        avg_per_file = full_df.groupby(['Group', 'FileID'])['Duration'].mean().unstack(fill_value=np.nan)

        plot_df = pd.merge(avg_all_files, avg_per_file, left_index=True, right_index=True)

        # ----------------------------
        # FILTRO: TAGLIO AI PRIMI N ROUND
        # ----------------------------
        if max_rounds is not None and len(plot_df) > max_rounds:
            plot_df = plot_df.iloc[:max_rounds]
            print(f"Plot limitato ai primi {max_rounds} round.")

        all_groups = plot_df.index.tolist()
        n_files = len(dfs)

        # ----------------------------
        # PRE-CALCOLO RATIO NON-LOCAL
        # ----------------------------
        if 'Is_Local' in full_df.columns:
            non_local_ratio = full_df.groupby(['Group', 'FileID'])['Is_Local'].apply(lambda x: (~x).mean()).unstack(fill_value=0)
        else:
            non_local_ratio = pd.DataFrame(0, index=plot_df.index, columns=avg_per_file.columns)

        # ----------------------------
        # ESTRAZIONE ENTRY HOST PER LA LEGENDA
        # ----------------------------
        host_map = {}
        if 'EntryHost' in full_df.columns:
            host_series = full_df.groupby('FileID')['EntryHost'].first()
            host_map = host_series.to_dict()

        # ----------------------------
        # 2. DEFINIZIONE COLORI (TAB10)
        # ----------------------------
        cmap = plt.get_cmap("tab10")
        client_colors_palette = [cmap(i % 10) for i in range(n_files)]

        # ----------------------------
        # 3. Setup Plot
        # ----------------------------
        plt.style.use('ggplot')
        if "conflict" in scenario:
            fig, ax = plt.subplots(figsize=(6, 5))
        else:
            fig, ax = plt.subplots(figsize=(8, 5))

        total_bars_in_group = n_files + 1
        bar_width = 0.9 / total_bars_in_group
        x = np.arange(len(all_groups))
        agg_pos = x - (total_bars_in_group / 2) * bar_width

        # ----------------------------
        # 5. Per-file bars
        # ----------------------------
        gray_hatch_color = (0.2, 0.2, 0.2, 0.5)

        for j in range(1, n_files + 1):
            file_pos = agg_pos + j * bar_width
            this_client_color = client_colors_palette[j-1]

            total_heights = []
            ratios = []

            for g in all_groups:
                h = plot_df.loc[g, j]
                if g in non_local_ratio.index:
                    r = non_local_ratio.loc[g, j] if j in non_local_ratio.columns else 0
                else:
                    r = 0

                if pd.isna(h): h = 0
                if pd.isna(r): r = 0
                total_heights.append(h)
                ratios.append(r)

            total_heights = np.array(total_heights)
            ratios = np.array(ratios)

            if show_if_remote:
                height_hatched = total_heights * ratios
                height_solid = total_heights - height_hatched
            else:
                height_hatched = np.zeros_like(total_heights)
                height_solid = total_heights

            bar_colors = [this_client_color] * len(all_groups)

            # Solid part (Local)
            ax.bar(
                file_pos,
                height_solid,
                bar_width,
                bottom=height_hatched,
                color=bar_colors,
                edgecolor='black',
                alpha=0.85,
                label='_nolegend_'
            )

            # Hatched part (Remote)
            if np.any(height_hatched > 0):
                ax.bar(
                    file_pos,
                    height_hatched,
                    bar_width,
                    color=bar_colors,
                    edgecolor=gray_hatch_color,
                    hatch='////',
                    linewidth=0,
                    alpha=0.85,
                    label='_nolegend_'
                )

            # Bordo totale
            ax.bar(
                file_pos,
                total_heights,
                bar_width,
                color='none',
                edgecolor='black',
                label='_nolegend_',
                alpha=1,
                linewidth=0.7
            )

        # ----------------------------
        # 6. LINEA MEDIA GLOBALE
        # ----------------------------
        # ax.plot(
        #     x,
        #     plot_df['Avg_All'],
        #     color='black',
        #     marker='',
        #     markersize=6,
        #     linestyle='--',
        #     linewidth=2,
        #     label='_nolegend_',
        #     zorder=10
        # )

        max_data_height = plot_df.max().max()
        if pd.notna(max_data_height):
            ax.set_ylim(0, max_data_height * 1.1)

        # ----------------------------
        # 8. Legend Setup
        # ----------------------------
        client_legend_elements = []
        for i in range(n_files):
            file_id = i + 1

            # --- TUA LOGICA DI MAPPING ---
            host_name = host_map.get(file_id, "Unknown")
            try:
                # Estrae l'ultimo ottetto dell'IP per usarlo come chiave in 'domains'
                ip_part = host_name.split(':')[0]
                last_octet = int(ip_part.split('.')[-1])
                domain = domains.get(last_octet, host_name) # Usa host_name se l'ottetto non è in domains
            except:
                domain = host_name

            print(f"File {file_id} EntryHost: {host_name} -> {domain}")
            # -----------------------------

            if i == 0 and "conflict" not in scenario:
                base_name = "Patient"
            else:
                if "conflict" in scenario:
                    base_name = f"Doctor {i + 1}"
                else:
                    base_name = f"Doctor {i}"

            label_text = f"{base_name} ({domain})"

            client_legend_elements.append(
                Patch(facecolor=client_colors_palette[i], edgecolor='black', label=label_text)
            )

        # Elemento Remote
        remote_legend_elements = []
        if show_if_remote and 'Is_Local' in full_df.columns:
            remote_legend_elements.append(
                Rectangle((0, 0), 1, 1, facecolor='white', edgecolor=gray_hatch_color, hatch='////',
                          label='% Non-Local Execution')
            )

        # Elemento Linea Media
        # avg_line_legend = [
        #     Line2D([0], [0], color='black', marker='',linestyle='--', lw=2, label='Global Avg per Round')
        # ]

        legend_elements = client_legend_elements + remote_legend_elements #+ avg_line_legend

        ax.legend(
            handles=legend_elements,
            facecolor='white',
            edgecolor='gray',
            loc='best'
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
