#!/bin/bash

# Memory Benchmark Script for Single Binary with Arguments
# Measures Max RSS across different runtime configurations

set -eEuo pipefail
trap 'echo -e "\n${RED}❌ ERROR: Command failed at line $LINENO: $BASH_COMMAND${NC}\n"' ERR

# Configuration
WARMUP_RUNS=15
BENCH_RUNS=20
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="benchmark_results/$TIMESTAMP"
TEST_COMPILED_PATH="./bin/built_test.test"

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

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configurations
# Format: "ConfigName:WasmFile:Runtime:IsInterpreter:RegisterHostFn:FunctionInput"
declare -a DEFAULT_TEST_CONFIGS=(
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

: "${TEST_CONFIGS_ENV:="${DEFAULT_TEST_CONFIGS[*]}"}"
IFS=' ' read -ra TEST_CONFIGS <<< "$TEST_CONFIGS_ENV"

declare -A MEMORY_DATA
declare -A MEMORY_DATA_STDDEV

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Function to print subsection
print_subsection() {
    echo -e "\n${YELLOW}--- $1 ---${NC}"
}

# Function to calculate mean and standard deviation
calculate_stats() {
    local values=("$@")
    local sum=0
    local count=${#values[@]}

    # Calculate mean
    for val in "${values[@]}"; do
        sum=$(echo "$sum + $val" | bc -l)
    done
    local mean=$(echo "scale=2; $sum / $count" | bc -l)

    # Calculate standard deviation
    local sum_sq_diff=0
    for val in "${values[@]}"; do
        local diff=$(echo "$val - $mean" | bc -l)
        local sq_diff=$(echo "$diff * $diff" | bc -l)
        sum_sq_diff=$(echo "$sum_sq_diff + $sq_diff" | bc -l)
    done
    local variance=$(echo "scale=2; $sum_sq_diff / $count" | bc -l)
    local stddev=$(echo "scale=2; sqrt($variance)" | bc -l)

    echo "$mean $stddev"
}

# Function to run native binary benchmark
run_native_benchmark() {
    local config_name=$1
    local native_binary=$2
    local function_input=$3
    local output_file=$4

    print_subsection "$config_name (running $BENCH_RUNS times)"

    # Check if native binary exists
    if [ ! -f "$native_binary" ]; then
        echo -e "${YELLOW}⚠ Skipping $config_name - binary not found: $native_binary${NC}"
        echo "## $config_name" >> "$output_file"
        echo "SKIPPED: Binary not found at $native_binary" >> "$output_file"
        echo "" >> "$output_file"
        return
    fi

    local max_rss_values=()

    # Run the native binary multiple times
    for ((run=1; run<=BENCH_RUNS; run++)); do
        echo -ne "  Run $run/$BENCH_RUNS...\r"

        # Run with /usr/bin/time and capture MaxRSS
        local time_output=$( { /usr/bin/time -f "%M" \
            "$native_binary" \
            "$function_input" \
            > /dev/null; } 2>&1 )

        # Extract only the numeric value (MaxRSS in KB)
        time_output=$(echo "$time_output" | grep -oE '[0-9]+' | tail -n 1)

        max_rss_values+=("$time_output")
    done

    echo -e "  Completed $BENCH_RUNS runs          "

    # Calculate statistics
    local stats=$(calculate_stats "${max_rss_values[@]}")
    read -r mean_rss stddev_rss <<< "$stats"

    # Display results
    echo "$config_name"
    echo "  Configuration:"
    echo "    Native Binary: $native_binary"
    echo "    Input: $function_input"
    echo "  Mean MaxRSS: $mean_rss KB"
    echo "  Std Dev: $stddev_rss KB"
    echo "  Min: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | head -n1) KB"
    echo "  Max: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | tail -n1) KB"
    echo ""

    # Append to results file
    echo "## $config_name" >> "$output_file"
    echo "Mean MaxRSS: $mean_rss KB (over $BENCH_RUNS runs)" >> "$output_file"
    echo "Std Dev: $stddev_rss KB" >> "$output_file"
    echo "Min: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | head -n1) KB" >> "$output_file"
    echo "Max: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | tail -n1) KB" >> "$output_file"
    echo "Raw values: ${max_rss_values[*]}" >> "$output_file"
    echo "" >> "$output_file"

    # Store memory data
    MEMORY_DATA["${config_name}"]="$mean_rss"
    MEMORY_DATA_STDDEV["${config_name}"]="$stddev_rss"
}

# Function to run memory benchmark for a single WASM configuration
run_wasm_benchmark() {
    local config_name=$1
    local wasm_file=$2
    local runtime=$3
    local is_interpreter=$4
    local register_hostfn=$5
    local function_input=$6
    local output_file=$7

    print_subsection "$config_name (running $BENCH_RUNS times)"

    local max_rss_values=()

    # Run the binary multiple times
    for ((run=1; run<=BENCH_RUNS; run++)); do
        echo -ne "  Run $run/$BENCH_RUNS...\r"

        # Run with /usr/bin/time and capture MaxRSS
        # Redirect stdout to /dev/null to avoid capturing test output
        # Only stderr from time command is captured
        local time_output=$( { /usr/bin/time -f "%M" \
            "$TEST_COMPILED_PATH" \
            -test.run ^TestProva$ \
            "$wasm_file" \
            "$runtime" \
            "$is_interpreter" \
            "$register_hostfn" \
            "$function_input" \
            "true" \
            > /dev/null; } 2>&1 )

        # Extract only the numeric value (MaxRSS in KB)
        time_output=$(echo "$time_output" | grep -oE '[0-9]+' | tail -n 1)

        max_rss_values+=("$time_output")
    done

    echo -e "  Completed $BENCH_RUNS runs          "

    # Calculate statistics
    local stats=$(calculate_stats "${max_rss_values[@]}")
    read -r mean_rss stddev_rss <<< "$stats"

    # Display results
    echo "$config_name"
    echo "  Configuration:"
    echo "    WASM File: $wasm_file"
    echo "    Runtime: $runtime"
    echo "    Interpreter: $is_interpreter"
    echo "    Host Functions: $register_hostfn"
    echo "    Input: $function_input"
    echo "  Mean MaxRSS: $mean_rss KB"
    echo "  Std Dev: $stddev_rss KB"
    echo "  Min: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | head -n1) KB"
    echo "  Max: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | tail -n1) KB"
    echo ""

    # Append to results file
    echo "## $config_name" >> "$output_file"
    echo "Mean MaxRSS: $mean_rss KB (over $BENCH_RUNS runs)" >> "$output_file"
    echo "Std Dev: $stddev_rss KB" >> "$output_file"
    echo "Min: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | head -n1) KB" >> "$output_file"
    echo "Max: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | tail -n1) KB" >> "$output_file"
    echo "Raw values: ${max_rss_values[*]}" >> "$output_file"
    echo "" >> "$output_file"

    # Store memory data
    MEMORY_DATA["${config_name}"]="$mean_rss"
    MEMORY_DATA_STDDEV["${config_name}"]="$stddev_rss"
}

# Function to create comparison table
create_comparison_table() {
    local output_file="$RESULTS_DIR/comparison_table_${TIMESTAMP}.txt"

    cat > "$output_file" << EOF
# Memory Consumption Comparison Table
# Generated: $(date)
# All values in KB

Configuration                              | Mean MaxRSS | Std Dev |
---------------------------------------------------------|---------|
EOF

    for config in "${TEST_CONFIGS[@]}"; do
        IFS=':' read -r config_name _ _ _ _ _ <<< "$config"
        local mean_rss="${MEMORY_DATA[$config_name]}"
        local stddev_rss="${MEMORY_DATA_STDDEV[$config_name]}"

        # Skip if no data (e.g., binary not found)
        if [ -n "$mean_rss" ]; then
            printf "%-42s | %11s | %7s |\n" "$config_name" "$mean_rss" "$stddev_rss" >> "$output_file"
        fi
    done

    echo -e "${GREEN}✓ Comparison table saved to: $output_file${NC}"
}

# Parse command line arguments
parse_flags() {
    while [[ $# -gt 0 ]]; do
        case $1 in
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
            -cb|--compiled-binary)
                shift
                if [[ $# -gt 0 ]]; then
                    TEST_COMPILED_PATH=$1
                else
                    echo "must specify a binary path"
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
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  -w,  --warmup               Specify how many warmup runs perform (default: 15)"
                echo "  -r,  --runs                 Specify how many benchmark runs perform (default: 20)"
                echo "  -cb, --compiled-binary      Path to the test binary (default: ./bin/built_test.test)"
                echo "  -od, --output-dir           Directory where to place benchmark results (default: 'benchmark_results/{Timestamp}')"
                echo "  -h,  --help                 Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0 --runs 10                          # Run 10 times per configuration"
                echo "  $0 --binary ./my_test.test --runs 20  # Use custom binary and 20 runs"
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                echo "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Main execution
main() {
    parse_flags "$@"

    if [[ -z "${SKIP_MEM_BENCH_INTERACTIVE:-}" ]]; then
      print_header "WASM Memory Benchmark Suite"

      echo "Configuration:"
      echo "  WASM Test Binary: $TEST_COMPILED_PATH"
      echo "  Warmup runs: $WARMUP_RUNS"
      echo "  Benchmark runs: $BENCH_RUNS"
      echo "  Results directory: $RESULTS_DIR"
      echo "  Timestamp: $TIMESTAMP"
      echo ""
      echo "Test configurations (${#TEST_CONFIGS[@]}):"
      for config in "${TEST_CONFIGS[@]}"; do
          IFS=':' read -r config_name _ _ _ _ _ <<< "$config"
          echo "  - $config_name"
      done
      echo ""

      # Check if WASM test binary exists
      if [ ! -f "$TEST_COMPILED_PATH" ]; then
          echo -e "${YELLOW}WARNING: WASM test binary not found at $TEST_COMPILED_PATH${NC}"
          echo "Native benchmarks will still run if binaries are available"
      fi

      # Check if GNU time is available
      if ! /usr/bin/time --version &> /dev/null 2>&1; then
          echo -e "${YELLOW}WARNING: GNU time not found at /usr/bin/time${NC}"
          echo "Memory benchmarks may not work correctly"
      fi

      # Check if bc is available
      if ! command -v bc &> /dev/null; then
          echo -e "${RED}ERROR: bc (calculator) is not installed${NC}"
          echo "Install with: apt-get install bc (Ubuntu/Debian) or brew install bc (macOS)"
          exit 1
      fi

      read -p "Press Enter to start benchmarking or Ctrl+C to cancel..."
    fi

    # Create results directory
    mkdir -p "$RESULTS_DIR"

    print_header "RUNNING MEMORY BENCHMARKS"

    # Run benchmarks for each configuration
    local old_algorithm_name=""
    local output_file="$RESULTS_DIR/memory_results_${TIMESTAMP}.txt"

    for config in "${TEST_CONFIGS[@]}"; do
        IFS=':' read -r config_name second_field third_field fourth_field fifth_field sixth_field <<< "$config"
        IFS="_" read -r algorithm_name rest <<< "$config_name"

        if [[ "$old_algorithm_name" != "$algorithm_name" ]]; then
          echo "################################################################################" >> "$output_file"
          echo "# SCENARIO: $algorithm_name" >> "$output_file"
          echo "################################################################################" >> "$output_file"
          echo "" >> "$output_file"
          old_algorithm_name=$algorithm_name
        fi

        # Check if this is a native binary configuration
        if [[ "$second_field" == "NATIVE" ]]; then
            # Format: ConfigName:NATIVE:NativeBinaryPath:Input
            run_native_benchmark "$config_name" "$third_field" "$fourth_field" "$output_file"
        else
            # Format: ConfigName:WasmFile:Runtime:IsInterpreter:RegisterHostFn:FunctionInput
            run_wasm_benchmark "$config_name" "$second_field" "$third_field" "$fourth_field" "$fifth_field" "$sixth_field" "$output_file"
        fi
    done

    # Write results to files
    create_comparison_table

    print_header "BENCHMARK COMPLETE"
    echo -e "${GREEN}All benchmarks completed successfully!${NC}"
    echo "Results saved in: $RESULTS_DIR/"
    echo ""
    echo "Files created:"
    echo "  📊 memory_results_${TIMESTAMP}.txt"
    echo "  📋 comparison_table_${TIMESTAMP}.txt"
    echo ""
    echo "Memory measurements:"
    echo "  ✓ Each value averaged over $BENCH_RUNS runs"
    echo "  ✓ Includes mean, standard deviation, min, and max"
}

# Run main function
main "$@"