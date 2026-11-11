# Heterogeneous convergence experiment

This experiment runs the collection creator on a Linux/amd64 cloud machine
and the existing `read_write` client on a single Linux/aarch64 Raspberry Pi 3.
The client source is reused from
[`../clients/read_write`](../clients/read_write); no copy of that implementation
is maintained here.

## Configuration

Edit [`clients/config.sh`](clients/config.sh) and replace the cloud and edge
node IP placeholders. SSH operations use the local aliases `sola4` and
`sola-pi`; the aliases are not used as Ermes network addresses. All addresses
and ports used by this experiment are derived from that file.
[`clients/config.yaml`](clients/config.yaml) is a template; the runner injects
the cloud node IP and `GTP_PORT` into a temporary copy before uploading it to
either node.

Run the runner on `sola4`. Cloud-side build, preparation, collection creation,
and result collection are local operations on that machine. Only Raspberry Pi
operations use `ssh sola-pi` and `scp sola-pi`; its username and any SSH
settings come from the local SSH configuration. `ERMES_DEPLOY_PATH` must point
to the `ermes-deploy` checkout because its
`heterogeneous-deploy/download_logs.sh` script handles log collection; the
runner passes the timestamped results directory as its only argument.

Before creating the collection, the runner executes the dedicated
[`clients/deploy_functions.sh`](clients/deploy_functions.sh) script locally.
It compiles the six existing sources under
`serverless_functions/functions/` and inserts them into the configured
registry. Set `SERVERLESS_FUNCTIONS_PATH` and `FUNCTION_REGISTRY_PORT` in
[`clients/config.sh`](clients/config.sh). The
registry is assumed to run on the cloud node IP.
Set `DEPLOY_FUNCTIONS=false` only when the functions are already deployed.
The deployment uses `${HOME}/go/bin/ermes-cli` by default; set `ERMES_CLI` if
the executable is installed elsewhere.

## Running

From this directory, run:

```bash
./clients/run_heterogeneous.sh
```

The runner cross-compiles the cloud clients with `GOARCH=amd64` and the read
client with `GOARCH=arm64`, creates and writes the collection on the cloud node,
starts the read client on the Raspberry Pi, and invokes the deployment
repository's log downloader into `clients/results/`. It then copies cloud CSV
results locally and downloads Raspberry Pi CSV results into the same
timestamped directory. The complete timestamped experiment directory is also
archived as `data/heterogeneous/heterogeneous_<timestamp>.zip`.

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
