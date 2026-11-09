import inspect
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Disable pycache generation
sys.dont_write_bytecode = True

import config
import data_processor
from plots import latency

# Panels shown side by side (scenario folder -> panel title)
PANELS = [
    ("conflict_1", "Sequential consistency"),
    ("conflict_eventual", "Eventual consistency"),
]
OUTPUT_SUBDIR = "conflict_combined"
OUTPUT_NAME = "execution_time_analysis_combined"


def load_scenario(base_dir, scenario):
    """Aggregate every run (zip not prefixed with '_') of one scenario into the
    per-client dataframes, exactly as code/main.py does for a single scenario."""
    data_dir_path = (base_dir / config.data_dir / scenario).resolve()
    files = sorted(f for f in data_dir_path.glob("*.zip") if not f.name.startswith("_"))

    full_dfs = []
    for f in files:
        csv, log = data_processor.process_zip_files(f)
        parsed_log = data_processor.parse_log(log)
        dfs = data_processor.parse_dfs(csv, parsed_log)
        if not full_dfs:
            full_dfs = dfs
        else:
            limit = min(len(full_dfs), len(dfs))
            for i in range(limit):
                full_dfs[i] = pd.concat([full_dfs[i], dfs[i]], ignore_index=True)
    return full_dfs


def main():
    base_dir = Path(inspect.getfile(inspect.currentframe())).parent

    # Independent y-axes: each panel keeps its own latency scale (set inside
    # plot_logs_avg_latency), so their y-tick values may differ.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.patch.set_facecolor('white')

    handles = None

    for ax, (scenario, title) in zip(axes, PANELS):
        dfs = load_scenario(base_dir, scenario)
        if not dfs:
            print(f"WARNING: no data for {scenario}, skipping panel.")
            continue

        result = latency.plot_logs_avg_latency(
            dfs, scenario, config.domains, max_rounds=6, ax=ax, draw_legend=False)
        if result is None:
            print(f"WARNING: plotting failed for {scenario}.")
            continue
        _, legend_elements, _ = result

        handles = legend_elements  # identical across the two conflict scenarios
        ax.set_title(title, fontsize=16)

    # A single y-axis label (on the left panel); each panel shows its own ticks
    axes[0].set_ylabel('Latency (ms)', fontsize=16)

    fig.tight_layout()

    # Single shared legend on top
    if handles:
        fig.legend(handles=handles, loc='upper center', ncol=len(handles),
                   frameon=True, facecolor='white', edgecolor='gray',
                   fontsize=12, bbox_to_anchor=(0.5, 1.08))

    out_dir = (base_dir / config.out_dir / OUTPUT_SUBDIR).resolve()
    (out_dir / "pdf").mkdir(parents=True, exist_ok=True)

    png_path = out_dir / f"{OUTPUT_NAME}.png"
    pdf_path = out_dir / "pdf" / f"{OUTPUT_NAME}.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    print(f"Done. Combined figure saved to:\n  {png_path}\n  {pdf_path}")


if __name__ == "__main__":
    main()
