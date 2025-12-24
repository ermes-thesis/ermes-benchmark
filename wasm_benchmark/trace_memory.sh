#!/bin/bash

# Script per tracciare la memoria (RSS) SINCRONIZZATA
# Esegue 'TestMemoryTimeline' per Hybrid e Standard Cache separatamente.

set -eEuo pipefail
trap 'echo -e "\n${RED}❌ ERROR: Command failed at line $LINENO: $BASH_COMMAND${NC}\n"' ERR

# --- Configurazione ---
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="benchmark_results_timeline/$TIMESTAMP"
TEST_COMPILED_PATH="./bin/built_test.test"
TRACER_SCRIPT_PATH="./memory_tracer.py"
PLOTTER_SCRIPT_PATH="./plot_timeline.py"
PDF_OUTPUT=false

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Parsing dei flag
while [[ $# -gt 0 ]]; do
    case $1 in
        -cb|--compiled-binary)
            TEST_COMPILED_PATH="$2"
            shift 2
            ;;
        --pdf)
            PDF_OUTPUT=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# --- Main ---
print_header "Avvio Tracing Memoria (Hybrid vs Standard)"

# Controlli essenziali
if ! command -v python3 &> /dev/null; then echo -e "${RED}ERRORE: python3 non trovato.${NC}"; exit 1; fi
if [ ! -f "$TRACER_SCRIPT_PATH" ]; then echo -e "${RED}ERRORE: $TRACER_SCRIPT_PATH non trovato.${NC}"; exit 1; fi
if [ ! -f "$PLOTTER_SCRIPT_PATH" ]; then echo -e "${RED}ERRORE: $PLOTTER_SCRIPT_PATH non trovato.${NC}"; exit 1; fi
if [ ! -f "$TEST_COMPILED_PATH" ]; then echo -e "${RED}ERRORE: Binario di test $TEST_COMPILED_PATH non trovato.${NC}"; exit 1; fi

mkdir -p "$RESULTS_DIR"
echo "I file CSV di trace verranno salvati in: $RESULTS_DIR"

declare -a runtimes_to_test=("WasmEdge_interpreter" "WasmEdge_AOT" "Wasmtime_JIT" "Wasmtime_AOT" "Wazero_AOT" "Wazero_interpreter")
declare -a cache_types=("Hybrid" "Standard")

declare -a hybrid_csvs=()
declare -a standard_csvs=()

# --- Esecuzione Test ---
for runtime in "${runtimes_to_test[@]}"; do
    for cache in "${cache_types[@]}"; do
        echo "-> Tracing: $runtime [Cache: $cache]"
        csv_file="$RESULTS_DIR/trace_sync_${runtime}_${cache}.csv"

        # Esegui il TRACER, passando anche il tipo di cache come argomento al test Go
        python3 "$TRACER_SCRIPT_PATH" --output "$csv_file" -- \
            "$TEST_COMPILED_PATH" -test.run ^TestMemoryTimeline$ "$runtime" "$cache"

        # Separiamo le liste per generare grafici puliti
        if [[ "$cache" == "Hybrid" ]]; then
            hybrid_csvs+=("$csv_file")
        else
            standard_csvs+=("$csv_file")
        fi
    done
done


# --- 3. Generazione Grafici ---
print_header "Generazione Grafici Timeline"

generate_plot() {
    local label=$1
    local output_file=$2
    local files_ref=$3
    local files=("${!files_ref}") # Dereference array

    if [ ${#files[@]} -eq 0 ]; then
        echo -e "${RED}Nessun file CSV per $label.${NC}"
        return
    fi

    echo "Generando grafico per $label..."

    local cmd_args=("--output" "$output_file")
    if [[ "$PDF_OUTPUT" == "true" ]]; then
        cmd_args+=("--pdf")
    fi
    cmd_args+=("${files[@]}")

    if python3 "$PLOTTER_SCRIPT_PATH" "${cmd_args[@]}"; then
        echo -e "${GREEN}✓ Salvato: $output_file${NC}"
    else
        echo -e "${RED}✗ Errore grafico $label.${NC}"
    fi
}

# Genera grafico Hybrid
generate_plot "Hybrid Cache" "memory_timeline_hybrid.png" hybrid_csvs[@]

# Genera grafico Standard
generate_plot "Standard Cache" "memory_timeline_standard.png" standard_csvs[@]

# Opzionale: Genera grafico combinato (tutto insieme)
# all_csvs=("${hybrid_csvs[@]}" "${standard_csvs[@]}")
# generate_plot "All" "memory_timeline_all.png" all_csvs[@]

print_header "Tracing Completato"