import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
    Custom Boxplot
    """
    try:
        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(14, 8))
        
        all_groups = sorted(list(set().union(*[df['Group'].unique() for df in dfs])))
        x = np.arange(len(all_groups))
        
        n_files = len(dfs)
        total_width = 0.8
        single_bar_width = total_width / n_files
        
        colors = plt.cm.Set1(np.linspace(0, 1, max(n_files, 3)))

        for i, df in enumerate(dfs):
            stats = []
            
            for group_id in all_groups:
                group_data = df[df['Group'] == group_id]
                
                if group_data.empty:
                    stats.append(None)
                    continue
                
                mean_total = group_data['Duration'].mean()
                
                local_data = group_data[group_data['Is_Local'] == True]
                mean_local = local_data['Duration'].mean() if not local_data.empty else np.nan
                
                remote_data = group_data[group_data['Is_Local'] == False]
                mean_remote = remote_data['Duration'].mean() if not remote_data.empty else np.nan
                
                stats.append({
                    'total': mean_total,
                    'local': mean_local,
                    'remote': mean_remote
                })
            
            pos = x + (i - (n_files - 1) / 2) * single_bar_width
            
            for idx, val in enumerate(stats):
                if val is None: continue
                
                m_loc = val['local']
                m_rem = val['remote']
                m_tot = val['total']
                
                current_x = pos[idx]
                
                if not np.isnan(m_loc) and not np.isnan(m_rem):
                    lower = min(m_loc, m_rem)
                    upper = max(m_loc, m_rem)
                    height = upper - lower
                    
                    ax.bar(current_x, height, bottom=lower, width=single_bar_width*0.9,
                           color=colors[i], alpha=0.4, edgecolor=colors[i], linewidth=1)
                    
                    ax.hlines(m_tot, current_x - single_bar_width*0.45, current_x + single_bar_width*0.45,
                              colors='black', linewidth=1.5)
                    
                elif not np.isnan(m_tot):
                    ax.hlines(m_tot, current_x - single_bar_width*0.4, current_x + single_bar_width*0.4,
                              colors=colors[i], linewidth=2, label='_nolegend_')
        
        from matplotlib.patches import Patch
        from matplotlib.lines import Line2D
        
        legend_elements = []
        
        for i in range(n_files):
            legend_elements.append(Patch(facecolor=colors[i], alpha=0.4, edgecolor=colors[i], label=f'File {i+1} Range (Local-Remote)'))
        
        legend_elements.append(Line2D([0], [0], color='black', lw=1.5, label='Global Average'))

        ax.legend(handles=legend_elements, loc='upper right')
        
        ax.set_title('Latency Gap: Local vs Remote (Box represents the spread)')
        ax.set_xlabel('Round Number')
        ax.set_ylabel('Average Latency (ms)')
        ax.set_xticks(x)
        ax.set_xticklabels(all_groups)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        return fig

    except Exception as e:
        print(f"Errore plotting latency: {e}")
        import traceback
        traceback.print_exc()
        return None

def plot_logs_avg_latency(dfs, eq_timestamp):
    """
    After knowing when it reaches equilibrium, use the client log to plot the results.
    """
    try:
        limit_ts = pd.to_datetime(eq_timestamp)

        full_df = pd.concat(dfs)

        avg = full_df.groupby('Group')['Duration'].mean()
        
        group_min_dates = full_df.groupby('Group')['StartTime'].min()
        
        colors = []
        highlight_color =  '#348ABD' # Blue (After Equilibrium)
        default_color = '#E24A33'    # Red (Before/Mixed)
        
        if limit_ts is None:
            colors = [default_color] * len(avg)
        else:
            for g in avg.index:
                if group_min_dates[g] > limit_ts:
                    colors.append(highlight_color)
                else:
                    colors.append(default_color)

        # 4. Plotting
        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(12, 6))
        
        avg.plot(
            kind='bar',
            color=colors,
            edgecolor='black',
            alpha=0.9,
            ax=ax,
            #title=f'Average Execution Time (Aggregated from {len(files)} files)'
        )
        
        global_mean = avg.mean()
        ax.axhline(global_mean, linestyle='--', linewidth=2, color='black')

        ax.set_xlabel('Round number', fontsize=12)
        ax.set_ylabel('Average Time (ms)', fontsize=12)
        plt.xticks(rotation=0, fontsize=10)
        plt.yticks(fontsize=10)

        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)

        for i, v in enumerate(avg):
            ax.text(i, v + 0.5, f'{v:.1f}', ha='center', fontsize=9)

        legend_elements = [
            Line2D([0], [0], color=default_color, lw=4, label='Average round time before Equilibrium'),
            Line2D([0], [0], color=highlight_color, lw=4, label='Average round time after Equilibrium'),
            Line2D([0], [0], color='black', lw=2, linestyle='--', label=f'Global Mean: {global_mean:.2f} ms')
        ]
        ax.legend(
            handles=legend_elements, 
            loc='lower center', 
            bbox_to_anchor=(0.5, 1.02), 
            ncol=3, 
            frameon=False
        )

        plt.tight_layout()
        
        # plt.show() # Decommenta se usi in locale interattivo
        
        print(f"Analysis completed for {len(avg)} groups using {len(dfs)} files.")
        print(f"Global average: {global_mean:.2f} ms")
        
        return avg

    except Exception as e:
        print(f"{e}")
        return None

n = 50 # Numero di funzioni per round
files = ['../data/results_log_54321_2025_11_19_17_40_57.csv', '../data/results_log_12345_2025_11_19_17_40_55.csv'] 

dfs = parse_dfs(files, n)

find_equilibrium_timestamp(dfs)
eq_timestamp = find_equilibrium_timestamp(dfs)
print(f"Equilibrium Timestamp: {eq_timestamp}")

plot_logs_avg_latency(dfs, eq_timestamp)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
plt.savefig(f'../output_img/execution_time_analysis_{timestamp}.png', dpi=300, bbox_inches='tight')

local_vs_remote_number_of_executions(dfs)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
plt.savefig(f'../output_img/local_vs_remote_executions_{timestamp}.png', dpi=300, bbox_inches='tight')

local_vs_remote_latency(dfs)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
plt.savefig(f'../output_img/local_vs_remote_latency_{timestamp}.png', dpi=300, bbox_inches='tight')

plt.show()