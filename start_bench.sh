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
OUTPUT_BUILD_DIR=bin

# Test scenarios (workloads)
SCENARIOS=(
    "PrimeNumbers"
    "Fibonacci"
    "Lightweight"
    "TailFibonacci"
)

# Runtime configurations
# Format: "RuntimeName:BinaryPrefix"
RUNTIMES=(
    "Native:native"
    #"Wasmedge_Interpreter_NoOpts:wasmedge_interpreter_noopts"
    #"Wasmedge_Interpreter_WithOpts:wasmedge_interpreter_wopts"
    "Wasmedge_AOT_NoOpts:wasmedge_aot_noopts"
    "Wasmedge_AOT_WithOpts:wasmedge_aot_wopts"
    "Wasmtime_JIT_NoOpts:wasmtime_jit_noopts"
    "Wasmtime_JIT_WithOpts:wasmtime_jit_wopts"
    "Wazero_AOT_NoOpts:wazero_aot_noopts"
    "Wazero_AOT_WithOpts:wazero_aot_wopts"
    #"Wazero_Interpreter_NoOpts:wazero_interpreter_noopts"
    #"Wazero_Interpreter_WithOpts:wazero_interpreter_wopts"
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
            DO_TIME_BENCH=true
            shift
            ;;
        -sb|--skip-build)
            SKIP_BINARY_BUILD=true
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
        -ob|--output-build-dir)
            shift
            if [[ $# -gt 0 ]]; then
              OUTPUT_BUILD_DIR=$1
            else
              echo "must specify a valid dir name"
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
            echo "  -dm, --disable-mem-bench    Disable memory benchmarking of the binaries (default: Memory benchmarking enabled)"
            echo "  -dt, --disable-time-bench   Disable time benchmarking of the binaries (default: Time benchmarking enabled)"
            echo "  -sb, --skip-build           Skip binaries building step (default: Binaries build skipped)"
            echo "  -w,  --warmup               Specify how many warmup runs perform (default: 15)"
            echo "  -r,  --runs                 Specify how many benchmark runs perform (default: 20)"
            echo "  -od, --output-dir           Directory where to place benchmark results (default: 'benchmark_results/{Timestamp}'"
            echo "  -ob, --output-build-dir     Directory where to place the build binaries (default: 'bin')"
            echo "  -eo, --enable-opts          Enable Go compiler optimizations (default: Opts disabled)"
            echo "  -h, --help                  Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                          # Build with optimizations disabled"
            echo "  $0 --disable-mem-bench      # Skip memory benchmarking"
            echo "  $0 --disable-time-bench     # Skip time benchmarking"
            echo "  $0 --skip-build             # Perform benchmarking without re-building the binaries"
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

if [[ "$SKIP_BINARY_BUILD" == false ]]; then
    build_flags=()
    if [[ "$DISABLE_OPTS" == false ]]; then
        build_flags+=("--enable-opts")
    fi
    build_flags+=("--output-build-dir" "$OUTPUT_BUILD_DIR")

    /bin/bash ./build.sh "${build_flags[@]}"
fi

print_header "WASM vs Native Benchmark Suite"

echo "Configuration:"
echo "  Warmup runs: $WARMUP_RUNS"
echo "  Benchmark runs: $BENCH_RUNS (used for timing and memory)"
echo "  Results directory: $RESULTS_DIR"
echo "  Timestamp: $TIMESTAMP"
echo ""
echo "Scenarios to test: ${SCENARIOS[*]}"
echo "Runtime configurations: ${#RUNTIMES[@]}"
echo ""
echo "Memory measurements will be averaged over $BENCH_RUNS runs per configuration"

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

if [[ "$DO_TIME_BENCH" == true ]]; then
  export SKIP_TIME_BENCH_INTERACTIVE=1
  /bin/bash ./time_bench.sh --warmup "$WARMUP_RUNS" --runs "$BENCH_RUNS" --output-dir "$RESULTS_DIR"
fi

if [[ "$DO_MEM_BENCH" == true ]]; then
  export SKIP_MEM_BENCH_INTERACTIVE=1
  /bin/bash ./mem_bench.sh --warmup "$WARMUP_RUNS" --runs "$BENCH_RUNS" --output-dir "$RESULTS_DIR"
fi

# Function to generate summary
generate_summary() {
    print_header "GENERATING SUMMARY"

    local summary_file="$RESULTS_DIR/summary_${TIMESTAMP}.md"

    cat > "$summary_file" << EOF
# WASM vs Native Performance Benchmark Summary
Generated: $(date)

## Configuration
- Warmup Runs: $WARMUP_RUNS
- Benchmark Runs: $BENCH_RUNS (used for both timing and memory measurements)
- Scenarios Tested: ${#SCENARIOS[@]}
- Runtime Configurations: ${#RUNTIMES[@]}

## Test Scenarios
EOF

    for scenario in "${SCENARIOS[@]}"; do
        echo "- $scenario" >> "$summary_file"
    done

    cat >> "$summary_file" << EOF

## Runtime Configurations
EOF

    for runtime_config in "${RUNTIMES[@]}"; do
        IFS=':' read -r runtime_name _ <<< "$runtime_config"
        echo "- $runtime_name" >> "$summary_file"
    done

    cat >> "$summary_file" << EOF

## Result Files
All detailed results are stored in: \`$RESULTS_DIR/\`

### Main Result Files (Use These for Analysis)

#### Timing Results
- \`timing_all_scenarios_${TIMESTAMP}.md\` - **All timing data including NET calculations**
- \`timing_all_scenarios_${TIMESTAMP}.json\` - Combined JSON for all scenarios

#### Memory Results
- \`memory_all_scenarios_${TIMESTAMP}.txt\` - **All memory data including NET calculations with statistics**

### Individual JSON Files (For Detailed Analysis)

#### Main Execution Times
EOF

    for scenario in "${SCENARIOS[@]}"; do
        echo "- \`timing_${scenario}_${TIMESTAMP}.json\` - JSON data for $scenario" >> "$summary_file"
    done

    cat >> "$summary_file" << EOF

#### Overhead Execution Times
EOF

    for scenario in "${SCENARIOS[@]}"; do
        echo "- \`timing_overheads_${scenario}_${TIMESTAMP}.json\` - Overhead JSON for $scenario" >> "$summary_file"
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

