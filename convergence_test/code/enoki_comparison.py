"""Plot Ermes (eventual/sequential) latency next to the Enoki traces.

For each subfolder of data/enoki_comparison/ (eventual, sequential), the Ermes
archive is parsed with data_processor and compared with the Enoki cloud-state
and replicated-state traces from data/enoki/. Six series are drawn: Ermes
writer/reader, Enoki cloud writer/reader, Enoki replicated writer/reader.

Latency is averaged over fixed time windows (--bucket-seconds, default: the
15 s client round) measured from each experiment's first request, and drawn
either as grouped bars (plots.latency.plot_logs_avg_latency) or as lines.
"""

import argparse
import inspect
import math
import sys
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

sys.dont_write_bytecode = True

import config
import data_processor
import enoki
from plots import latency


CONSISTENCY_MODELS = ("eventual", "sequential")
OUTPUT_NAME = "execution_time_analysis"
# Same Okabe-Ito order used by plots.latency, so both modes share colors.
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442"]


def load_ermes_dataframes(archive: Path, bucket_seconds: float) -> list[pd.DataFrame]:
    """Parse an Ermes archive and return [writer_df, reader_df]."""
    csv_data, log_data = data_processor.process_zip_files(archive)
    dfs = data_processor.parse_dfs(csv_data, data_processor.parse_log(log_data))
    dfs = [df for df in dfs if not df.empty and "Group" in df.columns]

    writers = [df for df in dfs if df["FuncName"].str.contains("write", case=False).any()]
    readers = [df for df in dfs if df["FuncName"].str.contains("read", case=False).any()]
    if len(writers) != 1 or len(readers) != 1:
        raise ValueError(f"{archive} must contain exactly one writer and one reader CSV")

    result = [writers[0].copy(), readers[0].copy()]
    # Re-bucket with the requested granularity (parse_dfs uses fixed 15 s rounds),
    # measured from the first request of either client.
    t0 = min(pd.to_datetime(df["StartTime"], utc=True).min() for df in result)
    for df in result:
        delta_s = (pd.to_datetime(df["StartTime"], utc=True) - t0).dt.total_seconds()
        df["Group"] = (delta_s // bucket_seconds).astype(int)
        # data_processor divides FuncDuration (ms) by 1000; plot in ms so the
        # values are comparable with the Enoki traces.
        df["Duration"] = df["FuncDuration"].astype(float)
    return result


def load_enoki_dataframes(archive: Path, bucket_seconds: float) -> list[pd.DataFrame]:
    """Return [writer_df, reader_df] for an Enoki archive, one row per window."""
    with zipfile.ZipFile(archive) as archive_file:
        members = [m for m in archive_file.namelist() if not m.endswith("/")]

    result = []
    for kind in ("write", "read"):
        matches = [m for m in members if kind in Path(m).name.lower()]
        if len(matches) != 1:
            raise ValueError(f"{archive} must contain exactly one {kind} CSV")
        trace = enoki.load_trace(archive, matches[0], bucket_seconds)
        result.append(pd.DataFrame({
            "Group": (trace["elapsed_s"] // bucket_seconds).round().astype(int),
            "Duration": trace["latency_ms"],
            "EntryHost": f"enoki-{kind}",
            "Is_Local": True,
        }))
    return result


def find_single_zip(directory: Path) -> Path:
    archives = sorted(f for f in directory.glob("*.zip") if not f.name.startswith("_"))
    if len(archives) != 1:
        raise ValueError(f"Expected exactly one ZIP archive in {directory}, found {len(archives)}")
    return archives[0]


def draw_bars(ax, consistency, dfs, labels, max_groups, bucket_seconds):
    result = latency.plot_logs_avg_latency(
        dfs, f"enoki_comparison_{consistency}", config.domains,
        max_rounds=max_groups, ax=ax, draw_legend=False,
    )
    if result is None:
        raise RuntimeError(f"Unable to generate the {consistency} bar plot")

    _, legend_elements, _ = result
    for element, label in zip(legend_elements, labels):
        element.set_label(label)

    if bucket_seconds != data_processor.ROUND_DURATION_S:
        ax.set_xlabel(f"Time window ({bucket_seconds:g} s)", fontsize=16)
    # Thin the tick labels when there are many windows.
    ticks = ax.get_xticks()
    step = max(1, math.ceil(len(ticks) / 20))
    for i, tick_label in enumerate(ax.get_xticklabels()):
        tick_label.set_visible(i % step == 0)
    return legend_elements


def draw_lines(ax, dfs, labels, max_groups, bucket_seconds):
    legend_elements = []
    for i, (df, label) in enumerate(zip(dfs, labels)):
        series = df.groupby("Group")["Duration"].mean().sort_index()
        series = series[series.index < max_groups]
        color = OKABE_ITO[i % len(OKABE_ITO)]
        ax.plot(series.index * bucket_seconds, series.values, color=color, linewidth=2,
                marker="o" if len(series) <= 30 else None, markersize=4)
        legend_elements.append(Line2D([0], [0], color=color, linewidth=2, label=label))

    ax.set_facecolor("white")
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#cccccc", linewidth=0.6, alpha=0.9)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Elapsed time (s)", fontsize=16)
    ax.tick_params(axis="both", labelsize=14)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#888888")
    return legend_elements


def plot_consistency(consistency: str, ermes_archive: Path,
                     enoki_archives: dict[str, Path], output_dir: Path,
                     mode: str, bucket_seconds: float, duration_s: float) -> Path:
    dfs = load_ermes_dataframes(ermes_archive, bucket_seconds)
    labels = [f"Ermes {consistency} writer", f"Ermes {consistency} reader"]
    for experiment_type, archive in enoki_archives.items():
        dfs += load_enoki_dataframes(archive, bucket_seconds)
        labels += [f"Enoki {experiment_type} writer", f"Enoki {experiment_type} reader"]

    max_groups = math.ceil(duration_s / bucket_seconds)

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("white")
    if mode == "bar":
        legend_elements = draw_bars(ax, consistency, dfs, labels, max_groups, bucket_seconds)
    else:
        legend_elements = draw_lines(ax, dfs, labels, max_groups, bucket_seconds)

    ax.legend(handles=legend_elements, facecolor="white", edgecolor="gray",
              loc="upper left", bbox_to_anchor=(1.01, 1.0))
    ax.set_ylabel("Latency (ms)", fontsize=16)
    fig.tight_layout()

    target_dir = output_dir / consistency
    (target_dir / "pdf").mkdir(parents=True, exist_ok=True)
    name = f"{OUTPUT_NAME}_{mode}_{bucket_seconds:g}s"
    png_path = target_dir / f"{name}.png"
    pdf_path = target_dir / "pdf" / f"{name}.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare Ermes eventual/sequential latency with the Enoki traces."
    )
    parser.add_argument("--mode", choices=("bar", "line"), default="bar",
                        help="Grouped bars per time window, or one line per client (default: bar).")
    parser.add_argument("--bucket-seconds", type=float,
                        default=data_processor.ROUND_DURATION_S,
                        help="Width of the averaging window in seconds "
                             f"(default: {data_processor.ROUND_DURATION_S:g}, one client round).")
    parser.add_argument("--duration", type=float, default=None,
                        help="Seconds of experiment shown (default: 90 for bars, 150 for lines).")
    args = parser.parse_args()
    if args.bucket_seconds <= 0:
        parser.error("--bucket-seconds must be greater than zero")
    duration_s = args.duration or (90.0 if args.mode == "bar" else 150.0)

    base_dir = Path(inspect.getfile(inspect.currentframe())).resolve().parent
    data_dir = (base_dir / config.data_dir).resolve()
    output_dir = (base_dir / config.out_dir / "enoki_comparison").resolve()

    enoki_archives = {}
    for experiment_type, archive in enoki.find_archives(data_dir / "enoki"):
        if experiment_type in enoki_archives:
            raise ValueError(f"More than one Enoki {experiment_type} archive found")
        enoki_archives[experiment_type] = archive
    missing = {"cloud", "replicated"} - enoki_archives.keys()
    if missing:
        parser.error(f"Missing Enoki archives for: {', '.join(sorted(missing))}")
    enoki_archives = {k: enoki_archives[k] for k in ("cloud", "replicated")}

    for consistency in CONSISTENCY_MODELS:
        archive = find_single_zip(data_dir / "enoki_comparison" / consistency)
        print(f"Processing {archive}...")
        pdf_path = plot_consistency(consistency, archive, enoki_archives, output_dir,
                                    args.mode, args.bucket_seconds, duration_s)
        print(f"Saved {pdf_path}")


if __name__ == "__main__":
    main()
