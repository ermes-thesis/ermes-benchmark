## Prerequisites & Installation

### 1. Python Libraries
You need Python 3.10 or higher (the scripts use `X | Y` type hints and built-in generic types such as `list[tuple[...]]`). Python 3.11 or higher is preferable, so the standard library can parse the timestamps' ISO format directly (with older versions the format is slightly adjusted first). Install the required packages using pip:

```bash
pip install pandas numpy matplotlib networkx pydot pytz colorama
```

### 2. Graphviz (Required for Topology Layouts)

The topology graph uses pydot for hierarchical layouts. You must install the Graphviz system binaries (not just the Python library).

* **Windows**: Download the installer from [Graphviz.org](https://graphviz.org/), install it, and add it to your System PATH.
* **Ubuntu/Debian**: `sudo apt-get install graphviz`
* **macOS**: `brew install graphviz`

### 3. How to Run

Place your data (ZIP files containing .csv and .log files) in a data/ folder (or adjust the path in the config).

Run the main script:

```bash
python main.py
```

The results will be generated in the output directory specified in the [configuration file](./config.py) (default: `../output_img/<subfolder>`).

The plot legends label each client with the domain of the node it connects to,
looked up by the last octet of the node address. Keep the tables in
[`config.py`](./config.py) aligned with the experiment configurations:

* `vm_domains`: the current VM cluster (the `NODE_<DOMAIN>` variables in `../clients/vm/config.sh`).
* `legacy_vm_domains`: the previous cluster (`.70`–`.77`), where the archives in
  `data/replication` and `data/conflict_*` were collected.
* `heterogeneous_domains`: the cloud and Raspberry Pi nodes (`../clients/heterogeneous/config.sh`).

### 4. Project Structure

```
.
├── config.py           # User configuration (Paths, Topology, Settings)
├── data_processor.py   # Logic for parsing ZIPs, Logs, and DataFrames
├── main.py             # Entry point: Orchestrates data loading and plotting
└── plots/              # Visualization modules
    ├── distribution.py # Charts for task counts/distribution
    ├── latency.py      # Charts for latency (Violin, Box, Heatmaps)
    └── topology.py     # Network tree visualization with sparklines
```
