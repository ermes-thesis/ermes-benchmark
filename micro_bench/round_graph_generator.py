import os
import sys

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator

# Disable pycache generation
sys.dont_write_bytecode = True

# Explicit input files -> paper series (order = legend order).
SERIES = [
    ("distributed.csv", "Ermes"),
    ("centralized.csv", "Cloud-Data"),
    ("cloud_only.csv", "Cloud-Only"),
]

# Okabe-Ito colorblind-safe palette (same as the RQ1 figures)
ARCH_STYLE = {
    "Ermes":      {"color": "#0072B2", "marker": "^"},
    "Cloud-Data": {"color": "#E69F00", "marker": "o"},
    "Cloud-Only": {"color": "#009E73", "marker": "s"},
}

LABEL_FONTSIZE = 16
TICK_FONTSIZE = 14


def process_scenario(scenario_name, base_input_dir, base_output_dir, filters=None,
                     legend_kwargs=None, yscale='linear', output_suffix=''):
    """Process one scenario ('static_users' -> Fig. 13, 'moving_users' -> Fig. 14):
    one latency-vs-epoch chart per (Users, Collections) combination.

    legend_kwargs overrides the matplotlib legend placement/appearance
    (defaults to an automatically-placed legend).
    yscale sets the y-axis scale ('linear' or 'log').
    output_suffix is appended to the output file name (e.g. '_log')."""
    if legend_kwargs is None:
        legend_kwargs = dict(loc='best')

    input_dir = os.path.join(base_input_dir, scenario_name)
    output_dir = os.path.join(base_output_dir, scenario_name)

    print(f"\n--- Processing scenario: {scenario_name} ---")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")

    os.makedirs(output_dir, exist_ok=True)

    # Load only the canonical files of the three configurations
    all_data = []
    for fname, arch_label in SERIES:
        file_path = os.path.join(input_dir, fname)

        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                df['Architecture'] = arch_label
                all_data.append(df)
                print(f"  ✅ Loaded: {fname} ({arch_label})")
            except Exception as e:
                print(f"  ❌ Error reading {fname}: {e}")
        else:
            print(f"  ⚠️ File not found: {fname}")

    if not all_data:
        print(f"  No data found for {scenario_name}. Skipping.")
        return

    full_df = pd.concat(all_data, ignore_index=True)

    # Apply AND filters
    if filters:
        mask = pd.Series(True, index=full_df.index)
        for col, expected_value in filters.items():
            if col not in full_df.columns:
                print(f"  ⚠️ Filter column not found: {col}")
                continue
            if isinstance(expected_value, (list, tuple, set)):
                mask &= full_df[col].isin(expected_value)
            else:
                mask &= full_df[col] == expected_value
        full_df = full_df[mask]

        if full_df.empty:
            print("  ⚠️ Empty dataset after filtering.")
            return

    # Cap the number of rounds
    if scenario_name == 'moving_users':
        full_df = full_df[full_df['Round'] <= 20]
    else:
        full_df = full_df[full_df['Round'] <= 10]

    required_cols = ['Users', 'Collections', 'Round', 'AverageLatency', 'Mode']
    if not all(col in full_df.columns for col in required_cols):
        print("  ❌ Error: missing columns in the CSV.")
        return

    # Group and plot
    grouped_configs = full_df.groupby(['Users', 'Collections'])
    count = 0

    for (users, collections), group_df in grouped_configs:
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('white')

        has_plotted = False

        for (arch, mode), sub_df in group_df.groupby(['Architecture', 'Mode']):
            if sub_df.empty:
                continue
            sub_df = sub_df.sort_values('Round')

            style = ARCH_STYLE.get(arch, {"color": "tab:gray", "marker": "d"})

            mode_str = str(mode).lower()
            if 'sequential' in mode_str:
                linestyle = '-'
            elif 'eventual' in mode_str:
                linestyle = '--'
            else:
                linestyle = ':'

            ax.plot(sub_df['Round'], sub_df['AverageLatency'],
                    label=f"{arch} [{mode_str}]", color=style["color"],
                    marker=style["marker"], linestyle=linestyle,
                    linewidth=2, markersize=6)
            has_plotted = True

        if has_plotted:
            ax.set_xlabel('Epoch', fontsize=LABEL_FONTSIZE)
            ax.set_ylabel('Latency (ms)', fontsize=LABEL_FONTSIZE)
            ax.tick_params(axis='both', labelsize=TICK_FONTSIZE)
            if yscale == 'log':
                ax.set_yscale('log')

            ax.set_facecolor('white')
            ax.yaxis.grid(True, color='#cccccc', linewidth=0.6)
            if yscale == 'log':
                # also show the minor decade gridlines on a log axis
                ax.yaxis.grid(True, which='minor', color='#eeeeee', linewidth=0.5)
            ax.xaxis.grid(False)
            ax.set_axisbelow(True)
            for spine in ax.spines.values():
                spine.set_color('#333333')

            ax.legend(handlelength=3, **legend_kwargs)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            fig.tight_layout()

            # bbox_inches='tight' keeps a legend placed outside the axes in frame
            base = f"u{users}_c{collections}{output_suffix}"
            fig.savefig(os.path.join(output_dir, f"{base}.png"),
                        dpi=300, facecolor='white', bbox_inches='tight')
            fig.savefig(os.path.join(output_dir, f"{base}.pdf"),
                        bbox_inches='tight', facecolor='white')
            count += 1

        plt.close(fig)

    print(f"  ✅ Generated {count} figure(s) in {output_dir}")


def main():
    base_data_dir = "data/rounds"
    base_out_dir = "output_img/rounds"

    # Fig. 13: temporal evolution with static users, u1024/c1000 configuration.
    process_scenario("static_users", base_data_dir, base_out_dir,
                     filters={"Users": 1024, "Collections": 1000})

    # Fig. 14: moving users (u64/c1000, the only combination present).
    # The legend sits inside, in the free upper-right area above the Cloud
    # lines, slightly smaller so it does not overlap the curves.
    moving_legend = dict(loc='upper right', fontsize=10,
                         title_fontsize=11, framealpha=0.9)
    process_scenario("moving_users", base_data_dir, base_out_dir,
                     legend_kwargs=moving_legend)
    # Log-scale variant (separate file, does not overwrite the linear one).
    process_scenario("moving_users", base_data_dir, base_out_dir,
                     legend_kwargs=moving_legend, yscale='log', output_suffix='_log')


if __name__ == "__main__":
    main()
