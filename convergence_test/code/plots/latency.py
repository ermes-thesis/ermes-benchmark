import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.patches import Rectangle


def plot_logs_avg_latency(dfs, scenario, domains, show_if_remote=True, max_rounds=7,
                          ax=None, draw_legend=True):
    """
    Plots the per-client average execution time for each epoch (grouped bars).
    - One bar group per epoch, one bar per client; the hatched portion of a bar
      is the fraction of requests served remotely.
    - Legend labels are 'Writer (Domain)' / 'Reader i (Domain)' or, in the
      conflict scenarios, 'Client i (Domain)'; the domain is resolved from the
      last octet of the client's EntryHost IP through the 'domains' dict.
    - The x-axis is limited to the first 'max_rounds' epochs.

    If 'ax' is given, the bars are drawn on it (no new figure is created) so the
    plot can be embedded in a multi-panel figure; 'draw_legend' toggles the
    per-axes legend. Returns (avg_all_files, legend_elements, max_data_height).
    """
    try:
        # Concatenate the per-client dataframes
        full_df = pd.concat(dfs, keys=range(1, len(dfs) + 1), names=['FileID', None])
        full_df = full_df.reset_index(level=0)

        avg_all_files = full_df.groupby('Group')['Duration'].mean().rename('Avg_All')
        avg_per_file = full_df.groupby(['Group', 'FileID'])['Duration'].mean().unstack(fill_value=np.nan)

        plot_df = pd.merge(avg_all_files, avg_per_file, left_index=True, right_index=True)

        # Keep only the first max_rounds epochs
        if max_rounds is not None and len(plot_df) > max_rounds:
            plot_df = plot_df.iloc[:max_rounds]
            print(f"Plot limited to the first {max_rounds} epochs.")

        all_groups = plot_df.index.tolist()
        n_files = len(dfs)

        # Fraction of remote executions per (epoch, client)
        if 'Is_Local' in full_df.columns:
            non_local_ratio = full_df.groupby(['Group', 'FileID'])['Is_Local'].apply(lambda x: (~x).mean()).unstack(fill_value=0)
        else:
            non_local_ratio = pd.DataFrame(0, index=plot_df.index, columns=avg_per_file.columns)

        # EntryHost of each client, used to build the legend labels
        host_map = {}
        if 'EntryHost' in full_df.columns:
            host_series = full_df.groupby('FileID')['EntryHost'].first()
            host_map = host_series.to_dict()

        # Okabe-Ito colorblind-safe palette; the first series (Writer) is blue
        okabe_ito = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7",
                     "#56B4E9", "#F0E442"]
        client_colors_palette = [okabe_ito[i % len(okabe_ito)] for i in range(n_files)]

        # White background, light horizontal gridlines only.
        # The replication scenario has more clients per epoch, so it is drawn wider.
        own_fig = ax is None
        if own_fig:
            fig_width = 10 if scenario == 'replication' else 6
            fig, ax = plt.subplots(figsize=(fig_width, 4))
            fig.patch.set_facecolor('white')

        ax.set_facecolor('white')
        ax.set_axisbelow(True)
        ax.grid(False)
        ax.yaxis.grid(True, color='#cccccc', linewidth=0.6, alpha=0.9, zorder=0)

        total_bars_in_group = n_files + 1
        bar_width = 0.9 / total_bars_in_group
        x = np.arange(len(all_groups))
        agg_pos = x - (total_bars_in_group / 2) * bar_width

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

            # Solid part (local executions)
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

            # Hatched part (remote executions)
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

            # Full-height outline
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

        max_data_height = plot_df.max().max()
        if pd.notna(max_data_height):
            ax.set_ylim(0, max_data_height * 1.1)

        # Legend
        client_legend_elements = []
        for i in range(n_files):
            file_id = i + 1

            host_name = host_map.get(file_id, "Unknown")
            try:
                # The last octet of the EntryHost IP is the key of the 'domains' dict
                ip_part = host_name.split(':')[0]
                last_octet = int(ip_part.split('.')[-1])
                domain = domains.get(last_octet, host_name)
            except:
                domain = host_name

            print(f"File {file_id} EntryHost: {host_name} -> {domain}")

            if i == 0 and "conflict" not in scenario:
                base_name = "Writer"
            else:
                if "conflict" in scenario:
                    base_name = f"Client {i + 1}"
                else:
                    base_name = f"Reader {i}"

            label_text = f"{base_name} ({domain})"

            client_legend_elements.append(
                Patch(facecolor=client_colors_palette[i], edgecolor='black', label=label_text)
            )

        remote_legend_elements = []
        if show_if_remote and 'Is_Local' in full_df.columns:
            remote_legend_elements.append(
                Rectangle((0, 0), 1, 1, facecolor='white', edgecolor=gray_hatch_color, hatch='////',
                          label='Remote access')
            )

        legend_elements = client_legend_elements + remote_legend_elements

        if draw_legend:
            ax.legend(
                handles=legend_elements,
                facecolor='white',
                edgecolor='gray',
                loc='best'
            )

        # Axes
        ax.set_xlabel('Epoch number', fontsize=16)
        if own_fig:
            ax.set_ylabel('Latency (ms)', fontsize=16)
        ax.set_xticks(x)
        ax.set_xticklabels(all_groups, rotation=0)
        ax.tick_params(axis='both', labelsize=14)

        # Left/bottom spines only, in light gray
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['left', 'bottom']:
            ax.spines[spine].set_color('#888888')

        if own_fig:
            plt.tight_layout()
        print(f"Analysis completed for {len(all_groups)} groups.")
        return avg_all_files, legend_elements, max_data_height

    except Exception as e:
        print(f"Error while plotting: {e}")
        import traceback
        traceback.print_exc()
        return None
