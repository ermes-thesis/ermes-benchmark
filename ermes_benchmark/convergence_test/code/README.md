## Prerequisites & Installation

### 1. Python Libraries
You need Python 3.8 or higher. It is preferrable to have Python 3.11 or higher to parse the ISO format of the timestamps using the standard library (else the format is slightly changed to match the older version). Install the required packages using pip:

```bash
pip install pandas numpy matplotlib networkx pydot pytz colorama bokeh holoviews d3blocks
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

The results will be generated in the output directory specified in the [configuration file](./config.py) (default: `../output_img_new/full_traversal_analysis`).

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
