"""Plot latency traces from the Enoki cloud and replicated-state experiments."""

import argparse
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


EXPERIMENTS = {
    "cloud_state": {
        "archive": "cloud_state/cloud_state.zip",
        "read": "cloud-read.csv",
        "write": "cloud-write.csv",
        "title": "Cloud state",
    },
    "replicated_state": {
        "archive": "replicated_state/replicated_state.zip",
        "read": "replicated-read.csv",
        "write": "replicated-write.csv",
        "title": "Replicated state",
    },
}


def load_trace(archive: Path, member: str, bucket_seconds: float) -> pd.DataFrame:
    """Load one trace and return average latency for each elapsed-time bucket."""
    with zipfile.ZipFile(archive) as archive_file:
        with archive_file.open(member) as trace_file:
            trace = pd.read_csv(trace_file, usecols=["start", "end"])

    trace["start"] = pd.to_numeric(trace["start"], errors="coerce")
    trace["end"] = pd.to_numeric(trace["end"], errors="coerce")
    trace["latency_ms"] = (trace["end"] - trace["start"]) * 1000
    trace = trace.dropna(subset=["start", "latency_ms"])
    if trace.empty:
        raise ValueError(f"{member} does not contain valid start/end timestamps")

    trace["elapsed_s"] = trace["start"] - trace["start"].min()
    trace["bucket"] = (trace["elapsed_s"] // bucket_seconds) * bucket_seconds
    return (
        trace.groupby("bucket", as_index=False)["latency_ms"]
        .mean()
        .rename(columns={"bucket": "elapsed_s"})
    )


def plot_experiment(
    name: str,
    settings: dict[str, str],
    data_dir: Path,
    output_dir: Path,
    bucket_seconds: float,
) -> Path:
    archive = data_dir / settings["archive"]
    if not archive.is_file():
        raise FileNotFoundError(f"Archive not found: {archive}")

    read = load_trace(archive, settings["read"], bucket_seconds)
    write = load_trace(archive, settings["write"], bucket_seconds)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.plot(read["elapsed_s"], read["latency_ms"], color="#0072B2", linewidth=2,
            label="Reading client")
    ax.plot(write["elapsed_s"], write["latency_ms"], color="#E69F00", linewidth=2,
            label="Writing client")
    ax.set_title(settings["title"])
    ax.set_xlabel("Elapsed time (s)")
    ax.set_ylabel("Average latency (ms)")
    ax.grid(axis="y", color="#cccccc", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend()
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()

    target_dir = output_dir / name
    target_dir.mkdir(parents=True, exist_ok=True)
    png_path = target_dir / "latency_over_time.png"
    pdf_path = target_dir / "pdf" / "latency_over_time.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    return pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot Enoki cloud and replicated-state latency traces."
    )
    parser.add_argument(
        "--bucket-seconds",
        type=float,
        default=10.0,
        help="Width of the elapsed-time averaging buckets (default: 10 seconds).",
    )
    args = parser.parse_args()
    if args.bucket_seconds <= 0:
        parser.error("--bucket-seconds must be greater than zero")

    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "data" / "enoki"
    output_dir = base_dir / "output_img" / "enoki"

    for name, settings in EXPERIMENTS.items():
        pdf_path = plot_experiment(
            name, settings, data_dir, output_dir, args.bucket_seconds
        )
        print(f"Saved {pdf_path}")


if __name__ == "__main__":
    main()
