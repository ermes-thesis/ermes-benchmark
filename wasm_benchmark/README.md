# WASM Benchmark Suite

This benchmark suite compares the performance of WebAssembly (WASM) in the context of the Ermes Framework. 
It evaluates various WASM runtimes against native binary execution to measure time and memory overheads.

## Tested Algorithms

The script benchmarks the following algorithms:

1. **Fibonacci** (input: 40)
    - Exponential recursive fibonacci calculation
    - Tests function call overhead and recursion

2. **PrimeNumbers** (input: 2,000,000)
    - Prime number counting
    - Tests loop performance and arithmetic operations

3. **TailFibonacci** (input: 20,000)
    - Linear Tail-recursive fibonacci
    - Tests performance tail calls

4. **Lightweight** (input: 20,000)
    - Lightweight computational task
    - Tests minimal overhead scenarios

5. **HostFns** (input: 10 - Not used)
    - Host function calls
    - Tests WASM-to-host communication overhead

### WASM Runtime Configurations

Each algorithm is tested with:
- **Native binary** (baseline)
- **WasmEdge**: Interpreter (NoOpts/WithOpts), AOT (NoOpts/WithOpts)
- **Wasmtime**: JIT (NoOpts/WithOpts), AOT (NoOpts/WithOpts)
- **Wazero**: Interpreter (NoOpts/WithOpts), AOT (NoOpts/WithOpts)


## Prerequisites

Before running the benchmark script, ensure you have the following installed:

- **GNU time**: For memory measurements (usually at `/usr/bin/time`)
    - Ubuntu/Debian: `apt-get install time`

- **bc**: For mathematical calculations
    - Ubuntu/Debian: `apt-get install bc`

## Build binaries
Before running benchmarks, you need to build the binaries.
From the `wasm_benchmark` directory, run:
```bash
./build.sh --enable-opts
```

## Running the time benchmarks

If you use Goland, you can run the `Run time benchmark` configuration directly.
Alternatively, you can run the benchmark from the terminal:

```bash
go test -bench Benchmark -v -benchtime=10s -benchmem -run ^$ wasm_benchmark > results.json
```

This command will execute the time benchmarks and save the results to `results.json`.

TO generate graphs from the results, you can use the `genWasmBenchGraph.py` script:

```bash
python3 genWasmBenchGraph.py
```

## Running the memory benchmarks

> Note: this section was written when time benchmark were performed with `hyperfine`.
> Please ignore any reference to time benchmark in this section.

```bash
./start_bench.sh [OPTIONS]
```

### Default Behavior

Running the script without any options will:
- Skip rebuilding binaries (uses existing ones)
- Perform both time and memory benchmarks
- Use 15 warmup runs
- Use 20 benchmark runs
- Save results to `benchmark_results/{TIMESTAMP}/`

### Command-Line Options

#### Benchmark Control

| Option | Long Form | Description | Default |
|--------|-----------|-------------|---------|
| `-dm` | `--disable-mem-bench` | Skip memory benchmarking | Enabled |
| `-dt` | `--disable-time-bench` | Skip time benchmarking | Enabled |
| `-w NUM` | `--warmup NUM` | Set number of warmup runs | 15 |
| `-r NUM` | `--runs NUM` | Set number of benchmark runs | 20 |

#### Build Control

| Option | Long Form | Description | Default |
|--------|-----------|-------------|---------|
| `-b` | `--build` | Rebuild binaries before benchmarking | Skip build |
| `-eo` | `--enable-opts` | Enable Go compiler optimizations | Disabled |
| `-bd DIR` | `--output-build-dir DIR` | Directory for built binaries | `bin` |
| `-bf NAME` | `--output-build-filename NAME` | Test binary filename | `built_test.test` |

#### Output Control

| Option | Long Form | Description | Default |
|--------|-----------|-------------|---------|
| `-od DIR` | `--output-dir DIR` | Results directory | `benchmark_results/{TIMESTAMP}` |
| `-h` | `--help` | Show help message | - |

### Common Usage Examples

#### 1. Quick Benchmark (Default Settings)
```bash
./start_bench.sh
```
Uses existing binaries, 15 warmup runs, 20 benchmark runs.

#### 2. Rebuild and Benchmark
```bash
./start_bench.sh --build
```
Rebuilds all binaries before running benchmarks.

#### 3. Fast Testing (Fewer Runs)
```bash
./start_bench.sh --warmup 5 --runs 10
```
Useful for quick testing.

#### 4. Memory-Only Benchmark
```bash
./start_bench.sh --disable-time-bench
```
Only measures memory consumption, skips timing.

#### 5. Time-Only Benchmark
```bash
./start_bench.sh --disable-mem-bench
```
Only measures execution time, skips memory profiling.

#### 6. Custom Output Directory
```bash
./start_bench.sh --output-dir my_results
```
Saves results to a custom directory.

#### 7. Build with Optimizations
```bash
./start_bench.sh --build --enable-opts
```
Rebuilds binaries with Go compiler optimizations enabled.

#### 8. Production Benchmark
```bash
./start_bench.sh --build --warmup 30 --runs 50 --output-dir production_results
```
Comprehensive benchmark with more runs for higher statistical confidence.

### Output Files

Results are saved to `$RESULTS_DIR` (default: `benchmark_results/{TIMESTAMP}/`):

#### Summary Files

- **`summary_{TIMESTAMP}.md`**: Complete overview of configuration and results

#### Timing Results

- **`timing_all_scenarios_{TIMESTAMP}.md`**: All timing data with NET calculations
- **`timing_all_scenarios_{TIMESTAMP}.json`**: Combined JSON for all scenarios
- Individual JSON files per runtime configuration

#### Memory Results

- **`memory_results_{TIMESTAMP}.txt`**: All memory data with NET calculations and statistics

### Understanding Results

#### Memory Measurements

Each memory measurement is the **average of N runs** (where N = `--runs` value):
- **Mean**: Average maximum resident set size (RSS)
- **Std Dev**: Standard deviation of measurements
- **Min/Max**: Range of observed values

#### NET Calculations

**NET** values represent pure computational cost after removing WASM runtime overhead:

```
NET Execution Time = Total Time - Overhead Time
NET Memory = Total Memory - Overhead Memory
NET Std Dev = sqrt(σ_total² + σ_overhead²)
```

Native binaries have no overhead calculations as overhead is negligible.

### Performance Tips

1. **Close unnecessary applications** before benchmarking
2. **Use consistent hardware state** (plugged in, no thermal throttling)
3. **Run multiple times** to verify consistency
4. **Increase runs** for more statistical confidence: `--warmup 30 --runs 50`
5. **Disable CPU frequency scaling** if available on your system

### Troubleshooting

#### "hyperfine is not installed"
```bash
# Ubuntu/Debian
apt install hyperfine
```

#### "GNU time not found"
Install GNU time package for your system.

#### "bc (calculator) is not installed"
```bash
# Ubuntu/Debian
apt-get install bc
```

#### Script fails during build
Make sure you have:
- Go compiler installed
- Proper permissions for the build directory

### Advanced Usage

#### Combining Options
```bash
./start_bench.sh \
  --build \
  --enable-opts \
  --warmup 20 \
  --runs 30 \
  --output-dir comprehensive_results \
  --output-build-dir custom_bin
```

#### Scripting with the Benchmark
```bash
# Run multiple benchmarks with different configurations
for runs in 10 20 50; do
  ./start_bench.sh --runs $runs --output-dir "results_${runs}_runs"
done
```

### Exit Codes

- **0**: Success
- **1**: Error (missing dependencies, invalid arguments, runtime failure)

### Notes

- The script includes error handling with detailed error messages
- Press **Ctrl+C** at the prompt to cancel before benchmarking starts
- Results include timestamps for easy comparison across runs
- All file paths are relative to the script directory


## Running the memory timeline benchmarks

To run memory timeline benchmarks, use the `trace_memory.sh` script:

```bash
./trace_memory.sh [OPTIONS]
```

Running the script without any options will:
- Trace memory usage over time for all WASM runtimes
- Save results to `benchmark_results_timeline/{TIMESTAMP}/`
- Generate plots for memory usage over time

## Running the scalability benchmarks

If you use Goland, you can run the `Scalability Test` configuration directly.
Alternatively, you can run the benchmark from the terminal:
```bash
go test -run TestScalability_ wasm_benchmark
```

This command will execute the scalability benchmarks and save the results in `scalability_results.json`.
You can generate graphs from the results using the `gen_scalability_graphs.py` script:

```bash
python3 gen_scalability_graphs.py
```