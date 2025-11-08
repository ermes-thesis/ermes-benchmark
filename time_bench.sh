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

# Arrays to store timing and memory data for NET calculations
declare -A TIMING_DATA
declare -A TIMING_OVERHEAD_DATA


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

# Function to extract mean time from JSON for a specific index (in seconds)
extract_mean_time_from_json() {
    local json_file=$1
    local index=${2:-0}
    if [ -f "$json_file" ]; then
        # Extract mean time using jq or python
        if command -v jq &> /dev/null; then
            jq -r ".results[$index].mean" "$json_file" 2>/dev/null || echo "0"
        else
            # Fallback: use grep and awk
            grep -o '"mean":[^,]*' "$json_file" | sed -n "$((index+1))p" | awk -F':' '{print $2}' | tr -d ' ' || echo "0"
        fi
    else
        echo "0"
    fi
}

# Function to run timing benchmarks with Hyperfine
run_timing_benchmarks() {
    local scenario=$1
    print_header "TIMING BENCHMARKS: $scenario"

    local binaries=()
    local runtime_order=()

    # First, collect the Native binary (baseline)
    for runtime_config in "${RUNTIMES[@]}"; do
        IFS=':' read -r runtime_name binary_prefix <<< "$runtime_config"
        [[ "$runtime_name" != "Native" ]] && continue
        local binary_path="./bin/${binary_prefix}_${scenario}"
        if check_binary "$binary_path"; then
            binaries+=("$binary_path")
            runtime_order+=("$runtime_name")
        else
            echo -e "${YELLOW}Skipping $runtime_name for $scenario (binary not found)${NC}"
        fi
    done

    # Then collect all non-Native runtimes
    for runtime_config in "${RUNTIMES[@]}"; do
        IFS=':' read -r runtime_name binary_prefix <<< "$runtime_config"
        [[ "$runtime_name" == "Native" ]] && continue
        local binary_path="./bin/${binary_prefix}_${scenario}"
        if check_binary "$binary_path"; then
            binaries+=("$binary_path")
            runtime_order+=("$runtime_name")
        else
            echo -e "${YELLOW}Skipping $runtime_name for $scenario (binary not found)${NC}"
        fi
    done

    if [ ${#binaries[@]} -eq 0 ]; then
        echo -e "${RED}No binaries found for scenario: $scenario${NC}"
        return 1
    fi

    local output_json="$RESULTS_DIR/timing_${scenario}_${TIMESTAMP}.json"
    local output_md="$RESULTS_DIR/timing_${scenario}_${TIMESTAMP}.md"

    echo -e "${GREEN}Running Hyperfine for $scenario with ${#binaries[@]} configurations...${NC}"

    hyperfine \
        --warmup "$WARMUP_RUNS" \
        --runs "$BENCH_RUNS" \
        --export-json "$output_json" \
        --export-markdown "$output_md" \
        --style full \
        "${binaries[@]}"

    echo -e "${GREEN}✓ Results saved to JSON${NC}"

    # Extract means in the same order
    local means=()
    if command -v jq &> /dev/null; then
        mapfile -t means < <(jq -r '.results[].mean' "$output_json")
    else
        mapfile -t means < <(grep -o '"mean":[^,]*' "$output_json" | awk -F':' '{print $2}')
    fi

    # Store them in associative array with correct mapping
    for ((i = 0; i < ${#runtime_order[@]}; i++)); do
        local rt="${runtime_order[$i]}"
        local mean="${means[$i]:-0}"
        TIMING_DATA["${rt}:${scenario}"]="$mean"
    done
}


# Function to run timing benchmarks for OVERHEAD binaries
run_overhead_timing_benchmarks() {
    local scenario=$1
    print_header "OVERHEAD TIMING BENCHMARKS: $scenario"

    local binaries=()
    local runtime_order=()

    # Only non-Native runtimes (Native has no overhead)
    for runtime_config in "${RUNTIMES[@]}"; do
        IFS=':' read -r runtime_name binary_prefix <<< "$runtime_config"
        [[ "$runtime_name" == "Native" ]] && continue
        local binary_path="./bin/overheads_${binary_prefix}_${scenario}"
        if check_binary "$binary_path"; then
            binaries+=("$binary_path")
            runtime_order+=("$runtime_name")
        else
            echo -e "${YELLOW}Skipping overhead for $runtime_name for $scenario (binary not found)${NC}"
        fi
    done

    if [ ${#binaries[@]} -eq 0 ]; then
        echo -e "${YELLOW}No overhead binaries found for $scenario${NC}"
        return 0
    fi

    local output_json="$RESULTS_DIR/timing_overheads_${scenario}_${TIMESTAMP}.json"
    local output_md="$RESULTS_DIR/timing_overheads_${scenario}_${TIMESTAMP}.md"

    echo -e "${GREEN}Running Hyperfine for overhead measurements in $scenario...${NC}"

    hyperfine \
        --warmup "$WARMUP_RUNS" \
        --runs "$BENCH_RUNS" \
        --export-json "$output_json" \
        --export-markdown "$output_md" \
        --style full \
        "${binaries[@]}"

    echo -e "${GREEN}✓ Overhead results saved to JSON${NC}"

    # Extract means in order
    local means=()
    if command -v jq &> /dev/null; then
        mapfile -t means < <(jq -r '.results[].mean' "$output_json")
    else
        mapfile -t means < <(grep -o '"mean":[^,]*' "$output_json" | awk -F':' '{print $2}')
    fi

    for ((i = 0; i < ${#runtime_order[@]}; i++)); do
        local rt="${runtime_order[$i]}"
        local mean="${means[$i]:-0}"
        TIMING_OVERHEAD_DATA["${rt}:${scenario}"]="$mean"
    done
}

# Function to combine timing results with NET calculations
combine_timing_results() {
    print_header "COMBINING TIMING RESULTS WITH NET CALCULATIONS"

    local combined_json="$RESULTS_DIR/timing_all_scenarios_${TIMESTAMP}.json"
    local combined_md="$RESULTS_DIR/timing_all_scenarios_${TIMESTAMP}.md"

    # Create combined markdown file
    cat > "$combined_md" << EOF
# Combined Timing Results - All Scenarios
Generated: $(date)

Warmup Runs: $WARMUP_RUNS | Benchmark Runs: $BENCH_RUNS

---

EOF

    # Start JSON
    echo "{" > "$combined_json"
    echo "  \"metadata\": {" >> "$combined_json"
    echo "    \"generated\": \"$(date -Iseconds)\"," >> "$combined_json"
    echo "    \"warmup_runs\": $WARMUP_RUNS," >> "$combined_json"
    echo "    \"benchmark_runs\": $BENCH_RUNS" >> "$combined_json"
    echo "  }," >> "$combined_json"
    echo "  \"scenarios\": {" >> "$combined_json"

    local first_scenario=true

    for scenario in "${SCENARIOS[@]}"; do
        local scenario_json="$RESULTS_DIR/timing_${scenario}_${TIMESTAMP}.json"
        local scenario_md="$RESULTS_DIR/timing_${scenario}_${TIMESTAMP}.md"

        if [ -f "$scenario_json" ]; then
            # Add to combined JSON
            if [ "$first_scenario" = true ]; then
                first_scenario=false
            else
                echo "," >> "$combined_json"
            fi

            echo "    \"$scenario\": " >> "$combined_json"
            cat "$scenario_json" >> "$combined_json"

            # Add to combined markdown
            echo "## Scenario: $scenario" >> "$combined_md"
            echo "" >> "$combined_md"

            if [ -f "$scenario_md" ]; then
                tail -n +1 "$scenario_md" >> "$combined_md"
            fi

            echo "" >> "$combined_md"
            echo "---" >> "$combined_md"
            echo "" >> "$combined_md"

            # Delete individual MD file
            rm -f "$scenario_md"
        fi
    done

    # Close JSON scenarios section
    echo "" >> "$combined_json"
    echo "  }" >> "$combined_json"
    echo "}" >> "$combined_json"

    # Add NET calculations section to markdown
    cat >> "$combined_md" << EOF

================================================================================
# NET EXECUTION TIME (Total - Overhead)
================================================================================

This section shows the pure execution time after subtracting WASM runtime overhead.
Formula: NET Time = Total Execution Time - Overhead Time

EOF

    for scenario in "${SCENARIOS[@]}"; do
        echo "## Scenario: $scenario" >> "$combined_md"
        echo "" >> "$combined_md"
        echo "| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |" >> "$combined_md"
        echo "|---------|----------------|-------------------|--------------|" >> "$combined_md"

        for runtime_config in "${RUNTIMES[@]}"; do
            IFS=':' read -r runtime_name _ <<< "$runtime_config"

            if [[ "$runtime_name" == "Native" ]]; then
                if [[ "$scenario" != "HostFns" ]]; then
                  local total_time="${TIMING_DATA[${runtime_name}:${scenario}]}"
                  if [ -n "$total_time" ] && [ "$total_time" != "0" ]; then
                      printf "| %-55s | %14s | %17s | %12s |\n" "$runtime_name" "$total_time" "N/A" "N/A" >> "$combined_md"
                  fi
                fi
            else
                local total_time="${TIMING_DATA[${runtime_name}:${scenario}]}"
                local overhead_time="${TIMING_OVERHEAD_DATA[${runtime_name}:${scenario}]}"

                if [ -n "$total_time" ] && [ "$total_time" != "0" ]; then
                    if [ -n "$overhead_time" ] && [ "$overhead_time" != "0" ]; then
                        local net_time=$(echo "$total_time - $overhead_time" | bc -l)
                        printf "| %-55s | %14.6f | %17.6f | %12.6f |\n" "$runtime_name" "$total_time" "$overhead_time" "$net_time" >> "$combined_md"
                    else
                        printf "| %-55s | %14.6f | %17s | %12s |\n" "$runtime_name" "$total_time" "No overhead data" "N/A" >> "$combined_md"
                    fi
                fi
            fi
        done

        echo "" >> "$combined_md"
        echo "---" >> "$combined_md"
        echo "" >> "$combined_md"
    done

    # Delete individual overhead MD files
    for scenario in "${SCENARIOS[@]}"; do
        rm -f "$RESULTS_DIR/timing_overheads_${scenario}_${TIMESTAMP}.md"
    done

    echo -e "${GREEN}✓ Combined timing results with NET calculations saved to:${NC}"
    echo "  - JSON: $combined_json"
    echo "  - Markdown: $combined_md"
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

    if [[ -z "${SKIP_TIME_BENCH_INTERACTIVE:-}" ]]; then
      print_header "WASM vs Native Benchmark Suite"

      echo "Configuration:"
      echo "  Warmup runs: $WARMUP_RUNS"
      echo "  Benchmark runs: $BENCH_RUNS"
      echo "  Results directory: $RESULTS_DIR"
      echo "  Timestamp: $TIMESTAMP"
      echo ""
      echo "Scenarios to test: ${SCENARIOS[*]}"
      echo "Runtime configurations: ${#RUNTIMES[@]}"

      # Check if hyperfine is installed
      if ! command -v hyperfine &> /dev/null; then
          echo -e "${RED}ERROR: hyperfine is not installed${NC}"
          echo "Install with: cargo install hyperfine"
          exit 1
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
        run_timing_benchmarks "$scenario"

        # Overhead binaries
        run_overhead_timing_benchmarks "$scenario"
    done

    # Combine all results with NET calculations
    combine_timing_results

    print_header "BENCHMARK COMPLETE"
    echo -e "${GREEN}All benchmarks completed successfully!${NC}"
    echo "Results saved in: $RESULTS_DIR/"
    echo ""
    echo "Main result files for your thesis:"
    echo "  📊 timing_all_scenarios_${TIMESTAMP}.md (includes NET calculations)"
    echo "  📈 Individual JSON files for detailed graphs"
    echo ""
    echo "NET calculations show pure execution cost after removing WASM runtime overhead!"
}

# Run main function
main "$@"