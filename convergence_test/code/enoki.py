"""Plot latency traces from all Enoki cloud and replicated-state archives."""

import argparse
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


EXPERIMENT_DIRS = {
    "cloud": ("cloud", "cloud_state"),
    "replicated": ("replicated", "replicated_state"),
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
    experiment_type: str,
    archive: Path,
    output_dir: Path,
    bucket_seconds: float,
) -> Path:
    with zipfile.ZipFile(archive) as archive_file:
        members = [
            Path(member).name
            for member in archive_file.namelist()
            if not member.endswith("/")
        ]
    read_members = [member for member in members if "read" in member.lower()]
    write_members = [member for member in members if "write" in member.lower()]
    if len(read_members) != 1 or len(write_members) != 1:
        raise ValueError(
            f"{archive} must contain exactly one read and one write CSV "
            f"(found {read_members!r} and {write_members!r})"
        )

    read = load_trace(archive, read_members[0], bucket_seconds)
    write = load_trace(archive, write_members[0], bucket_seconds)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.plot(read["elapsed_s"], read["latency_ms"], color="#0072B2", linewidth=2,
            label="Reading client")
    ax.plot(write["elapsed_s"], write["latency_ms"], color="#E69F00", linewidth=2,
            label="Writing client")
    ax.set_title(f"{experiment_type.capitalize()} state: {archive.stem}")
    ax.set_xlabel("Elapsed time (s)")
    ax.set_ylabel("Average latency (ms)")
    ax.grid(axis="y", color="#cccccc", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend()
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()

    target_dir = output_dir / experiment_type / archive.stem
    target_dir.mkdir(parents=True, exist_ok=True)
    png_path = target_dir / "latency_over_time.png"
    pdf_path = target_dir / "pdf" / "latency_over_time.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    return pdf_path


def find_archives(data_dir: Path) -> list[tuple[str, Path]]:
    """Return every archive under the configured cloud/replicated directories."""
    archives = []
    for experiment_type, directory_names in EXPERIMENT_DIRS.items():
        for directory_name in directory_names:
            directory = data_dir / directory_name
            if directory.is_dir():
                archives.extend(
                    (experiment_type, archive)
                    for archive in sorted(directory.glob("*.zip"))
                )
    return archives


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

    archives = find_archives(data_dir)
    if not archives:
        parser.error(f"No cloud or replicated ZIP archives found under {data_dir}")

    for experiment_type, archive in archives:
        pdf_path = plot_experiment(
            experiment_type, archive, output_dir, args.bucket_seconds
        )
        print(f"Saved {pdf_path}")


if __name__ == "__main__":
    main()
