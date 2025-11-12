import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import seaborn as sns
import sys
import re
import numpy as np

# === CONFIG ===
# Imposta l'estensione predefinita
file_ext = ".png"
args = sys.argv[1:] # Copia gli argomenti

# Controlla il flag --pdf
if "--pdf" in args:
    file_ext = ".pdf"
    args.remove("--pdf") # Rimuovi il flag dalla lista degli argomenti
    print("Output format set to PDF.")
else:
    print("Output format set to PNG (default).")


# Controlla il percorso del file di memoria
if len(args) < 1:
    print("Error: Memory file path not provided.", file=sys.stderr)
    print("Usage: python plot.py [--pdf] <path_to_memory_file.txt>", file=sys.stderr)
    sys.exit(1)

memory_path = Path(args[0])

mem_summary_img = Path(f"memory-summary{file_ext}")

sns.set_theme(style="whitegrid", font_scale=1.2)
palette = "Set2"

# ============================================================
# PARSING FUNCTIONS FOR MEMORY DATA
# ============================================================

def _parse_label(raw_label):
    """Helper to parse labels like 'Fibonacci_Wasmedge_AOT_NoOpts' or 'Fibonacci_Native'"""
    parts = raw_label.split("_")
    if not parts:
        return None, None, None, None, None

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

def parse_main_benchmarks(lines):
    """
    Parse the main runtime + memory sections (MaxRSS) from a benchmark file.
    Filters out "OVERHEAD" and "NET MEMORY" scenarios.
    Returns a DataFrame with columns:
    [Algorithm, Runtime, Compilation, Optimization, Label, MaxRSS_KB]
    """
    records = []
    text = "".join(lines)
    scenario_blocks = re.split(r"#+ SCENARIO: ", text)

    for block in scenario_blocks[1:]:
        lines_in_block = block.strip().splitlines()
        if not lines_in_block:
            continue

        scenario_header = lines_in_block[0].strip()
        # Filter for main scenarios only, not OVERHEAD or NET MEMORY
        if "OVERHEAD" in scenario_header or "NET MEMORY" in scenario_header:
            continue

        content = "\n".join(lines_in_block[1:])

        scenarios = re.split(r"## ", content)
        for rblock in scenarios[1:]:
            if not rblock.strip():
                continue

            try:
                raw_label, *rest = rblock.strip().splitlines()
            except ValueError:
                print(f"Warning: Skipping block, possibly empty: '{rblock}'")
                continue

            raw_label = raw_label.strip()
            if not raw_label:
                continue

            # Parse label
            algorithm_name, runtime, compiler, opt, label = _parse_label(raw_label)
            if algorithm_name is None:
                continue

            # Extract metrics from the block
            block_text = "\n".join(rest)
            maxrss_match = re.search(r"Mean MaxRSS:\s*([\d\.]+) KB", block_text)
            maxrss = float(maxrss_match.group(1)) if maxrss_match else np.nan

            records.append({
                "Runtime": runtime,
                "Compilation": compiler,
                "Algorithm": algorithm_name,
                "Optimization": opt,
                "Label": label,
                "MaxRSS_KB": maxrss,
            })

    return pd.DataFrame(records)


def parse_memory_stats(lines):
    """
    Parse the NET MEMORY sections from the benchmark text file.
    Returns a DataFrame with columns:
    [Algorithm, Runtime, Compilation, Optimization, Label, NetMemory_MB, etc.]
    """
    records = []
    text = "".join(lines)
    scenario_blocks = re.split(r"#+ SCENARIO: ", text)

    for block in scenario_blocks[1:]:
        lines_in_block = block.strip().splitlines()
        if not lines_in_block:
            continue

        scenario_header = lines_in_block[0].strip()
        # Filter only for NET MEMORY scenarios
        if "NET MEMORY" not in scenario_header:
            continue

        # Extract algorithm name from header (e.g., "Fibonacci")
        algorithm_name_from_header = scenario_header.split("-")[0].strip()
        content = "\n".join(lines_in_block[1:])

        scenarios = re.split(r"## ", content)
        for rblock in scenarios[1:]:
            if not rblock.strip():
                continue

            try:
                raw_label, *rest = rblock.strip().splitlines()
            except ValueError:
                print(f"Warning: Skipping block, possibly empty: '{rblock}'")
                continue

            raw_label = raw_label.strip()
            if not raw_label:
                continue

            # Parse label
            algorithm_name, runtime, compiler, opt, label = _parse_label(raw_label)
            if algorithm_name is None:
                continue

            # Sanity check
            if algorithm_name != algorithm_name_from_header:
                # Add suffixes to header name for comparison
                if "TailFibonacci" == algorithm_name_from_header:
                    algorithm_name_from_header_suffixed = algorithm_name_from_header + " (20k)"
                elif "Fibonacci" == algorithm_name_from_header:
                    algorithm_name_from_header_suffixed = algorithm_name_from_header + " (40)"
                else:
                    algorithm_name_from_header_suffixed = algorithm_name_from_header

                # Re-check with suffixes
                if algorithm_name != algorithm_name_from_header_suffixed:
                    print(f"Warning: Label algorithm '{algorithm_name}' differs from header '{algorithm_name_from_header_suffixed}'")


            block_text = "\n".join(rest)

            tot_mem_match = re.search(r"Total Memory:\s*([\d\.]+) KB", block_text)
            tot_mem = float(tot_mem_match.group(1)) if tot_mem_match else np.nan

            overhead_mem_match = re.search(r"Overhead Memory:\s*([\d\.]+|N/A)", block_text) # 'N/A' won't have 'KB'
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

df_max_mem = parse_main_benchmarks(lines)
df_mem = parse_memory_stats(lines)

print("--- MaxRSS Memory Data (from main scenarios) ---")
print(df_max_mem.head())
print("------------------------------------------------\n")
print("--- NET Memory Data (from NET MEMORY scenarios) ---")
print(df_mem.head())
print("---------------------------------------------------\n")


# ============================================================
# PLOTTING
# ============================================================

print(f"Generating combined memory summary plot ({mem_summary_img})...")
# --- Create the figure grid ---
fig = plt.figure(figsize=(15, 18)) # Figura alta

# Griglia 3x1 (verticale)
ax1 = plt.subplot2grid((3, 1), (0, 0)) # Riga 0
ax2 = plt.subplot2grid((3, 1), (1, 0)) # Riga 1
ax3 = plt.subplot2grid((3, 1), (2, 0)) # Riga 2

# --- Plot 1: Total Memory ---
sns.barplot(data=df_mem, x="Label", y="TotMemory_MB", hue="Algorithm", ax=ax1, palette=palette)
ax1.set_title("Total Memory (MB)")
# ax1.set_yscale("log")
ax1.set_xlabel("")
ax1.set_ylabel("Memory (MB)")
# ax1.set_ylim(1e3, 1e5)
ax1.tick_params(axis="x", labelsize=12)
handles, labels = ax1.get_legend_handles_labels()
ax1.legend_.remove()

# --- Plot 2: Overhead Memory ---
sns.barplot(data=df_mem, x="Label", y="OverheadMemory_MB", hue="Algorithm", ax=ax2, palette=palette)
ax2.set_title("Overhead Memory (MB)")
# ax2.set_yscale("log")
ax2.set_xlabel("")
ax2.set_ylabel("Memory (MB)")
# ax2.set_ylim(1e3, 1e5)
ax2.tick_params(axis="x", labelsize=12)
ax2.legend_.remove()

# --- Plot 3: Net Memory ---
sns.barplot(data=df_mem, x="Label", y="NetMemory_MB", hue="Algorithm", ax=ax3, palette=palette)
ax3.set_title("Net Memory (MB)")
ax3.set_xlabel("Runtime Configuration")
ax3.set_ylabel("Memory (MB)")
ax3.tick_params(axis="x", labelsize=12)
ax3.legend_.remove()

# --- Layout adjustments ---
fig.suptitle("Memory Usage Comparison across Scenarios", fontsize=16, y=0.98)

num_labels = len(labels)
ncol = min(num_labels, 6) # Massimo 6 colonne
fig.legend(
    handles=handles,
    labels=labels,
    title="Algorithm",
    loc='upper center',         # Posiziona in alto
    bbox_to_anchor=(0.5, 0.96), # Appena sotto il titolo
    borderaxespad=0.1,
    ncol=ncol
)

plt.subplots_adjust(
    top=0.90,    # Spazio per il titolo e la legenda
    bottom=0.05, # Meno spazio in basso
    left=0.08,   # Spazio per etichette Y
    right=0.98,
    hspace=0.30, # Spazio verticale ridotto
    wspace=0.0   # Nessuno spazio orizzontale
)
plt.savefig(mem_summary_img)
plt.close(fig)

print(f"Plots generated and saved to {mem_summary_img}")