"""Plot the read latency of an unpacked heterogeneous experiment."""

import argparse
import inspect
import sys
import tempfile
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import LogFormatterMathtext, LogLocator

sys.dont_write_bytecode = True

import config
import data_processor
from plots import latency


DEFAULT_READ_CSV = "results_log_54321_2026_11_10_12_08_04.csv"
OUTPUT_NAME = "execution_time_analysis"


def load_read_dataframe(experiment_dir: Path, csv_name: str) -> pd.DataFrame:
    """Load and validate the client read-results CSV."""
    csv_path = experiment_dir / csv_name
    if not csv_path.is_file():
        raise FileNotFoundError(f"Read-results CSV not found: {csv_path}")

    dataframe = pd.read_csv(csv_path)
    required_columns = {
        "StartTime",
        "EntryHost",
        "ExecHost",
        "FuncName",
        "FuncDuration",
    }
    missing = required_columns.difference(dataframe.columns)
    if missing:
        missing_columns = ", ".join(sorted(missing))
        raise ValueError(f"{csv_path} is missing columns: {missing_columns}")
    return dataframe


def plot_experiment(
    experiment_dir: Path,
    output_name: str,
    csv_name: str,
    max_epochs: int,
    base_dir: Path,
) -> None:
    dataframe = load_read_dataframe(experiment_dir, csv_name)
    csv_data = {csv_name: dataframe}

    log_data = {}
    for node_name in ("cloud", "edge"):
        log_path = experiment_dir / node_name / "general.log"
        if log_path.is_file():
            log_data[f"{node_name}.log"] = log_path.read_text(encoding="utf-8")
    parsed_log = data_processor.parse_log(log_data)
    dataframes = data_processor.parse_dfs(csv_data, parsed_log)
    if not dataframes or dataframes[0].empty:
        raise ValueError(f"No plottable read operations found in {experiment_dir / csv_name}")

    # The client starts independently of the Ermes migration cycle. Use the
    # cloud's policy transitions as the epoch boundaries so requests around a
    # transition are assigned to the Ermes epoch that served them.
    transition_timestamps = parsed_log.get("cloud.log", [])
    if not transition_timestamps:
        transition_timestamps = parsed_log.get("edge.log", [])
    if not transition_timestamps:
        raise ValueError("No Ermes epoch transitions found in cloud/edge logs")

    transitions = pd.DatetimeIndex(
        [data_processor.parse_timestamp(timestamp) for timestamp in transition_timestamps]
    ).tz_convert("UTC")
    request_times = pd.to_datetime(dataframes[0]["StartTime"], utc=True)
    first_request = request_times.min()
    first_boundary_index = transitions.searchsorted(first_request, side="right") - 1
    if first_boundary_index < 0:
        raise ValueError("Some client requests precede the first Ermes epoch boundary")
    ermes_epochs = (
        transitions.searchsorted(request_times, side="right")
        - first_boundary_index
    )
    dataframes[0]["Group"] = ermes_epochs
    dataframes[0] = dataframes[0].sort_values(
        by=["Group", "StartTime"]
    ).reset_index(drop=True)

    output_dir = (
        base_dir / config.out_dir / "heterogeneous" / output_name
    ).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir = output_dir / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor("white")
    result = latency.plot_logs_avg_latency(
        dataframes,
        "heterogeneous",
        {134: "SOLA4", 243: "SOLA4/PI"},
        max_rounds=max_epochs,
        ax=ax,
        draw_legend=False,
    )
    if result is None:
        raise RuntimeError("Unable to generate the heterogeneous latency plot")

    _, legend_elements, max_data_height = result
    # ax.set_yscale("log")
    positive_durations = dataframes[0].loc[
        dataframes[0]["Duration"] > 0, "Duration"
    ]
    if positive_durations.empty:
        raise ValueError("Latency values must be positive for logarithmic scaling")
    ax.set_ylim(positive_durations.min() * 0.8, max_data_height * 1.1)
    # ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0,), numticks=10))
    # ax.yaxis.set_major_formatter(LogFormatterMathtext(base=10))
    ax.set_ylabel("Latency (ms)", fontsize=18)
    ax.tick_params(axis="y", labelsize=16)
    if legend_elements:
        legend_elements[0].set_label("Reader (SOLA4/PI)")
        ax.legend(
            handles=legend_elements,
            facecolor="white",
            edgecolor="gray",
            loc="best",
        )

    fig.tight_layout()
    png_path = output_dir / f"{OUTPUT_NAME}.png"
    pdf_path = pdf_dir / f"{OUTPUT_NAME}.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Done. Figure saved to:\n  {png_path}\n  {pdf_path}")


def process_archive(
    archive_path: Path,
    csv_name: str,
    max_epochs: int,
    base_dir: Path,
) -> None:
    output_name = archive_path.stem
    if output_name.startswith("heterogeneous_"):
        output_name = output_name[len("heterogeneous_"):]

    with tempfile.TemporaryDirectory(prefix="heterogeneous_") as temporary_dir:
        extraction_dir = Path(temporary_dir)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extraction_dir)

        csv_paths = list(extraction_dir.rglob(csv_name))
        if len(csv_paths) != 1:
            raise ValueError(
                f"Expected one {csv_name} in {archive_path}, found {len(csv_paths)}"
            )
        plot_experiment(
            csv_paths[0].parent,
            output_name,
            csv_name,
            max_epochs,
            base_dir,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot per-epoch read latency for an unpacked heterogeneous run."
    )
    parser.add_argument(
        "experiment",
        nargs="?",
        default=None,
        help="Optional experiment directory or ZIP relative to convergence_test/data; "
        "without it, all heterogeneous ZIP files are processed",
    )
    parser.add_argument(
        "--csv",
        default=DEFAULT_READ_CSV,
        help="Read-results CSV filename inside the experiment directory",
    )
    parser.add_argument(
        "--max-epochs",
        type=int,
        default=6,
        help="Maximum number of epochs to show (default: 6)",
    )
    args = parser.parse_args()

    base_dir = Path(inspect.getfile(inspect.currentframe())).parent
    data_root = (base_dir / config.data_dir / "heterogeneous").resolve()
    if args.experiment is None:
        archives = sorted(data_root.glob("*.zip"))
        if not archives:
            raise FileNotFoundError(f"No heterogeneous ZIP files found in {data_root}")
        for archive_path in archives:
            process_archive(archive_path, args.csv, args.max_epochs, base_dir)
        return

    experiment_path = (base_dir / config.data_dir / args.experiment).resolve()
    if experiment_path.is_file() and experiment_path.suffix.lower() == ".zip":
        process_archive(experiment_path, args.csv, args.max_epochs, base_dir)
    elif experiment_path.is_dir():
        plot_experiment(
            experiment_path,
            experiment_path.name,
            args.csv,
            args.max_epochs,
            base_dir,
        )
    else:
        raise FileNotFoundError(f"Experiment directory or ZIP not found: {experiment_path}")


if __name__ == "__main__":
    main()
