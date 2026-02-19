# Ermes distributed benchmark

This benchmark suite compares the performance of the Ermes Framework in a distributed setting.

The suite is composed of two main components:
1. **[Convergence Benchmark](convergence_test)**: Evaluates the time taken for a distributed computation to converge across multiple nodes.
2. **[System Benchmark](micro_bench)**: Measures the throughput of the system under varying loads and configurations

## Prerequisites
Before running the benchmark you need deploy the Ermes Framework on a cluster of machines. Follow the deployment instructions in the [Ermes deploy](https://github.com/ermes-thesis/ermes-deploy) repository.

Moreover, you need to install the ermes-cli tool on your local machine to interact with the cluster. You can find the installation instructions in the [Ermes CLI](https://github.com/ermes-thesis/ermes-cli)

> Note: all scripts contains hardcoded IP addresses and ports. Make sure to update them according to your cluster configuration.

### Deploy serverless functions
To run the benchmarks, you need to deploy the serverless functions on the cluster. From the `serverless_function` directory, run:
```bash
./deploy.sh
```
This will deploy the necessary serverless functions on the function registry.

>Note: the function registry address is hardcoded in the `deploy.sh` script
> and must be reached from your local machine.

## Running the benchmarks

### Convergence Benchmark
To run the convergence benchmark, navigate to the `convergence_test/clients` directory.
This folder contains the scripts to run each convergence benchmark on the clients. 

To run the `full_traversal` benchmark, execute the following command:
```bash
  ./run_full_traversal.sh
```
This will run the convergence benchmark and save the results in `convergence_test/data/full_traversal`.

To generate the plots for the convergence benchmark, navigate to the `convergence_test/code` directory and run:
```bash
  python3 main.py <experiment_name>
```
This will generate the plots for the specified experiment and save them in `convergence_test/output_img`.


### System Benchmark
To run the system benchmark, navigate to the `micro_bench/clients` directory.
This folder contains the `run_experiment.sh` script that allows you to run the system benchmark with different configurations.
To run the system benchmark with a specific configuration, execute the following command:
```bash
  ./run_experiment.sh <consistency_models> <experiment_name>
```
Accepted values for <consistency_models> are:
- `sequential`
- `eventual`
- `all`

Accepted values for `<experiment_name>` are:
- `scalability` (default): this will run the benchmark with a variable number of users and collection.
- `density`: this will run the benchmark with a variable number of state access per function.
- `moving`: this will run the benchmark with a moving users.

To download the results of the system benchmark, navigate to the `micro_bench/clients` directory and run:
```bash
  ./download_results.sh
```
This will download the results of the system benchmark and save them in `micro_bench/clients/results/<timestamp>`.
Most important files are:
- `final_global_summary.csv`: this file contains the summary of the benchmark results, including the throughput and latency for each configuration.
- `final_global_summary.csv`: the same as above but removing data before convergence.
- `final_global_rounds.csv`: results for each round of the benchmark, including the latency for each round.

You need to manually move the downloaded results to `micro_bench/data` and rename in the appropriate way to generate the plots.
See the `micro_bench/data` directory for an example of how to organize the data for the plot generation.

To generate the plots for the system benchmark, navigate to the `micro_bench` directory and run one of the following scripts:
```bash
  python3 scalability_graph_generator.py
  python3 accesses_graph_generator.py
  python3 round_graph_generator.py
```