import inspect
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from scipy import stats

# Disable pycache generation
sys.dont_write_bytecode = True

# Input: steady-state summaries of the full scalability sweep (Fig. 11).
# Output: a single 2x2 figure (Ermes / Cloud-Data x Eventual / Sequential).
DATA_DIR = 'data/scalability'
OUTPUT_DIR = 'output_img/scalability'
OUTPUT_NAME = 'steady_state_scalability'

# Columns of the figure (one configuration each), in left-to-right order
CONFIGS = [
    ("Ermes", "distributed_steady_state.csv"),
    ("Cloud-Data", "centralized_steady_state.csv"),
    ("Cloud-Only", "cloud_only_steady_state.csv"),
]
# Rows of the figure (one consistency mode each): Sequential on top, Eventual below
ROW_MODES = [("sequential", "Sequential"), ("eventual", "Eventual")]

# Okabe-Ito colorblind-safe palette (same as the RQ1 figures)
PALETTE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442"]

LABEL_FONTSIZE = 16
TICK_FONTSIZE = 10
TITLE_FONTSIZE = 16
LEGEND_FONTSIZE = 14


def compute_confidence_intervals_from_summary(df, confidence=95):
    """Recompute the CI on AverageLatency from Variance and N (CorrectRequests)."""
    ci_data = {}
    alpha = 1 - confidence / 100.0

    if df.empty:
        return {}

    for collections in df['Collections'].unique():
        collections = int(collections)
        ci_data[collections] = {}

        subset = df[df['Collections'] == collections]

        for _, row in subset.iterrows():
            users = int(row['Users'])

            mean = row.get("AverageLatency", 0)
            variance = row.get("VarianceLatency", 0)
            n = int(row.get("CorrectRequests", 0))

            if n < 2:
                continue

            std = np.sqrt(variance)
            sem = std / np.sqrt(n)
            t_crit = stats.t.ppf(1 - alpha / 2, df=n - 1)

            ci_data[collections][users] = {
                "mean": mean,
                "ci_lower": mean - t_crit * sem,
                "ci_upper": mean + t_crit * sem,
                "n_samples": n,
            }

    return ci_data


def print_confidence_intervals(ci_data, config_name, mode_name, confidence=95,
                               max_rel_error_ok=0.25, max_rel_error_weak=0.50):
    print("\n" + "=" * 80)
    print(f" [{config_name} | {mode_name.upper()}] CI {confidence}% on AverageLatency")
    print("=" * 80)

    if not ci_data:
        print("Not enough data to compute CIs.")
        return

    for collections in sorted(ci_data.keys()):
        print(f"▶ Collections: {collections}")
        for users in sorted(ci_data[collections].keys()):
            r = ci_data[collections][users]
            mean, lower, upper, n = r["mean"], r["ci_lower"], r["ci_upper"], r["n_samples"]
            rel_error = (upper - lower) / (2 * mean) if mean != 0 else 0

            if lower < 0 or rel_error > max_rel_error_weak:
                status = "❌ INVALID"
            elif rel_error > max_rel_error_ok:
                status = "⚠️ WEAK"
            else:
                status = "✅ OK"

            print(f"  Users: {users:>5} | mean = {mean:8.3f} ms | "
                  f"CI{confidence}% = [{lower:8.3f}, {upper:8.3f}] | "
                  f"rel.err = {rel_error*100:6.1f}% | n = {n:>2} | {status}")
        print()


def plot_panel(ax, df_mode, metric="AverageLatency", yscale='linear'):
    """One panel: latency (avg or median) vs users, one line per collections
    count, IQR band (Q1-Q3) plus Q1/Q3 whisker ticks. yscale is 'linear' or
    'log' (for the Latency axis)."""
    collections_list = sorted(int(c) for c in df_mode['Collections'].unique())

    for i, collections in enumerate(collections_list):
        subset = df_mode[df_mode['Collections'] == collections].sort_values('Users')
        if subset.empty:
            continue

        xs = subset['Users'].astype(int).to_numpy()
        vals = subset[metric].astype(float).to_numpy()
        q1 = subset['Q1'].astype(float).to_numpy()
        q3 = subset['Q3'].astype(float).to_numpy()

        color = PALETTE[i % len(PALETTE)]
        ax.fill_between(xs, q1, q3, alpha=0.18, color=color)
        ax.plot(xs, vals, marker="o", linewidth=2, color=color, label=f"{collections}")

        tick_len = (xs.max() - xs.min()) * 0.015 if len(xs) > 1 else 1
        ax.hlines(q1, xs - tick_len, xs + tick_len, linewidth=2, color=color)
        ax.hlines(q3, xs - tick_len, xs + tick_len, linewidth=2, color=color)

    if yscale == 'log':
        ax.set_yscale('log')
        # Plain numeric labels (e.g. 1.5, 2, 25, 30) instead of "x 10^n"
        plain = FuncFormatter(lambda v, _: f"{v:g}")
        ax.yaxis.set_major_formatter(plain)
        ax.yaxis.set_minor_formatter(plain)
        # Keep major (powers of ten) and minor tick labels the same size
        ax.tick_params(axis='y', which='minor', labelsize=TICK_FONTSIZE)
    else:
        ax.set_ylim(bottom=0)
    ax.set_facecolor('white')
    ax.yaxis.grid(True, color='#cccccc', linewidth=0.6)
    if yscale == 'log':
        # also show the minor decade gridlines on a log axis
        ax.yaxis.grid(True, which='minor', color='#eeeeee', linewidth=0.5)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color('#333333')
    ax.tick_params(labelsize=TICK_FONTSIZE)


def _load_configs(data_dir):
    """Read the per-configuration steady-state CSVs once."""
    dfs = {}
    for config_name, csv_name in CONFIGS:
        csv_path = data_dir / csv_name
        if not csv_path.exists():
            print(f"ERROR: missing input file {csv_path}")
            exit(1)
        dfs[config_name] = pd.read_csv(csv_path)
    return dfs


def make_figure(data_dir, output_dir, metric, output_name, print_ci=False,
                yscale='linear'):
    """2-row x 3-column grid: rows are the consistency modes (Sequential on top,
    Eventual below), columns are the three configurations."""
    dfs = _load_configs(data_dir)
    legend_source_ax = None

    n_rows, n_cols = len(ROW_MODES), len(CONFIGS)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6 * n_cols, 4 * n_rows))
    fig.patch.set_facecolor('white')

    for r, (mode_key, mode_label) in enumerate(ROW_MODES):
        for c, (config_name, _csv) in enumerate(CONFIGS):
            ax = axes[r][c]
            df_mode = dfs[config_name][dfs[config_name]['Mode'] == mode_key].copy()
            if df_mode.empty:
                print(f"WARNING: no '{mode_key}' rows for {config_name}")
                continue
            if print_ci:
                ci = compute_confidence_intervals_from_summary(df_mode)
                print_confidence_intervals(ci, config_name, mode_key)

            plot_panel(ax, df_mode, metric=metric, yscale=yscale)
            ax.set_title(f"{config_name} — {mode_label}", fontsize=TITLE_FONTSIZE)
            if r == n_rows - 1:
                ax.set_xlabel("Users", fontsize=LABEL_FONTSIZE)
            if c == 0:
                ax.set_ylabel("Latency (ms)", fontsize=LABEL_FONTSIZE)
            if legend_source_ax is None:
                legend_source_ax = ax

    legend_rect_top = 0.93

    # Single shared legend on top
    handles, labels = legend_source_ax.get_legend_handles_labels()
    fig.legend(handles, labels, title="Number of collections",
               loc='upper center', ncol=4, frameon=False,
               fontsize=LEGEND_FONTSIZE, title_fontsize=LEGEND_FONTSIZE,
               bbox_to_anchor=(0.5, 1.0))

    fig.tight_layout(rect=[0, 0, 1, legend_rect_top])

    png_path = output_dir / f"{output_name}.png"
    pdf_path = output_dir / f"{output_name}.pdf"
    fig.savefig(png_path, dpi=300, facecolor='white', bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    print(f"\n✅ Figure saved: {png_path}")
    print(f"✅ Figure saved: {pdf_path}")


def main():
    base_dir = Path(inspect.getfile(inspect.currentframe())).parent
    data_dir = (base_dir / DATA_DIR).resolve()
    output_dir = (base_dir / OUTPUT_DIR).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Paper figure: average latency, linear axes (CI printed once here)
    make_figure(data_dir, output_dir, "AverageLatency", OUTPUT_NAME, print_ci=True)
    # Alternative version: median latency, logarithmic Latency (y) axis
    make_figure(data_dir, output_dir, "MedianLatency", f"{OUTPUT_NAME}_median",
                yscale='log'
                )


if __name__ == "__main__":
    main()
