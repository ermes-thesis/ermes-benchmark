#!/bin/bash

# Script per tracciare la memoria (RSS) SINCRONIZZATA
# Esegue 'TestMemoryTimeline' (che stampa "SYNC_POINT")
# e lo passa a 'memory_tracer.py' (che ascolta).

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
print_header "Avvio Tracing Memoria Sincronizzato (RSS)"

# Controlli essenziali
if ! command -v python3 &> /dev/null; then echo -e "${RED}ERRORE: python3 non trovato.${NC}"; exit 1; fi
if [ ! -f "$TRACER_SCRIPT_PATH" ]; then echo -e "${RED}ERRORE: $TRACER_SCRIPT_PATH non trovato.${NC}"; exit 1; fi
if [ ! -f "$PLOTTER_SCRIPT_PATH" ]; then echo -e "${RED}ERRORE: $PLOTTER_SCRIPT_PATH non trovato.${NC}"; exit 1; fi
if [ ! -f "$TEST_COMPILED_PATH" ]; then echo -e "${RED}ERRORE: Binario di test $TEST_COMPILED_PATH non trovato.${NC}"; exit 1; fi

mkdir -p "$RESULTS_DIR"
echo "I file CSV di trace verranno salvati in: $RESULTS_DIR"

declare -a csv_files=()
declare -a runtimes_to_test=("wasmedge" "wasmtime" "wazero")

# --- Esecuzione Test ---
for runtime in "${runtimes_to_test[@]}"; do
    echo "-> Tracing: $runtime (sincronizzato)"
    csv_file="$RESULTS_DIR/trace_sync_${runtime}.csv"

    # Esegui il TRACER, che a sua volta ESEGUE il test Go
    python3 "$TRACER_SCRIPT_PATH" --output "$csv_file" -- \
        "$TEST_COMPILED_PATH" -test.run ^TestMemoryTimeline$ "$runtime"

    csv_files+=("$csv_file")
done


# --- 3. Generazione Grafico ---
print_header "Generazione Grafico Timeline Sincronizzato"

if [ ${#csv_files[@]} -eq 0 ]; then
    echo -e "${RED}Nessun file CSV generato. Impossibile creare il grafico.${NC}"
    exit 1
fi

plot_cmd_args=()
plot_cmd_args+=("${csv_files[@]}") # Aggiungi tutti i file CSV

timeline_output_file="memory_timeline.png"
if [[ "$PDF_OUTPUT" == "true" ]]; then
    plot_cmd_args+=("--pdf")
    timeline_output_file="memory_timeline.pdf"
fi

if python3 "$PLOTTER_SCRIPT_PATH" "${plot_cmd_args[@]}"; then
    echo -e "${GREEN}✓ Grafico timeline salvato in: $timeline_output_file${NC}"
else
    echo -e "${RED}✗ Errore durante la generazione del grafico timeline.${NC}"
fi

print_header "Tracing Completato"