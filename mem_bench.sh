#!/bin/bash

# WASM vs Native Benchmark Script for Thesis
# This script compares execution time and memory consumption across different configurations

set -eEuo pipefail
trap 'echo -e "\n${RED}❌ ERROR: Command failed at line $LINENO: $BASH_COMMAND${NC}\n"' ERR

# Configuration
WARMUP_RUNS=1
BENCH_RUNS=5
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="benchmark_results/$TIMESTAMP"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test scenarios (workloads)
DEFAULT_SCENARIOS=(
    "PrimeNumbers"
    "Fibonacci"
    "Lightweight"
    "TailFibonacci"
    "HostFns"
)

# Runtime configurations
# Format: "RuntimeName:BinaryPrefix"
DEFAULT_RUNTIMES=(
    "Native:native"
    "Wasmedge_Interpreter_NoOpts:wasmedge_interpreter_noopts"
    "Wasmedge_Interpreter_WithOpts:wasmedge_interpreter_wopts"
    "Wasmedge_AOT_NoOpts:wasmedge_aot_noopts"
    "Wasmedge_AOT_WithOpts:wasmedge_aot_wopts"
    "Wasmtime_JIT_NoOpts:wasmtime_jit_noopts"
    "Wasmtime_JIT_WithOpts:wasmtime_jit_wopts"
    "Wasmtime_AOT_NoOpts:wasmtime_aot_noopts"
    "Wasmtime_AOT_WithOpts:wasmtime_aot_wopts"
    "Wazero_AOT_NoOpts:wazero_aot_noopts"
    "Wazero_AOT_WithOpts:wazero_aot_wopts"
    "Wazero_Interpreter_NoOpts:wazero_interpreter_noopts"
    "Wazero_Interpreter_WithOpts:wazero_interpreter_wopts"
)

: "${SCENARIOS_ENV:="${DEFAULT_SCENARIOS[*]}"}"
: "${RUNTIMES_ENV:="${DEFAULT_RUNTIMES[*]}"}"

IFS=' ' read -ra SCENARIOS <<< "$SCENARIOS_ENV"
IFS=' ' read -ra RUNTIMES <<< "$RUNTIMES_ENV"

declare -A MEMORY_DATA
declare -A MEMORY_DATA_STDDEV
declare -A MEMORY_OVERHEAD_DATA
declare -A MEMORY_OVERHEAD_DATA_STDDEV

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

# Function to check if binary exists
check_binary() {
    if [ ! -f "$1" ]; then
        return 1
    fi
    return 0
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

# Function to run memory benchmarks with GNU time (multiple runs with averaging)
run_memory_benchmarks() {
    local scenario=$1
    print_header "MEMORY BENCHMARKS: $scenario (averaging over $BENCH_RUNS runs)"

    local output_file="$RESULTS_DIR/memory_${scenario}_${TIMESTAMP}.txt"

    echo "# Memory Benchmark Results: $scenario" > "$output_file"
    echo "# Generated: $(date)" >> "$output_file"
    echo "# Runs per configuration: $BENCH_RUNS" >> "$output_file"
    echo "" >> "$output_file"

    for runtime_config in "${RUNTIMES[@]}"; do
        IFS=':' read -r runtime_name binary_prefix <<< "$runtime_config"
        local binary_path="./bin/${binary_prefix}_${scenario}"

        if ! check_binary "$binary_path"; then
            echo -e "${YELLOW}Skipping $runtime_name for $scenario (binary not found)${NC}"
            continue
        fi

        print_subsection "$runtime_name (running $BENCH_RUNS times)"

        local max_rss_values=()

        # Run the binary multiple times
        for ((run=1; run<=BENCH_RUNS; run++)); do
            echo -ne "  Run $run/$BENCH_RUNS...\r"

            # Run with /usr/bin/time and capture MaxRSS
            local time_output=$(/usr/bin/time -f "%M" "$binary_path" 2>&1 | tail -n 1)
            max_rss_values+=("$time_output")

        done

        echo -e "  Completed $BENCH_RUNS runs          "

        # Calculate statistics
        local stats=$(calculate_stats "${max_rss_values[@]}")
        read -r mean_rss stddev_rss <<< "$stats"

        # Display results
        echo "$runtime_name"
        echo "  Mean MaxRSS: $mean_rss KB"
        echo "  Std Dev: $stddev_rss KB"
        echo "  Min: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | head -n1) KB"
        echo "  Max: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | tail -n1) KB"
        echo ""

        # Append to results file
        echo "## $runtime_name" >> "$output_file"
        echo "Mean MaxRSS: $mean_rss KB (over $BENCH_RUNS runs)" >> "$output_file"
        echo "Std Dev: $stddev_rss KB" >> "$output_file"
        echo "Min: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | head -n1) KB" >> "$output_file"
        echo "Max: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | tail -n1) KB" >> "$output_file"
        echo "Raw values: ${max_rss_values[*]}" >> "$output_file"
        echo "" >> "$output_file"

        # Store memory data (use mean)
        MEMORY_DATA["${runtime_name}:${scenario}"]="$mean_rss"
        MEMORY_DATA_STDDEV["${runtime_name}:${scenario}"]="$stddev_rss"
    done

    echo -e "${GREEN}✓ Memory results saved (averaged over $BENCH_RUNS runs)${NC}"
}

# Function to run memory benchmarks for OVERHEAD binaries (multiple runs with averaging)
run_overhead_memory_benchmarks() {
    local scenario=$1
    print_header "OVERHEAD MEMORY BENCHMARKS: $scenario (averaging over $BENCH_RUNS runs)"

    local output_file="$RESULTS_DIR/memory_overheads_${scenario}_${TIMESTAMP}.txt"

    echo "# Overhead Memory Benchmark Results: $scenario" > "$output_file"
    echo "# Generated: $(date)" >> "$output_file"
    echo "# Runs per configuration: $BENCH_RUNS" >> "$output_file"
    echo "" >> "$output_file"

    local found_any=false

    for runtime_config in "${RUNTIMES[@]}"; do
        IFS=':' read -r runtime_name binary_prefix <<< "$runtime_config"

        # Skip Native runtime
        if [[ "$runtime_name" == "Native" ]]; then
            continue
        fi

        local binary_path="./bin/overheads_${binary_prefix}_${scenario}"

        if ! check_binary "$binary_path"; then
            echo -e "${YELLOW}Skipping overhead for $runtime_name for $scenario (binary not found)${NC}"
            continue
        fi

        found_any=true
        print_subsection "${runtime_name} OVERHEAD (running $BENCH_RUNS times)"

        local max_rss_values=()

        # Run the binary multiple times
        for ((run=1; run<=BENCH_RUNS; run++)); do
            echo -ne "  Run $run/$BENCH_RUNS...\r"

            local time_output=$(/usr/bin/time -f "%M" "$binary_path" 2>&1 | tail -n 1)
            max_rss_values+=("$time_output")
        done

        echo -e "  Completed $BENCH_RUNS runs          "

        # Calculate statistics
        local stats=$(calculate_stats "${max_rss_values[@]}")
        read -r mean_rss stddev_rss <<< "$stats"

        # Display results
        echo "${runtime_name} OVERHEAD"
        echo "  Mean MaxRSS: $mean_rss KB"
        echo "  Std Dev: $stddev_rss KB"
        echo "  Min: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | head -n1) KB"
        echo "  Max: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | tail -n1) KB"
        echo ""

        echo "## ${runtime_name} OVERHEAD" >> "$output_file"
        echo "Mean MaxRSS: $mean_rss KB (over $BENCH_RUNS runs)" >> "$output_file"
        echo "Std Dev: $stddev_rss KB" >> "$output_file"
        echo "Min: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | head -n1) KB" >> "$output_file"
        echo "Max: $(printf '%s\n' "${max_rss_values[@]}" | sort -n | tail -n1) KB" >> "$output_file"
        echo "Raw values: ${max_rss_values[*]}" >> "$output_file"
        echo "" >> "$output_file"

        # Store overhead memory data
        MEMORY_OVERHEAD_DATA["${runtime_name}:${scenario}"]="$mean_rss"
        MEMORY_OVERHEAD_DATA_STDDEV["${runtime_name}:${scenario}"]="$stddev_rss"
    done

    if [ "$found_any" = true ]; then
        echo -e "${GREEN}✓ Overhead memory results saved (averaged over $BENCH_RUNS runs)${NC}"
    else
        echo -e "${YELLOW}No overhead binaries found for memory benchmarking${NC}"
    fi
}

# Function to combine memory results with NET calculations
combine_memory_results() {
    print_header "COMBINING MEMORY RESULTS WITH NET CALCULATIONS"

    local combined_file="$RESULTS_DIR/memory_all_scenarios_${TIMESTAMP}.txt"

    cat > "$combined_file" << EOF
# Combined Memory Benchmark Results - All Scenarios
# Generated: $(date)
# Runs per configuration: $BENCH_RUNS
# Format: Runtime | Mean Max RSS (KB) ± Std Dev | Min | Max

================================================================================

EOF

    for scenario in "${SCENARIOS[@]}"; do
        local scenario_file="$RESULTS_DIR/memory_${scenario}_${TIMESTAMP}.txt"

        if [ -f "$scenario_file" ]; then
            echo "################################################################################" >> "$combined_file"
            echo "# SCENARIO: $scenario" >> "$combined_file"
            echo "################################################################################" >> "$combined_file"
            echo "" >> "$combined_file"

            tail -n +5 "$scenario_file" >> "$combined_file"

            echo "" >> "$combined_file"
            echo "" >> "$combined_file"

            # Delete individual memory file
            rm -f "$scenario_file"
        fi
    done

    # Add NET memory calculations section
    cat >> "$combined_file" << EOF

################################################################################
# NET MEMORY CONSUMPTION (Total - Overhead)
################################################################################
# This section shows the pure memory usage after subtracting WASM runtime overhead.
# Formula: NET Memory = Total Memory - Overhead Memory
# Note: Standard deviations are combined using sqrt(σ₁² + σ₂²)

EOF

    for scenario in "${SCENARIOS[@]}"; do
        echo "################################################################################" >> "$combined_file"
        echo "# SCENARIO: $scenario - NET MEMORY" >> "$combined_file"
        echo "################################################################################" >> "$combined_file"
        echo "" >> "$combined_file"

        for runtime_config in "${RUNTIMES[@]}"; do
            IFS=':' read -r runtime_name _ <<< "$runtime_config"

            if [[ "$runtime_name" == "Native" ]]; then
                if [[ "$scenario" != "HostFns" ]]; then
                  local total_mem="${MEMORY_DATA[${runtime_name}:${scenario}]}"
                  local total_stddev="${MEMORY_DATA_STDDEV[${runtime_name}:${scenario}]}"
                  if [ -n "$total_mem" ] && [ "$total_mem" != "0" ]; then
                      echo "## $runtime_name" >> "$combined_file"
                      echo "Total Memory: $total_mem KB (±${total_stddev} KB)" >> "$combined_file"
                      echo "Overhead Memory: N/A" >> "$combined_file"
                      echo "NET Memory: $total_mem KB (±${total_stddev} KB)" >> "$combined_file"
                      echo "" >> "$combined_file"
                  fi
                fi
            else
                local total_mem="${MEMORY_DATA[${runtime_name}:${scenario}]}"
                local total_stddev="${MEMORY_DATA_STDDEV[${runtime_name}:${scenario}]}"
                local overhead_mem="${MEMORY_OVERHEAD_DATA[${runtime_name}:${scenario}]}"
                local overhead_stddev="${MEMORY_OVERHEAD_DATA_STDDEV[${runtime_name}:${scenario}]}"

                if [ -n "$total_mem" ] && [ "$total_mem" != "0" ]; then
                    echo "## $runtime_name" >> "$combined_file"
                    echo "Total Memory: $total_mem KB (±${total_stddev} KB)" >> "$combined_file"

                    if [ -n "$overhead_mem" ] && [ "$overhead_mem" != "0" ]; then
                        local net_mem=$(echo "$total_mem - $overhead_mem" | bc -l)
                        # Combine standard deviations: sqrt(σ₁² + σ₂²)
                        local net_stddev=$(echo "scale=2; sqrt(($total_stddev * $total_stddev) + ($overhead_stddev * $overhead_stddev))" | bc -l)
                        echo "Overhead Memory: $overhead_mem KB (±${overhead_stddev} KB)" >> "$combined_file"
                        printf "NET Memory: %.2f KB (±%.2f KB)\n" "$net_mem" "$net_stddev" >> "$combined_file"
                    else
                        echo "Overhead Memory: No overhead data available" >> "$combined_file"
                        echo "NET Memory: N/A" >> "$combined_file"
                    fi
                    echo "" >> "$combined_file"
                fi
            fi
        done

        echo "" >> "$combined_file"
    done

    # Delete individual overhead memory files
    for scenario in "${SCENARIOS[@]}"; do
        rm -f "$RESULTS_DIR/memory_overheads_${scenario}_${TIMESTAMP}.txt"
    done

    echo -e "${GREEN}✓ Combined memory results with NET calculations saved to: $combined_file${NC}"
}

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
              echo "  -od, --output-dir           Directory where to place benchmark results (default: 'benchmark_results/{Timestamp}'"
              echo "  -h, --help                  Show this help message"
              echo ""
              echo "Examples:"
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
}

# Main execution
main() {
    parse_flags "$@"

    if [[ -z "${SKIP_MEM_BENCH_INTERACTIVE:-}" ]]; then
      print_header "WASM vs Native Benchmark Suite"

      echo "Configuration:"
      echo "  Warmup runs: $WARMUP_RUNS"
      echo "  Benchmark runs: $BENCH_RUNS"
      echo "  Results directory: $RESULTS_DIR"
      echo "  Timestamp: $TIMESTAMP"
      echo ""
      echo "Scenarios to test:"
      for scenario in "${SCENARIOS[@]}"; do
        echo "  - $scenario"
      done
      echo ""
      echo "Runtime configurations (${#RUNTIMES[@]}):"
      for runtime in "${RUNTIMES[@]}"; do
        echo "  - $runtime"
      done
      echo ""
      echo "Memory measurements will be averaged over $BENCH_RUNS runs per configuration"
      echo ""

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
    fi

    # Create results directory
    mkdir -p "$RESULTS_DIR"

    # Run benchmarks for each scenario
    for scenario in "${SCENARIOS[@]}"; do
        # Main binaries
        run_memory_benchmarks "$scenario"

        # Overhead binaries
        run_overhead_memory_benchmarks "$scenario"
    done

    # Combine all results with NET calculations
    combine_memory_results

    print_header "MEMORY BENCHMARK COMPLETE"
    echo -e "${GREEN}All benchmarks completed successfully!${NC}"
    echo "Results saved in: $RESULTS_DIR/"
    echo ""
    echo "Main result files:"
    echo "  💾 memory_all_scenarios_${TIMESTAMP}.txt (includes NET calculations + statistics)"
    echo ""
    echo "Memory measurements:"
    echo "  ✓ Each value averaged over $BENCH_RUNS runs"
    echo "  ✓ Includes mean, standard deviation, min, and max"
    echo "  ✓ NET calculations with combined standard deviations"
    echo ""
    echo "NET calculations show pure execution cost after removing WASM runtime overhead!"
}

# Run main function
main "$@"