#!/bin/bash

set -eEuo pipefail
trap 'echo -e "\n${RED}❌ ERROR: Command failed at line $LINENO: $BASH_COMMAND${NC}\n"' ERR

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parts of the bench suite to execute
DO_MEM_BENCH=true
DO_TIME_BENCH=true
SKIP_BINARY_BUILD=true

# Configuration benchmarks (Default values)
WARMUP_RUNS=15
BENCH_RUNS=20
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="benchmark_results/$TIMESTAMP"

# Configuration build
DISABLE_OPTS=true
OUTPUT_BUILD_DIR="bin"
TEST_COMPILED_FILENAME="built_test.test"
TEST_COMPILED_PATH="${OUTPUT_BUILD_DIR}/${TEST_COMPILED_FILENAME}"

# WASM binary path prefixes
BINARY_FIBONACCI_PATH_PREFIX="_WASM_BINARIES/cpuIntensive/fibonacci"
BINARY_PRIMENUM_PATH_PREFIX="_WASM_BINARIES/cpuIntensive/primeNums"
BINARY_TAILFIBONACCI_PATH_PREFIX="_WASM_BINARIES/cpuIntensive/tailFibonacci"
BINARY_HOSTFNS_PATH_PREFIX="_WASM_BINARIES/hostFns"
BINARY_LIGHTWEIGHT_PATH_PREFIX="_WASM_BINARIES/lightweight"

# Native binary paths
NATIVE_FIBONACCI_PATH="./bin/native_fibonacci"
NATIVE_PRIMENUM_PATH="./bin/native_primeNums"
NATIVE_TAILFIBONACCI_PATH="./bin/native_tailFibonacci"
NATIVE_LIGHTWEIGHT_PATH="./bin/native_lightweight"

# Test configurations
# Format: "ConfigName:WasmFile:Runtime:IsInterpreter:RegisterHostFn:FunctionInput"
TEST_CONFIGS=(
    # Fibonacci - Native first, then WASM configurations
    "Fibonacci_Native:NATIVE:${NATIVE_FIBONACCI_PATH}:40"
    "Fibonacci_Wasmedge_Interpreter_NoOpts:${BINARY_FIBONACCI_PATH_PREFIX}/fibonacci.wasm:wasmedge:false:false:40"
    "Fibonacci_Wasmedge_Interpreter_WithOpts:${BINARY_FIBONACCI_PATH_PREFIX}/fibonacci_wOpts.wasm:wasmedge:false:false:40"
    "Fibonacci_Wasmedge_AOT_NoOpts:${BINARY_FIBONACCI_PATH_PREFIX}/fibonacci_noOpts_AOTwasmedge.wasm:wasmedge:false:false:40"
    "Fibonacci_Wasmedge_AOT_WithOpts:${BINARY_FIBONACCI_PATH_PREFIX}/fibonacci_wOpts_AOTwasmedge.wasm:wasmedge:false:false:40"
    "Fibonacci_Wasmtime_JIT_NoOpts:${BINARY_FIBONACCI_PATH_PREFIX}/fibonacci.wasm:wasmtime:false:false:40"
    "Fibonacci_Wasmtime_JIT_WithOpts:${BINARY_FIBONACCI_PATH_PREFIX}/fibonacci_wOpts.wasm:wasmtime:false:false:40"
    "Fibonacci_Wasmtime_AOT_NoOpts:${BINARY_FIBONACCI_PATH_PREFIX}/fibonacci_noOpts_AOTwasmtime.wasm:wasmtime:true:false:40"
    "Fibonacci_Wasmtime_AOT_WithOpts:${BINARY_FIBONACCI_PATH_PREFIX}/fibonacci_wOpts_AOTwasmtime.wasm:wasmtime:true:false:40"
    "Fibonacci_Wazero_Interpreter_NoOpts:${BINARY_FIBONACCI_PATH_PREFIX}/fibonacci.wasm:wazero:false:false:40"
    "Fibonacci_Wazero_Interpreter_WithOpts:${BINARY_FIBONACCI_PATH_PREFIX}/fibonacci_wOpts.wasm:wazero:false:false:40"
    "Fibonacci_Wazero_AOT_NoOpts:${BINARY_FIBONACCI_PATH_PREFIX}/fibonacci.wasm:wazero:true:false:40"
    "Fibonacci_Wazero_AOT_WithOpts:${BINARY_FIBONACCI_PATH_PREFIX}/fibonacci_wOpts.wasm:wazero:true:false:40"

    # PrimeNumbers - Native first, then WASM configurations
    "PrimeNumbers_Native:NATIVE:${NATIVE_PRIMENUM_PATH}:2000000"
    "PrimeNumbers_Wasmedge_Interpreter_NoOpts:${BINARY_PRIMENUM_PATH_PREFIX}/fnPrimeNums.wasm:wasmedge:false:false:2000000"
    "PrimeNumbers_Wasmedge_Interpreter_WithOpts:${BINARY_PRIMENUM_PATH_PREFIX}/fnPrimeNums_wOpts.wasm:wasmedge:false:false:2000000"
    "PrimeNumbers_Wasmedge_AOT_NoOpts:${BINARY_PRIMENUM_PATH_PREFIX}/fnPrimeNums_noOpts_AOTwasmedge.wasm:wasmedge:false:false:2000000"
    "PrimeNumbers_Wasmedge_AOT_WithOpts:${BINARY_PRIMENUM_PATH_PREFIX}/fnPrimeNums_wOpts_AOTwasmedge.wasm:wasmedge:false:false:2000000"
    "PrimeNumbers_Wasmtime_JIT_NoOpts:${BINARY_PRIMENUM_PATH_PREFIX}/fnPrimeNums.wasm:wasmtime:false:false:2000000"
    "PrimeNumbers_Wasmtime_JIT_WithOpts:${BINARY_PRIMENUM_PATH_PREFIX}/fnPrimeNums_wOpts.wasm:wasmtime:false:false:2000000"
    "PrimeNumbers_Wasmtime_AOT_NoOpts:${BINARY_PRIMENUM_PATH_PREFIX}/fnPrimeNums_noOpts_AOTwasmtime.wasm:wasmtime:true:false:2000000"
    "PrimeNumbers_Wasmtime_AOT_WithOpts:${BINARY_PRIMENUM_PATH_PREFIX}/fnPrimeNums_wOpts_AOTwasmtime.wasm:wasmtime:true:false:2000000"
    "PrimeNumbers_Wazero_Interpreter_NoOpts:${BINARY_PRIMENUM_PATH_PREFIX}/fnPrimeNums.wasm:wazero:false:false:2000000"
    "PrimeNumbers_Wazero_Interpreter_WithOpts:${BINARY_PRIMENUM_PATH_PREFIX}/fnPrimeNums_wOpts.wasm:wazero:false:false:2000000"
    "PrimeNumbers_Wazero_AOT_NoOpts:${BINARY_PRIMENUM_PATH_PREFIX}/fnPrimeNums.wasm:wazero:true:false:2000000"
    "PrimeNumbers_Wazero_AOT_WithOpts:${BINARY_PRIMENUM_PATH_PREFIX}/fnPrimeNums_wOpts.wasm:wazero:true:false:2000000"

    # TailFibonacci - Native first, then WASM configurations
    "TailFibonacci_Native:NATIVE:${NATIVE_TAILFIBONACCI_PATH}:20000"
    "TailFibonacci_Wasmedge_Interpreter_NoOpts:${BINARY_TAILFIBONACCI_PATH_PREFIX}/tailFibonacci.wasm:wasmedge:false:false:20000"
    "TailFibonacci_Wasmedge_Interpreter_WithOpts:${BINARY_TAILFIBONACCI_PATH_PREFIX}/tailFibonacci_wOpts.wasm:wasmedge:false:false:20000"
    "TailFibonacci_Wasmedge_AOT_NoOpts:${BINARY_TAILFIBONACCI_PATH_PREFIX}/tailFibonacci_noOpts_AOTwasmedge.wasm:wasmedge:false:false:20000"
    "TailFibonacci_Wasmedge_AOT_WithOpts:${BINARY_TAILFIBONACCI_PATH_PREFIX}/tailFibonacci_wOpts_AOTwasmedge.wasm:wasmedge:false:false:20000"
    "TailFibonacci_Wasmtime_JIT_NoOpts:${BINARY_TAILFIBONACCI_PATH_PREFIX}/tailFibonacci.wasm:wasmtime:false:false:20000"
    "TailFibonacci_Wasmtime_JIT_WithOpts:${BINARY_TAILFIBONACCI_PATH_PREFIX}/tailFibonacci_wOpts.wasm:wasmtime:false:false:20000"
    "TailFibonacci_Wasmtime_AOT_NoOpts:${BINARY_TAILFIBONACCI_PATH_PREFIX}/tailFibonacci_noOpts_AOTwasmtime.wasm:wasmtime:true:false:20000"
    "TailFibonacci_Wasmtime_AOT_WithOpts:${BINARY_TAILFIBONACCI_PATH_PREFIX}/tailFibonacci_wOpts_AOTwasmtime.wasm:wasmtime:true:false:20000"
    "TailFibonacci_Wazero_Interpreter_NoOpts:${BINARY_TAILFIBONACCI_PATH_PREFIX}/tailFibonacci.wasm:wazero:false:false:20000"
    "TailFibonacci_Wazero_Interpreter_WithOpts:${BINARY_TAILFIBONACCI_PATH_PREFIX}/tailFibonacci_wOpts.wasm:wazero:false:false:20000"
    "TailFibonacci_Wazero_AOT_NoOpts:${BINARY_TAILFIBONACCI_PATH_PREFIX}/tailFibonacci.wasm:wazero:true:false:20000"
    "TailFibonacci_Wazero_AOT_WithOpts:${BINARY_TAILFIBONACCI_PATH_PREFIX}/tailFibonacci_wOpts.wasm:wazero:true:false:20000"

    # Lightweight - Native first, then WASM configurations
    "Lightweight_Native:NATIVE:${NATIVE_LIGHTWEIGHT_PATH}:20000"
    "Lightweight_Wasmedge_Interpreter_NoOpts:${BINARY_LIGHTWEIGHT_PATH_PREFIX}/lightweight.wasm:wasmedge:false:false:20000"
    "Lightweight_Wasmedge_Interpreter_WithOpts:${BINARY_LIGHTWEIGHT_PATH_PREFIX}/lightweight_wOpts.wasm:wasmedge:false:false:20000"
    "Lightweight_Wasmedge_AOT_NoOpts:${BINARY_LIGHTWEIGHT_PATH_PREFIX}/lightweight_noOpts_AOTwasmedge.wasm:wasmedge:false:false:20000"
    "Lightweight_Wasmedge_AOT_WithOpts:${BINARY_LIGHTWEIGHT_PATH_PREFIX}/lightweight_wOpts_AOTwasmedge.wasm:wasmedge:false:false:20000"
    "Lightweight_Wasmtime_JIT_NoOpts:${BINARY_LIGHTWEIGHT_PATH_PREFIX}/lightweight.wasm:wasmtime:false:false:20000"
    "Lightweight_Wasmtime_JIT_WithOpts:${BINARY_LIGHTWEIGHT_PATH_PREFIX}/lightweight_wOpts.wasm:wasmtime:false:false:20000"
    "Lightweight_Wasmtime_AOT_NoOpts:${BINARY_LIGHTWEIGHT_PATH_PREFIX}/lightweight_noOpts_AOTwasmtime.wasm:wasmtime:true:false:20000"
    "Lightweight_Wasmtime_AOT_WithOpts:${BINARY_LIGHTWEIGHT_PATH_PREFIX}/lightweight_wOpts_AOTwasmtime.wasm:wasmtime:true:false:20000"
    "Lightweight_Wazero_Interpreter_NoOpts:${BINARY_LIGHTWEIGHT_PATH_PREFIX}/lightweight.wasm:wazero:false:false:20000"
    "Lightweight_Wazero_Interpreter_WithOpts:${BINARY_LIGHTWEIGHT_PATH_PREFIX}/lightweight_wOpts.wasm:wazero:false:false:20000"
    "Lightweight_Wazero_AOT_NoOpts:${BINARY_LIGHTWEIGHT_PATH_PREFIX}/lightweight.wasm:wazero:true:false:20000"
    "Lightweight_Wazero_AOT_WithOpts:${BINARY_LIGHTWEIGHT_PATH_PREFIX}/lightweight_wOpts.wasm:wazero:true:false:20000"

    # HostFns - Always Register Host Functions
    "HostFns_Wasmedge_Interpreter_NoOpts:${BINARY_HOSTFNS_PATH_PREFIX}/functionCreateCollections.wasm:wasmedge:false:true:10"
    "HostFns_Wasmedge_Interpreter_WithOpts:${BINARY_HOSTFNS_PATH_PREFIX}/functionCreateCollections_wOpts.wasm:wasmedge:false:true:10"
    "HostFns_Wasmedge_AOT_NoOpts:${BINARY_HOSTFNS_PATH_PREFIX}/functionCreateCollections_noOpts_AOTwasmedge.wasm:wasmedge:false:true:10"
    "HostFns_Wasmedge_AOT_WithOpts:${BINARY_HOSTFNS_PATH_PREFIX}/functionCreateCollections_wOpts_AOTwasmedge.wasm:wasmedge:false:true:10"
    "HostFns_Wasmtime_JIT_NoOpts:${BINARY_HOSTFNS_PATH_PREFIX}/functionCreateCollections.wasm:wasmtime:false:true:10"
    "HostFns_Wasmtime_JIT_WithOpts:${BINARY_HOSTFNS_PATH_PREFIX}/functionCreateCollections_wOpts.wasm:wasmtime:false:true:10"
    "HostFns_Wasmtime_AOT_NoOpts:${BINARY_HOSTFNS_PATH_PREFIX}/functionCreateCollections_noOpts_AOTwasmtime.wasm:wasmtime:true:true:10"
    "HostFns_Wasmtime_AOT_WithOpts:${BINARY_HOSTFNS_PATH_PREFIX}/functionCreateCollections_wOpts_AOTwasmtime.wasm:wasmtime:true:true:10"
    "HostFns_Wazero_Interpreter_NoOpts:${BINARY_HOSTFNS_PATH_PREFIX}/functionCreateCollections.wasm:wazero:false:true:10"
    "HostFns_Wazero_Interpreter_WithOpts:${BINARY_HOSTFNS_PATH_PREFIX}/functionCreateCollections_wOpts.wasm:wazero:false:true:10"
    "HostFns_Wazero_AOT_NoOpts:${BINARY_HOSTFNS_PATH_PREFIX}/functionCreateCollections.wasm:wazero:true:true:10"
    "HostFns_Wazero_AOT_WithOpts:${BINARY_HOSTFNS_PATH_PREFIX}/functionCreateCollections_wOpts.wasm:wazero:true:true:10"
)

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -dm|--disable-mem-bench)
            DO_MEM_BENCH=false
            shift
            ;;
        -dt|--disable-time-bench)
            DO_TIME_BENCH=false
            shift
            ;;
        -b|--build)
            SKIP_BINARY_BUILD=false
            shift
            ;;
        -w|--warmup)
            shift
            if [[ $# -gt 0 ]]; then
              WARMUP_RUNS=$1
            else
              echo "must specify a number of warmup runs"
              exit 1
            fi
            shift
            ;;
        -r|--runs)
            shift
            if [[ $# -gt 0 ]]; then
              BENCH_RUNS=$1
            else
              echo "must specify a number of benchmark runs"
              exit 1
            fi
            shift
            ;;
        -od|--output-dir)
            shift
            if [[ $# -gt 0 ]]; then
              RESULTS_DIR=$1
            else
              echo "must specify a valid dir name"
              exit 1
            fi
            shift
            ;;
        -bd|--output-build-dir)
            shift
            if [[ $# -gt 0 ]]; then
              OUTPUT_BUILD_DIR=$1
            else
              echo "must specify a valid dir name"
              exit 1
            fi
            shift
            ;;
        -bf|--output-build-filename)
            shift
            if [[ $# -gt 0 ]]; then
              TEST_COMPILED_FILENAME=$1
            else
              echo "must specify a valid filename"
              exit 1
            fi
            shift
            ;;
        -eo|--enable-opts)
            DISABLE_OPTS=false
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -dm, --disable-mem-bench        Disable memory benchmarking of the binaries (default: Memory benchmarking enabled)"
            echo "  -dt, --disable-time-bench       Disable time benchmarking of the binaries (default: Time benchmarking enabled)"
            echo "  -b,  --build                    Build the binaries needed for benchmark (default: Binaries build skipped)"
            echo "  -w,  --warmup                   Specify how many warmup runs perform (default: 15)"
            echo "  -r,  --runs                     Specify how many benchmark runs perform (default: 20)"
            echo "  -od, --output-dir               Directory where to place benchmark results (default: 'benchmark_results/{Timestamp}'"
            echo "  -bd, --output-build-dir         Directory where to place the built binary (default: 'bin')"
            echo "  -bf, --output-build-filename    Filename of the built test binary (default: 'built_test.test')"
            echo "  -eo, --enable-opts              Enable Go compiler optimizations (default: Opts disabled)"
            echo "  -h,  --help                     Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                          # Perform benchmarking with default settings and without re-building binaries"
            echo "  $0 --disable-mem-bench      # Skip memory benchmarking"
            echo "  $0 --disable-time-bench     # Skip time benchmarking"
            echo "  $0 --build                  # Perform benchmarking re-building the binaries"
            echo "  $0 --warmup 5 --runs 10     # Perform benchmarking with 5 warmup runs and 10 benchmark runs"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

print_header "WASM vs Native Benchmark Suite"

echo "Configuration:"
echo "  Warmup runs: $WARMUP_RUNS"
echo "  Benchmark runs: $BENCH_RUNS"
echo "  Results directory: $RESULTS_DIR"
echo "  Timestamp: $TIMESTAMP"
echo "  Do memory benchmark: $DO_MEM_BENCH"
echo "  Do time benchmark: $DO_TIME_BENCH"
echo "  -------------------------------------------------------------"
echo "  Skip binaries build: $SKIP_BINARY_BUILD"
echo "  Build without optimizations (ignored if build is skipped): $DISABLE_OPTS"
echo "  Output binaries folder: $OUTPUT_BUILD_DIR"
echo "  Test compiled binary filename: $TEST_COMPILED_FILENAME"
echo "  Test compiled binary path: $TEST_COMPILED_PATH"
echo ""
echo "Test configurations (${#TEST_CONFIGS[@]}):"
for config in "${TEST_CONFIGS[@]}"; do
    IFS=':' read -r config_name _ _ _ _ _ <<< "$config"
    echo "  - $config_name"
done
echo ""
echo "Memory measurements will be averaged over $BENCH_RUNS runs per configuration"
echo ""

# Check if hyperfine is installed
if ! command -v hyperfine &> /dev/null; then
    echo -e "${RED}ERROR: hyperfine is not installed${NC}"
    echo "Install with: cargo install hyperfine"
    exit 1
fi

# Check if GNU time is available
if ! /usr/bin/time --version &> /dev/null 2>&1; then
    echo -e "${YELLOW}WARNING: GNU time not found at /usr/bin/time${NC}"
    echo "Memory benchmarks may not work correctly"
    exit 1
fi

# Check if bc is available (needed for calculations)
if ! command -v bc &> /dev/null; then
    echo -e "${RED}ERROR: bc (calculator) is not installed${NC}"
    echo "Install with: apt-get install bc (Ubuntu/Debian) or brew install bc (macOS)"
    exit 1
fi

read -p "Press Enter to start benchmarking or Ctrl+C to cancel..."

# Create results directory
mkdir -p "$RESULTS_DIR"

if [[ "$SKIP_BINARY_BUILD" == false ]]; then
    build_flags=()
    if [[ "$DISABLE_OPTS" == false ]]; then
        build_flags+=("--enable-opts")
    fi
    build_flags+=("--output-build-dir" "$OUTPUT_BUILD_DIR")
    build_flags+=("--output-build-filename" "$TEST_COMPILED_FILENAME")

    /bin/bash ./build.sh "${build_flags[@]}"
fi

#if [[ "$DO_TIME_BENCH" == true ]]; then
#  export SKIP_TIME_BENCH_INTERACTIVE=1
#  export TEST_CONFIGS_ENV="${TEST_CONFIGS[*]}"
#
#  /bin/bash ./time_bench.sh --warmup "$WARMUP_RUNS" --runs "$BENCH_RUNS" --output-dir "$RESULTS_DIR" --compiled-binary "$TEST_COMPILED_PATH"
#fi

if [[ "$DO_MEM_BENCH" == true ]]; then
  export SKIP_MEM_BENCH_INTERACTIVE=1
  export TEST_CONFIGS_ENV="${TEST_CONFIGS[*]}"

  /bin/bash ./mem_bench.sh --warmup "$WARMUP_RUNS" --runs "$BENCH_RUNS" --output-dir "$RESULTS_DIR" --compiled-binary "$TEST_COMPILED_PATH"
fi

# Function to generate summary
generate_summary() {
    print_header "GENERATING SUMMARY"

    local summary_file="$RESULTS_DIR/summary_${TIMESTAMP}.md"

    ALGORITHMS=()
    RUNTIMES=()

    for entry in "${TEST_CONFIGS[@]}"; do
        IFS=':' read -r first_part _ <<< "$entry"
        alg="${first_part%%_*}"       # everything before first "_"
        runtime="${first_part#*_}"     # everything after first "_"

        ALGORITHMS+=("$alg")
        RUNTIMES+=("$runtime")
    done

    readarray -t UNIQUE_ALGORITHMS < <(printf "%s\n" "${ALGORITHMS[@]}" | sort -u)
    readarray -t UNIQUE_RUNTIMES < <(printf "%s\n" "${RUNTIMES[@]}" | sort -u)

    cat > "$summary_file" << EOF
# WASM vs Native Performance Benchmark Summary
Generated: $(date)

## Configuration
- Warmup Runs: $WARMUP_RUNS
- Benchmark Runs: $BENCH_RUNS (used for both timing and memory measurements)
- Algorithms Tested: ${#UNIQUE_ALGORITHMS[@]}
- Runtime Configurations: ${#UNIQUE_RUNTIMES[@]}

## Test Configs
EOF

    for alg in "${UNIQUE_ALGORITHMS[@]}"; do
        echo "- $alg" >> "$summary_file"
    done

    cat >> "$summary_file" << EOF

## Runtime Configurations
EOF

    for runtime_config in "${UNIQUE_RUNTIMES[@]}"; do
        echo "- $runtime_config" >> "$summary_file"
    done

    cat >> "$summary_file" << EOF

## Result Files
All detailed results are stored in: \`$RESULTS_DIR/\`

### Main Result Files (Use These for Analysis)

#### Timing Results
- \`timing_all_scenarios_${TIMESTAMP}.md\` - **All timing data including NET calculations**
- \`timing_all_scenarios_${TIMESTAMP}.json\` - Combined JSON for all scenarios

#### Memory Results
- \`memory_results_${TIMESTAMP}.txt\` - **All memory data including NET calculations with statistics**

### Individual JSON Files (For Detailed Analysis)

#### Main Execution Times
EOF

    for runtime in "${UNIQUE_RUNTIMES[@]}"; do
        echo "- \`timing_${runtime}_${TIMESTAMP}.json\` - JSON data for $scenario" >> "$summary_file"
    done

    cat >> "$summary_file" << EOF

#### Overhead Execution Times
EOF

    for runtime in "${UNIQUE_RUNTIMES[@]}"; do
        echo "- \`timing_overheads_${runtime}_${TIMESTAMP}.json\` - Overhead JSON for $scenario" >> "$summary_file"
    done

    cat >> "$summary_file" << EOF

## Understanding Results

### Memory Measurements
Each memory measurement is the **average of $BENCH_RUNS runs**, reported as:
- **Mean**: Average maximum resident set size (RSS) across all runs
- **Std Dev**: Standard deviation showing measurement variability
- **Min/Max**: Range of values observed across all runs

### NET Calculations

**NET Execution Time** and **NET Memory** represent the pure computational cost after removing WASM runtime overhead.

#### Formula:
\`\`\`
NET Execution Time = Total Execution Time - Overhead Time
NET Memory = Total Memory - Overhead Memory
NET Standard Deviation = sqrt(σ_total² + σ_overhead²)
\`\`\`

#### Where to Find:
- **Timing**: Check the "NET EXECUTION TIME" section in \`timing_all_scenarios_${TIMESTAMP}.md\`
- **Memory**: Check the "NET MEMORY CONSUMPTION" section in \`memory_all_scenarios_${TIMESTAMP}.txt\`

#### Note:
- Native runtime has no overhead calculations (overhead is negligible)
- NET values show the true performance after accounting for WASM runtime costs
- Standard deviations are combined using the quadrature method for independent measurements
- Memory measurements use $BENCH_RUNS runs (same as timing) for statistical reliability

## Statistical Reliability
- **Timing**: Hyperfine performs $WARMUP_RUNS warmup runs + $BENCH_RUNS benchmark runs
- **Memory**: Each measurement averaged over $BENCH_RUNS independent runs
- **Outliers**: Check raw data files to identify any anomalous measurements
- **Reproducibility**: Rerun the script to verify consistency of results
EOF

    echo -e "${GREEN}✓ Summary saved to: $summary_file${NC}"
}

generate_summary

