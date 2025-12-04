import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def local_vs_remote_number_of_executions(dfs, normalization: int):
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
            counts = counts / normalization

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
                        f'{height}',
                        ha='center', va='bottom', fontsize=9, color='#555555')

            bars_remote = ax.bar(pos_remote, remote_vals, single_bar_width, 
                                 color=colors[i], edgecolor='black', hatch='//', alpha=0.7, label=f'File {i+1} Remote')
            
            for bar in bars_remote:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height}',
                        ha='center', va='bottom', fontsize=9, color='#555555')

        # Estetica
        ax.set_title('Local vs Remote Executions per Epoch')
        ax.set_xlabel('Epoch Number')
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

def plot_heatmap_count_tasks(dfs, normalization: int):
    """
    Genera una heatmap che mostra il numero totale di esecuzioni (task)
    per ogni nodo di esecuzione (ExecHost) su ogni round (Group).
    (ExecHost sull'asse Y, Round sull'asse X)
    """

    try:
        df_combined = pd.concat(dfs, ignore_index=True)

        heatmap_data = df_combined.groupby(['Group', 'ExecHost']).size().reset_index(name='TaskCount')
        heatmap_data['TaskCount'] = heatmap_data['TaskCount'] / normalization  # Normalizzazione
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
        plt.xlabel('Epoch', fontsize=14)
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

