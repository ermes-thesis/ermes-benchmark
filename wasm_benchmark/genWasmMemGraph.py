import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import seaborn as sns
import sys
import re
import numpy as np

# === CONFIG ===
file_ext = ".png"
args = sys.argv[1:]

# Check flags
if "--pdf" in args:
    file_ext = ".pdf"
    args.remove("--pdf")
    print("Output format set to PDF.")
else:
    print("Output format set to PNG (default).")

if "--individual" in args:
    args.remove("--individual")

if len(args) < 1:
    print("Error: Memory file path not provided.", file=sys.stderr)
    print("Usage: python plot.py [--pdf] <path_to_memory_file.txt>", file=sys.stderr)
    sys.exit(1)

memory_path = Path(args[0])

sns.set_theme(style="whitegrid", font_scale=1.2)
palette = "viridis"

# ============================================================
# PARSING FUNCTIONS
# ============================================================

def _parse_label(raw_label):
    parts = raw_label.split("_")
    if not parts: return None, None, None, None, None

    algorithm_name = parts[0]
    runtime = "Unknown"
    compiler = "None"
    opt = "None"

    if len(parts) > 1:
        runtime = parts[1].capitalize()
        if runtime == "Native":
            compiler = "Native"
            opt = "Native"
        else:
            other_parts = parts[2:]
            for token in other_parts:
                if token.lower() in ["interpreter", "jit", "aot"]:
                    compiler = token.capitalize()
                elif "noopts" in token.lower():
                    opt = "NoOpts"
                elif "withopts" in token.lower():
                    opt = "WithOpts"

    # Add suffixes
    if "TailFibonacci" == algorithm_name:
        algorithm_name_suffixed = algorithm_name + " (20k)"
    elif "Fibonacci" == algorithm_name:
        algorithm_name_suffixed = algorithm_name + " (40)"
    else:
        algorithm_name_suffixed = algorithm_name

    label = f"{runtime}\n{compiler}\n{opt}"
    return algorithm_name_suffixed, runtime, compiler, opt, label

def parse_memory_stats(lines):
    records = []
    text = "".join(lines)
    scenario_blocks = re.split(r"#+ SCENARIO: ", text)

    for block in scenario_blocks[1:]:
        lines_in_block = block.strip().splitlines()
        if not lines_in_block: continue

        scenario_header = lines_in_block[0].strip()
        if "NET MEMORY" not in scenario_header: continue

        algorithm_name_from_header = scenario_header.split("-")[0].strip()
        content = "\n".join(lines_in_block[1:])
        scenarios = re.split(r"## ", content)

        for rblock in scenarios[1:]:
            if not rblock.strip(): continue
            try:
                raw_label, *rest = rblock.strip().splitlines()
            except ValueError: continue

            raw_label = raw_label.strip()
            if not raw_label: continue

            algorithm_name, runtime, compiler, opt, label = _parse_label(raw_label)
            if algorithm_name is None: continue

            block_text = "\n".join(rest)
            tot_mem_match = re.search(r"Total Memory:\s*([\d\.]+) KB", block_text)
            tot_mem = float(tot_mem_match.group(1)) if tot_mem_match else np.nan

            overhead_mem_match = re.search(r"Overhead Memory:\s*([\d\.]+|N/A)", block_text)
            overhead_val = overhead_mem_match.group(1) if overhead_mem_match else None
            overhead_mem = float(overhead_val) if overhead_val and overhead_val != "N/A" else np.nan

            net_match = re.search(r"NET Memory:\s*([\d\.]+) KB", block_text)
            net_mem = float(net_match.group(1)) if net_match else np.nan

            records.append({
                "Algorithm": algorithm_name,
                "Runtime": runtime,
                "Compilation": compiler,
                "Optimization": opt,
                "Label": label,
                "TotMemory_MB": tot_mem / 1000,
                "OverheadMemory_MB": overhead_mem / 1000,
                "NetMemory_MB": net_mem / 1000
            })

    return pd.DataFrame(records)

# ============================================================
# MAIN SCRIPT
# ============================================================

print(f"Loading memory data from: {memory_path}")
with open(memory_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

df_mem = parse_memory_stats(lines)

# ============================================================
# PLOTTING
# ============================================================

print("\nGenerating individual memory plots...")

# 1. Calc Max Y for Opts Comparison (No Native)
max_y_total_no_native = df_mem[df_mem["Runtime"] != "Native"]["TotMemory_MB"].max()
if pd.isna(max_y_total_no_native): max_y_total_no_native = 100
max_y_total_no_native *= 1.1

# 2. Calc Max Y for Total vs Overhead (With Native support in Total)
max_total_w_opts = df_mem[(df_mem["Optimization"] == "WithOpts") | (df_mem["Runtime"] == "Native")]["TotMemory_MB"].max()
max_overhead_w_opts = df_mem[(df_mem["Optimization"] == "WithOpts") & (df_mem["Runtime"] != "Native")]["OverheadMemory_MB"].max()
max_y_total_vs_overhead = max(max_total_w_opts, max_overhead_w_opts)
if pd.isna(max_y_total_vs_overhead): max_y_total_vs_overhead = 100
max_y_total_vs_overhead *= 1.1

# 3. Max Y for Net Memory
max_y_net = df_mem["NetMemory_MB"].max()
if pd.isna(max_y_net): max_y_net = 10
max_y_net *= 1.1

configs = [
    # --- PAIR 1: Optimization Impact (No Native) ---
    {
        "col": "TotMemory_MB",
        "filter": lambda df: df[(df["Optimization"] == "NoOpts") & (df["Runtime"] != "Native")],
        "filename": f"memory-total-noopts-no-native{file_ext}",
        "ylim": max_y_total_no_native,
        "figsize": (7, 5),
        "hide_ylabel": False # Show label and ticks for first chart
    },
    {
        "col": "TotMemory_MB",
        "filter": lambda df: df[(df["Optimization"] == "WithOpts") & (df["Runtime"] != "Native")],
        "filename": f"memory-total-withopts-no-native{file_ext}",
        "ylim": max_y_total_no_native,
        "figsize": (7, 5),
        "hide_ylabel": True # HIDE label and ticks for comparison
    },

    # --- PAIR 2: Overhead vs Total (With Native in Total) ---
    {
        "col": "OverheadMemory_MB",
        "filter": lambda df: df[(df["Optimization"] == "WithOpts") & (df["Runtime"] != "Native")],
        "filename": f"memory-overhead-withopts-no-native{file_ext}",
        "ylim": max_y_total_vs_overhead,
        "figsize": (7, 5),
        "hide_ylabel": True # HIDE label and ticks
    },
    {
        "col": "TotMemory_MB",
        "filter": lambda df: df[(df["Optimization"] == "WithOpts") | (df["Runtime"] == "Native")],
        "filename": f"memory-total-withopts-native{file_ext}",
        "ylim": max_y_total_vs_overhead,
        "figsize": (8, 5), # WIDER for Native
        "hide_ylabel": False # Show label and ticks
    },

    # --- SINGLE: Net Memory (With Native) ---
    {
        "col": "NetMemory_MB",
        "filter": lambda df: df[(df["Optimization"] == "WithOpts") | (df["Runtime"] == "Native")],
        "filename": f"memory-net-withopts-native{file_ext}",
        # "ylim": max_y_net,
        "figsize": (8, 5), # WIDER for Native
        "hide_ylabel": False
    }
]

for cfg in configs:
    filtered_data = cfg["filter"](df_mem)

    if filtered_data.empty:
        print(f"  -> Skipping {cfg['filename']} (No data)")
        continue

    # Use specified figsize
    plt.figure(figsize=cfg["figsize"])

    ax = sns.barplot(data=filtered_data, x="Label", y=cfg["col"], hue="Algorithm", palette=palette)

    plt.xlabel("")

    if cfg.get("hide_ylabel", False):
        plt.ylabel("")
        plt.tick_params(axis="y", labelleft=False) # Hide numbers
    else:
        plt.ylabel("Memory (MB)")
        plt.tick_params(axis="y", labelleft=True)

    plt.tick_params(axis="x")

    if "ylim" in cfg:
        plt.ylim(0, cfg["ylim"])

    plt.legend().remove()

    plt.tight_layout()
    plt.savefig(cfg["filename"], bbox_inches='tight')
    plt.close()
    print(f"  -> Saved {cfg['filename']}")

# Legend generation (based on last plot handles)
if not df_mem.empty:
    handles, labels = ax.get_legend_handles_labels()
    fig_leg = plt.figure(figsize=(len(labels) * 2.5, 1))
    ax_leg = fig_leg.add_subplot(111)
    ax_leg.axis('off')
    ax_leg.legend(handles, labels, title="Algorithm", loc='center', ncol=len(labels), frameon=True, borderaxespad=0.1)
    fig_leg.savefig(f"legend_algorithms{file_ext}", bbox_inches='tight')
    plt.close(fig_leg)
    print(f"  -> Saved legend_algorithms{file_ext}")

print("Individual plots generation complete.")