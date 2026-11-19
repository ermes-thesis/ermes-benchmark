# Convergence experiments

The experiments run on two different kinds of infrastructure. Each one has its
own folder under [`clients/`](clients), with its own configuration. The Go
clients ([`create`](clients/create), [`read`](clients/read),
[`write`](clients/write), [`read_write`](clients/read_write)) are shared and
stay in `clients/`.

```
clients/
├── create/ read/ write/ read_write/   Go clients (shared)
├── vm/                                VM cluster (ermes-deploy inventories/stateful)
│   ├── config.sh                      subnet, SSH jump host, client VMs, Ermes nodes
│   ├── config.yaml                    client config (GTP on <subnet>.58)
│   ├── common.sh                      shared steps: build, upload, flush, download, zip
│   ├── run_enoki_comparison.sh        Ermes vs Enoki (1 writer, 1 reader)
│   ├── run_replication.sh             state replication (1 writer, 4 readers)
│   └── run_conflict.sh                conflicting updates (2 read-write clients)
└── heterogeneous/                     amd64 cloud machine + aarch64 Raspberry Pi
    ├── config.sh                      node IPs, ports, experiment parameters
    ├── config.yaml                    client config (GTP on the cloud node)
    ├── deploy_functions.sh
    └── run_heterogeneous.sh
```

## VM-cluster experiments

The scripts run from your workstation. They connect to the client VMs as
`ubuntu` through the `sola5remote` jump host. Everything about the cluster is
in [`clients/vm/config.sh`](clients/vm/config.sh), and every value must match
the `ermes-deploy` inventory `inventories/stateful`:

- the subnet, SSH user and jump host;
- the two client VMs (`.59` and `.60`) and the central GTP node (`.58`);
- one variable per Ermes node, named after its domain (`NODE_IT`,
  `NODE_UNIMI`, …).

You can override the main values through the environment: `ERMES_SUBNET`,
`ERMES_SSH_USER`, `ERMES_JUMP_HOST` (set it to an empty string for direct
SSH) and `ERMES_DEPLOY_PATH`.

```bash
./clients/vm/run_enoki_comparison.sh [sequential|eventual]  # -> data/enoki_comparison/<consistency>/
./clients/vm/run_replication.sh                              # -> data/replication/
./clients/vm/run_conflict.sh sequential                      # -> data/conflict_1/
./clients/vm/run_conflict.sh eventual                        # -> data/conflict_eventual/
```

You can also give the consistency through `ERMES_CONSISTENCY` (default:
`sequential`). Each script follows the same steps from
[`common.sh`](clients/vm/common.sh):

1. cross-compile the clients for amd64 into `clients/vm/bin/`;
2. stop stale clients, clean the remote folders, then upload the binaries and
   `config.yaml` (with the GTP address moved to `ERMES_SUBNET`);
3. flush Ermes with the `flush-ermes-nodes.yml` playbook;
4. run the scenario;
5. download the client CSVs into `clients/vm/results/<timestamp>/`, and the
   node logs into `clients/vm/logs/` with `ermes-deploy/scripts/download_logs.sh`;
6. archive them as `data/<scenario>/<scenario>_<timestamp>.zip`.

## Heterogeneous experiment

This experiment runs the collection creator and the writer on a Linux/amd64
cloud machine, and the existing `read` client on a single Linux/aarch64
Raspberry Pi 3.

### Configuration

Edit [`clients/heterogeneous/config.sh`](clients/heterogeneous/config.sh) and
set the cloud and edge node IPs. SSH operations use the local aliases `sola4`
and `sola-pi`; Ermes does not use these aliases as network addresses.
[`clients/heterogeneous/config.yaml`](clients/heterogeneous/config.yaml) is
copied verbatim to both nodes, so keep its `GTP_Address` equal to
`CLOUD_NODE_IP:GTP_PORT`.

Run the runner on `sola4`. Building, preparation, collection creation and
result collection on the cloud side are local operations on that machine; the
cloud working directory is `clients/heterogeneous/heterogeneous/`. Only the
Raspberry Pi steps use `ssh sola-pi` and `scp sola-pi`; the Pi's username and
other SSH settings come from your local SSH configuration.

`ERMES_DEPLOY_PATH` must point to the `ermes-deploy` checkout, because its
`heterogeneous-deploy/download_logs.sh` script collects the logs. The runner
passes the timestamped results directory to that script as its only argument.

Before it creates the collection, the runner executes
[`clients/heterogeneous/deploy_functions.sh`](clients/heterogeneous/deploy_functions.sh)
locally. That script compiles the six existing sources under
`serverless_functions/functions/` and inserts them into the configured
registry, which is assumed to run on the cloud node IP:

- Set `SERVERLESS_FUNCTIONS_PATH` and `FUNCTION_REGISTRY_PORT` in
  `config.sh`.
- Set `DEPLOY_FUNCTIONS=false` only when the functions are already deployed.
- The script uses `${HOME}/go/bin/ermes-cli` by default; set `ERMES_CLI` if
  the executable is installed elsewhere.

### Running

```bash
./clients/heterogeneous/run_heterogeneous.sh
```

The runner:

1. cross-compiles the cloud clients with `GOARCH=amd64` and the read client
   with `GOARCH=arm64`;
2. creates the collection and writes to it on the cloud node;
3. starts the read client on the Raspberry Pi;
4. downloads the logs, the cloud CSVs and the Raspberry Pi CSVs into
   `clients/heterogeneous/results/<timestamp>/`;
5. archives that directory as
   `data/heterogeneous/heterogeneous_<timestamp>.zip`.

## Enoki latency plots

The Enoki traces are stored in ZIP archives under `data/enoki/cloud_state/`
and `data/enoki/replicated_state/` (the shorter `cloud/` and `replicated/`
directory names are also supported). Generate one read/write latency plot for
every archive with:

```bash
python3 code/enoki.py
```

The script ignores the response payload, computes `(end - start)` for each
request, averages latency in 10-second elapsed-time buckets, and writes each
PNG and PDF figure below `output_img/enoki/{cloud,replicated}/<archive-name>/`.
The ZIP members are read directly into memory and are never extracted to disk.
Use `--bucket-seconds` to change the averaging interval.

## Ermes vs Enoki comparison plots

To compare the Ermes runs in `data/enoki_comparison/{eventual,sequential}/`
with the Enoki cloud and replicated traces, run:

```bash
cd code && python3 enoki_comparison.py
```

Each figure shows six series: Ermes writer/reader and the Enoki cloud and
replicated writer/reader. Options:

- `--mode bar|line`: grouped bars per time window (default) or one line per
  client over elapsed time.
- `--bucket-seconds N`: width of the averaging window (default: 15, one client
  round), e.g. `--bucket-seconds 1`.
- `--duration S`: seconds of experiment shown (default: 90 for bars, i.e. six
  15 s epochs, and 150 for lines).

Figures are written to `output_img/enoki_comparison/{eventual,sequential}/` as
`execution_time_analysis_<mode>_<bucket>s.{png,pdf}`, so different settings
don't overwrite each other.

## Heterogeneous latency plot

For the unpacked two-node heterogeneous experiment, generate the existing
grouped-bar plot of per-epoch average latency with a logarithmic latency axis:

```bash
python3 code/heterogeneous.py
```

By default, the script extracts and processes every
`data/heterogeneous/*.zip`, writing each figure under its matching timestamp
directory in `output_img/heterogeneous/`. Archives are extracted into temporary
directories and removed automatically when processing finishes. An explicit
experiment directory or ZIP can be supplied as the positional argument.
Override the CSV filename or displayed epoch count with `--csv` and
`--max-epochs`. Epoch assignment uses the Ermes policy-transition timestamps
from `cloud/general.log` (falling back to `edge/general.log`).
