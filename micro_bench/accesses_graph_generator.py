import inspect
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Disable pycache generation
sys.dont_write_bytecode = True

# Input: density summaries (Fig. 12), latency vs number of state operations.
data_rel_path = 'data/variable_accesses'
output_dir_name = 'output_img/variable_accesses'
output_filename = 'global_comparison.png'

X_AXIS_COL = "Accesses"

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
MODE_STYLE = {
    "sequential": "-",
    "eventual": "--",
}

LABEL_FONTSIZE = 16
TICK_FONTSIZE = 14


def plot_global_comparison(input_dir, save_path):
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor('white')

    for csv_name, arch_label in SERIES:
        csv_path = input_dir / csv_name
        if not csv_path.exists():
            print(f"⚠️ File not found, series skipped: {csv_path}")
            continue

        df = pd.read_csv(csv_path)
        if X_AXIS_COL not in df.columns or 'Mode' not in df.columns:
            print(f"⚠️ Skipping {csv_name}: missing columns.")
            continue

        style = ARCH_STYLE[arch_label]

        for mode, linestyle in MODE_STYLE.items():
            sub = df[df['Mode'] == mode].copy()
            if sub.empty:
                continue
            sub = sub.sort_values(X_AXIS_COL)

            ax.plot(sub[X_AXIS_COL].astype(int), sub['AverageLatency'].astype(float),
                    marker=style["marker"], linestyle=linestyle, color=style["color"],
                    linewidth=2, markersize=4, label=f"{arch_label} [{mode}]")

        print(f"  ✅ Loaded: {csv_name} ({arch_label})")

    ax.set_xlabel("Number of operations", fontsize=LABEL_FONTSIZE)
    ax.set_ylabel("Latency (ms)", fontsize=LABEL_FONTSIZE)
    ax.set_ylim(bottom=0)
    ax.tick_params(axis='both', labelsize=TICK_FONTSIZE)

    ax.set_facecolor('white')
    ax.yaxis.grid(True, color='#cccccc', linewidth=0.6)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color('#333333')

    ax.legend(loc='best', framealpha=0.9,
              handlelength=3, handletextpad=1)

    fig.tight_layout()
    fig.savefig(save_path, dpi=300, facecolor='white')
    pdf_path = Path(save_path).with_suffix('.pdf')
    fig.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    print(f"\n✅ Plot saved to: {save_path}")
    print(f"✅ Plot saved to: {pdf_path}")


def main():
    current_file_path = inspect.getfile(inspect.currentframe())
    base_dir = Path(current_file_path).parent

    input_dir = (base_dir / data_rel_path).resolve()
    output_dir = (base_dir / output_dir_name).resolve()

    print(f"Reading CSVs from: {input_dir}")

    if not input_dir.exists():
        print("❌ Input directory not found.")
        exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    plot_global_comparison(input_dir, output_dir / output_filename)


if __name__ == "__main__":
    main()
