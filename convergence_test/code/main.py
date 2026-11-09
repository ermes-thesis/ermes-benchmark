import argparse
import inspect
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Disable pycache generation
sys.dont_write_bytecode = True

# Custom modules
import config
import data_processor
from plots import latency


def main():
    # ==========================================
    # 0. Parse Command Line Arguments
    # ==========================================
    parser = argparse.ArgumentParser(description="Analyze trace logs from ZIP files.")
    parser.add_argument(
        "subfolder",
        nargs="?",
        default="",
        help="Subfolder name for input (inside data_dir) and output (inside out_dir)"
    )
    args = parser.parse_args()

    # ==========================================
    # 1. Setup Paths and Output Directory
    # ==========================================

    # Determine the directory where main.py is located
    current_file_path = inspect.getfile(inspect.currentframe())
    base_dir = Path(current_file_path).parent

    # Resolve input directory using config AND subfolder argument
    data_dir_path = (base_dir / config.data_dir / args.subfolder).resolve()

    print(f"Searching for ZIP files in: {data_dir_path}")

    if not data_dir_path.exists():
        print(f"ERROR: Directory {data_dir_path} does not exist.")
        return

    # Only zip files not prefixed with '_' are plotted (prefix '_' excludes a run).
    files = [f for f in data_dir_path.glob("*.zip") if not f.name.startswith("_")]
    files.sort()

    if not files:
        print(f"ERROR: No .zip files found in {data_dir_path}")
        return

    # Resolve output directory using config AND subfolder argument
    output_dir = (base_dir / config.out_dir / args.subfolder).resolve()

    # Clean and recreate output directory
    if output_dir.exists() and output_dir.is_dir():
        for item in output_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_dir = output_dir / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory set to: {output_dir}")

    # ==========================================
    # 2. Data Processing Phase
    # ==========================================
    # Parse every run and aggregate the per-client DataFrames index-wise.
    full_dfs = []

    print(f"Starting analysis for {len(files)} ZIP files...")

    for f in files:
        print(f"Processing file: {f.name}...")

        csv, log = data_processor.process_zip_files(f)
        parsed_log = data_processor.parse_log(log)
        dfs = data_processor.parse_dfs(csv, parsed_log)
        print(f"  Parsed {len(dfs)} DataFrames.")

        if not full_dfs:
            full_dfs = dfs
        else:
            limit = min(len(full_dfs), len(dfs))
            for i in range(limit):
                full_dfs[i] = pd.concat([full_dfs[i], dfs[i]], ignore_index=True)

    # ==========================================
    # 3. Paper Figure: per-epoch latency (local vs remote)
    # ==========================================
    print("Generating execution time analysis...")
    latency.plot_logs_avg_latency(full_dfs, args.subfolder, config.domains, max_rounds=6)
    plt.savefig(f'{output_dir}/execution_time_analysis.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_dir}/pdf/execution_time_analysis.pdf', bbox_inches='tight')
    plt.close()

    print(f"Done. Figure saved to: {output_dir}/pdf/execution_time_analysis.pdf")


if __name__ == "__main__":
    main()
