# Ermes paper benchmarks

Workloads, experimental data, and plotting scripts for the paper evaluation.

Two benchmark suites:
1. **[Convergence benchmark](convergence_test)** — RQ1 (state management &
   perceived latency): per-client latency over epochs on the **Ermes**
   configuration, as the platform migrates and replicates the state. Two
   experiments: state replication (one writer, four readers) and a two-client
   read/write conflict under each consistency policy.
2. **[Micro benchmarks](micro_bench)** — RQ2/RQ4 (scalability, io-intensity)
   and RQ3/RQ4 (adaptation to static and mobile clients): compares three
   configurations — **Ermes** (`distributed`), **Cloud-Data / CD**
   (`centralized`), **Cloud-Only / CO** (`cloud_only`).

The `data/` folders ship the datasets used in the paper, so **all figures can
be regenerated without a cluster** (see below). To re-run the experiments,
first deploy the platform: see the package top-level `README.md` (build,
inventories, deploy, function publishing).

> Note: the client scripts read the cluster location from the environment
> (`ERMES_SUBNET`, `ERMES_JUMP_HOST`, `ERMES_SSH_USER` — see the package
> top-level README, Section 2). Set them to match your inventory before
> re-running experiments; the defaults assume subnet `10.10.101`, no bastion,
> user `ubuntu`.

## Regenerating the figures

Convergence — RQ1:
```bash
cd convergence_test
python3 -m venv .venv && ./.venv/bin/pip install -q pandas numpy matplotlib pytz
./.venv/bin/python code/main.py replication          # writer/readers figure
./.venv/bin/python code/combined_conflict.py         # two-client figure (both policies, side by side)
# main.py also accepts conflict_1 / conflict_eventual for the panels on their own
# -> output_img/<scenario>/…/execution_time_analysis[_combined].pdf
```
`code/main.py` aggregates every `data/<scenario>/*.zip` not prefixed with `_`.
Node labels come from `code/config.py` (`domains`).

Micro benchmarks — RQ2/RQ3/RQ4:
```bash
cd micro_bench
python3 -m venv .venv && ./.venv/bin/pip install -q pandas numpy matplotlib scipy pytz
./.venv/bin/python scalability_graph_generator.py    # data/scalability/ -> output_img/scalability/
./.venv/bin/python accesses_graph_generator.py       # data/variable_accesses/ -> output_img/variable_accesses/
./.venv/bin/python round_graph_generator.py          # data/rounds/ -> output_img/rounds/
```
Each generator reads a fixed list of per-configuration CSVs (`SERIES`/`CONFIGS`
at the top of the script) and produces the paper figure(s) in `output_img/`.
The scalability generator emits an average (linear-y) and a median (log-y, the
one used in the paper) variant, each a 2×3 grid of the three configurations by
the two consistency policies.

## Running the experiments

### Convergence benchmark — RQ1

Requires the **Ermes (stateful)** configuration deployed (RQ1 has no baselines).
From `convergence_test/clients/`:
```bash
bash run_replication.sh        # state replication (one writer, four readers)
bash run_conflict_1.sh         # two clients, sequential consistency
bash run_conflict_eventual.sh  # two clients, eventual consistency
```
Each script cross-compiles the Go clients, flushes the platform, runs the
scenario, downloads the client CSV traces and the per-node logs, and archives
everything to `data/<scenario>/<scenario>_<timestamp>.zip` (timestamped, never
overwritten).

### Micro benchmarks — RQ2/RQ3/RQ4

Config-agnostic: they measure whatever configuration is currently deployed.
From `micro_bench/clients/`:
```bash
bash run_experiment.sh <mode> <experiment>
# <mode>:       sequential | eventual | all
# <experiment>: scalability (default) | density | moving
```
- `scalability`: varies users (1..1024) and collections (1..1000).
- `density`: varies the number of state operations per function (1..10).
- `moving`: fixed u64/c1000; users migrate across the edge nodes every 5 epochs.

The experiment runs in a tmux session (`experiment`) on the client machine.
When it finishes:
```bash
bash download_results.sh       # -> clients/results/<timestamp>/
```
Key files: `final_global_summary.csv` (whole-run summary),
`final_global_summary_steady_state.csv` (same, transient removed),
`final_global_rounds.csv` (per-epoch metrics).

Save each file under `micro_bench/data/` with the deployed configuration's
name (`distributed`, `centralized`, `cloud_only`) as shown in the top-level
README (Section 8), then regenerate the figures.
