# WASM vs Native Benchmark Suite - Usage Guide

## Overview

This benchmark suite compares the performance of WebAssembly (WASM) runtimes against native binaries across multiple algorithms and configurations. It measures both execution time and memory consumption.

## Prerequisites

Before running the benchmark script, ensure you have the following installed:

- **hyperfine**: For time benchmarking
  - Ubuntu/Debian: `apt install hyperfine`

- **GNU time**: For memory measurements (usually at `/usr/bin/time`)
    - Ubuntu/Debian: `apt-get install time`

- **bc**: For mathematical calculations
    - Ubuntu/Debian: `apt-get install bc`

## Basic Usage

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

## Command-Line Options

### Benchmark Control

| Option | Long Form | Description | Default |
|--------|-----------|-------------|---------|
| `-dm` | `--disable-mem-bench` | Skip memory benchmarking | Enabled |
| `-dt` | `--disable-time-bench` | Skip time benchmarking | Enabled |
| `-w NUM` | `--warmup NUM` | Set number of warmup runs | 15 |
| `-r NUM` | `--runs NUM` | Set number of benchmark runs | 20 |

### Build Control

| Option | Long Form | Description | Default |
|--------|-----------|-------------|---------|
| `-b` | `--build` | Rebuild binaries before benchmarking | Skip build |
| `-eo` | `--enable-opts` | Enable Go compiler optimizations | Disabled |
| `-bd DIR` | `--output-build-dir DIR` | Directory for built binaries | `bin` |
| `-bf NAME` | `--output-build-filename NAME` | Test binary filename | `built_test.test` |

### Output Control

| Option | Long Form | Description | Default |
|--------|-----------|-------------|---------|
| `-od DIR` | `--output-dir DIR` | Results directory | `benchmark_results/{TIMESTAMP}` |
| `-h` | `--help` | Show help message | - |

## Common Usage Examples

### 1. Quick Benchmark (Default Settings)
```bash
./benchmark.sh
```
Uses existing binaries, 15 warmup runs, 20 benchmark runs.

### 2. Rebuild and Benchmark
```bash
./benchmark.sh --build
```
Rebuilds all binaries before running benchmarks.

### 3. Fast Testing (Fewer Runs)
```bash
./benchmark.sh --warmup 5 --runs 10
```
Useful for quick testing.

### 4. Memory-Only Benchmark
```bash
./benchmark.sh --disable-time-bench
```
Only measures memory consumption, skips timing.

### 5. Time-Only Benchmark
```bash
./benchmark.sh --disable-mem-bench
```
Only measures execution time, skips memory profiling.

### 6. Custom Output Directory
```bash
./benchmark.sh --output-dir my_results
```
Saves results to a custom directory.

### 7. Build with Optimizations
```bash
./benchmark.sh --build --enable-opts
```
Rebuilds binaries with Go compiler optimizations enabled.

### 8. Production Benchmark
```bash
./benchmark.sh --build --warmup 30 --runs 50 --output-dir production_results
```
Comprehensive benchmark with more runs for higher statistical confidence.

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

## Output Files

Results are saved to `$RESULTS_DIR` (default: `benchmark_results/{TIMESTAMP}/`):

### Summary Files

- **`summary_{TIMESTAMP}.md`**: Complete overview of configuration and results

### Timing Results

- **`timing_all_scenarios_{TIMESTAMP}.md`**: All timing data with NET calculations
- **`timing_all_scenarios_{TIMESTAMP}.json`**: Combined JSON for all scenarios
- Individual JSON files per runtime configuration

### Memory Results

- **`memory_results_{TIMESTAMP}.txt`**: All memory data with NET calculations and statistics

## Understanding Results

### Memory Measurements

Each memory measurement is the **average of N runs** (where N = `--runs` value):
- **Mean**: Average maximum resident set size (RSS)
- **Std Dev**: Standard deviation of measurements
- **Min/Max**: Range of observed values

### NET Calculations

**NET** values represent pure computational cost after removing WASM runtime overhead:

```
NET Execution Time = Total Time - Overhead Time
NET Memory = Total Memory - Overhead Memory
NET Std Dev = sqrt(σ_total² + σ_overhead²)
```

Native binaries have no overhead calculations as overhead is negligible.

## Performance Tips

1. **Close unnecessary applications** before benchmarking
2. **Use consistent hardware state** (plugged in, no thermal throttling)
3. **Run multiple times** to verify consistency
4. **Increase runs** for more statistical confidence: `--warmup 30 --runs 50`
5. **Disable CPU frequency scaling** if available on your system

## Troubleshooting

### "hyperfine is not installed"
```bash
# Ubuntu/Debian
apt install hyperfine
```

### "GNU time not found"
Install GNU time package for your system.

### "bc (calculator) is not installed"
```bash
# Ubuntu/Debian
apt-get install bc
```

### Script fails during build
Make sure you have:
- Go compiler installed
- Proper permissions for the build directory

## Advanced Usage

### Combining Options
```bash
./benchmark.sh \
  --build \
  --enable-opts \
  --warmup 20 \
  --runs 30 \
  --output-dir comprehensive_results \
  --output-build-dir custom_bin
```

### Scripting with the Benchmark
```bash
# Run multiple benchmarks with different configurations
for runs in 10 20 50; do
  ./benchmark.sh --runs $runs --output-dir "results_${runs}_runs"
done
```

## Exit Codes

- **0**: Success
- **1**: Error (missing dependencies, invalid arguments, runtime failure)

## Notes

- The script includes error handling with detailed error messages
- Press **Ctrl+C** at the prompt to cancel before benchmarking starts
- Results include timestamps for easy comparison across runs
- All file paths are relative to the script directory