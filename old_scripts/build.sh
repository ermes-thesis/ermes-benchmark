#!/bin/bash

# Exit on error
set -e

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse command line arguments
DISABLE_OPTS=true
OUTPUT_BUILD_DIR="bin"

while [[ $# -gt 0 ]]; do
    case $1 in
        --enable-opts)
            DISABLE_OPTS=false
            shift
            ;;
        -ob|--output-build-dir)
            shift
            if [[ $# -gt 0 ]]; then
              OUTPUT_BUILD_DIR=$1
              shift
            else
              echo "must specify a valid dir name"
              exit 1
            fi
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -eb, --enable-opts            Enable Go compiler optimizations (default: disabled)"
            echo "  -ob, --output-build-dir       Specify output directory (default: bin)"
            echo "  -h,  --help                   Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                           # Build with optimizations disabled"
            echo "  $0 --enable-opts             # Build with optimizations enabled"
            echo "  $0 -ob custom_bin            # Build to custom_bin directory"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Set build flags based on optimization setting
if [ "$DISABLE_OPTS" = true ]; then
    BUILD_FLAGS=(-gcflags="-N -l")
    echo -e "${YELLOW}Building with Go compiler optimizations DISABLED${NC}"
else
    BUILD_FLAGS=()
    echo -e "${YELLOW}Building with Go compiler optimizations ENABLED${NC}"
fi

# Create "${OUTPUT_BUILD_DIR}" directory if it doesn't exist
mkdir -p "${OUTPUT_BUILD_DIR}"

echo "Building all Go projects..."

echo -e "\n${GREEN}Building overheads wasmedge AOT no_opts implementations...${NC}"

if [ -f "overheads/wasmedge/AOT/no_opts/fibonacci/main.go" ]; then
    echo "Building overheads/wasmedge/AOT/no_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_aot_noopts_Fibonacci overheads/wasmedge/AOT/no_opts/fibonacci/main.go
fi

if [ -f "overheads/wasmedge/AOT/no_opts/fibonacciTail/main.go" ]; then
    echo "Building overheads/wasmedge/AOT/no_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_aot_noopts_TailFibonacci overheads/wasmedge/AOT/no_opts/fibonacciTail/main.go
fi

if [ -f "overheads/wasmedge/AOT/no_opts/lightweight/main.go" ]; then
    echo "Building overheads/wasmedge/AOT/no_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_aot_noopts_Lightweight overheads/wasmedge/AOT/no_opts/lightweight/main.go
fi

if [ -f "overheads/wasmedge/AOT/no_opts/primeNums/main.go" ]; then
    echo "Building overheads/wasmedge/AOT/no_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_aot_noopts_PrimeNumbers overheads/wasmedge/AOT/no_opts/primeNums/main.go
fi

if [ -f "overheads/wasmedge/AOT/no_opts/hostFns/main.go" ]; then
    echo "Building overheads/wasmedge/AOT/no_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_aot_noopts_HostFns overheads/wasmedge/AOT/no_opts/hostFns/main.go
fi

# Build overheads wasmedge AOT w_opts implementations
echo -e "\n${GREEN}Building overheads wasmedge AOT w_opts implementations...${NC}"

if [ -f "overheads/wasmedge/AOT/w_opts/fibonacci/main.go" ]; then
    echo "Building overheads/wasmedge/AOT/w_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_aot_wopts_Fibonacci overheads/wasmedge/AOT/w_opts/fibonacci/main.go
fi

if [ -f "overheads/wasmedge/AOT/w_opts/fibonacciTail/main.go" ]; then
    echo "Building overheads/wasmedge/AOT/w_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_aot_wopts_TailFibonacci overheads/wasmedge/AOT/w_opts/fibonacciTail/main.go
fi

if [ -f "overheads/wasmedge/AOT/w_opts/lightweight/main.go" ]; then
    echo "Building overheads/wasmedge/AOT/w_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_aot_wopts_Lightweight overheads/wasmedge/AOT/w_opts/lightweight/main.go
fi

if [ -f "overheads/wasmedge/AOT/w_opts/primeNums/main.go" ]; then
    echo "Building overheads/wasmedge/AOT/w_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_aot_wopts_PrimeNumbers overheads/wasmedge/AOT/w_opts/primeNums/main.go
fi

if [ -f "overheads/wasmedge/AOT/w_opts/hostFns/main.go" ]; then
    echo "Building overheads/wasmedge/AOT/w_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_aot_wopts_HostFns overheads/wasmedge/AOT/w_opts/hostFns/main.go
fi

# Build overheads wasmedge interpreter no_opts implementations
echo -e "\n${GREEN}Building overheads wasmedge interpreter no_opts implementations...${NC}"

if [ -f "overheads/wasmedge/interpreter/no_opts/fibonacci/main.go" ]; then
    echo "Building overheads/wasmedge/interpreter/no_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_interpreter_noopts_Fibonacci overheads/wasmedge/interpreter/no_opts/fibonacci/main.go
fi

if [ -f "overheads/wasmedge/interpreter/no_opts/fibonacciTail/main.go" ]; then
    echo "Building overheads/wasmedge/interpreter/no_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_interpreter_noopts_TailFibonacci overheads/wasmedge/interpreter/no_opts/fibonacciTail/main.go
fi

if [ -f "overheads/wasmedge/interpreter/no_opts/lightweight/main.go" ]; then
    echo "Building overheads/wasmedge/interpreter/no_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_interpreter_noopts_Lightweight overheads/wasmedge/interpreter/no_opts/lightweight/main.go
fi

if [ -f "overheads/wasmedge/interpreter/no_opts/primeNums/main.go" ]; then
    echo "Building overheads/wasmedge/interpreter/no_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_interpreter_noopts_PrimeNumbers overheads/wasmedge/interpreter/no_opts/primeNums/main.go
fi

if [ -f "overheads/wasmedge/interpreter/no_opts/hostFns/main.go" ]; then
    echo "Building overheads/wasmedge/interpreter/no_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_interpreter_noopts_HostFns overheads/wasmedge/interpreter/no_opts/hostFns/main.go
fi

# Build overheads wasmedge interpreter w_opts implementations
echo -e "\n${GREEN}Building overheads wasmedge interpreter w_opts implementations...${NC}"

if [ -f "overheads/wasmedge/interpreter/w_opts/fibonacci/main.go" ]; then
    echo "Building overheads/wasmedge/interpreter/w_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_interpreter_wopts_Fibonacci overheads/wasmedge/interpreter/w_opts/fibonacci/main.go
fi

if [ -f "overheads/wasmedge/interpreter/w_opts/fibonacciTail/main.go" ]; then
    echo "Building overheads/wasmedge/interpreter/w_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_interpreter_wopts_TailFibonacci overheads/wasmedge/interpreter/w_opts/fibonacciTail/main.go
fi

if [ -f "overheads/wasmedge/interpreter/w_opts/lightweight/main.go" ]; then
    echo "Building overheads/wasmedge/interpreter/w_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_interpreter_wopts_Lightweight overheads/wasmedge/interpreter/w_opts/lightweight/main.go
fi

if [ -f "overheads/wasmedge/interpreter/w_opts/primeNums/main.go" ]; then
    echo "Building overheads/wasmedge/interpreter/w_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_interpreter_wopts_PrimeNumbers overheads/wasmedge/interpreter/w_opts/primeNums/main.go
fi

if [ -f "overheads/wasmedge/interpreter/w_opts/hostFns/main.go" ]; then
    echo "Building overheads/wasmedge/interpreter/w_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmedge_interpreter_wopts_HostFns overheads/wasmedge/interpreter/w_opts/hostFns/main.go
fi

# Build overheads wasmtime JIT no_opts implementations
echo -e "\n${GREEN}Building overheads wasmtime JIT no_opts implementations...${NC}"

if [ -f "overheads/wasmtime/JIT/no_opts/fibonacci/main.go" ]; then
    echo "Building overheads/wasmtime/JIT/no_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_jit_noopts_Fibonacci overheads/wasmtime/JIT/no_opts/fibonacci/main.go
fi

if [ -f "overheads/wasmtime/JIT/no_opts/fibonacciTail/main.go" ]; then
    echo "Building overheads/wasmtime/JIT/no_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_jit_noopts_TailFibonacci overheads/wasmtime/JIT/no_opts/fibonacciTail/main.go
fi

if [ -f "overheads/wasmtime/JIT/no_opts/lightweight/main.go" ]; then
    echo "Building overheads/wasmtime/JIT/no_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_jit_noopts_Lightweight overheads/wasmtime/JIT/no_opts/lightweight/main.go
fi

if [ -f "overheads/wasmtime/JIT/no_opts/primeNums/main.go" ]; then
    echo "Building overheads/wasmtime/JIT/no_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_jit_noopts_PrimeNumbers overheads/wasmtime/JIT/no_opts/primeNums/main.go
fi

if [ -f "overheads/wasmtime/JIT/no_opts/hostFns/main.go" ]; then
    echo "Building overheads/wasmtime/JIT/no_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_jit_noopts_HostFns overheads/wasmtime/JIT/no_opts/hostFns/main.go
fi

# Build overheads wasmtime JIT w_opts implementations
echo -e "\n${GREEN}Building overheads wasmtime JIT w_opts implementations...${NC}"

if [ -f "overheads/wasmtime/JIT/w_opts/fibonacci/main.go" ]; then
    echo "Building overheads/wasmtime/JIT/w_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_jit_wopts_Fibonacci overheads/wasmtime/JIT/w_opts/fibonacci/main.go
fi

if [ -f "overheads/wasmtime/JIT/w_opts/fibonacciTail/main.go" ]; then
    echo "Building overheads/wasmtime/JIT/w_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_jit_wopts_TailFibonacci overheads/wasmtime/JIT/w_opts/fibonacciTail/main.go
fi

if [ -f "overheads/wasmtime/JIT/w_opts/lightweight/main.go" ]; then
    echo "Building overheads/wasmtime/JIT/w_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_jit_wopts_Lightweight overheads/wasmtime/JIT/w_opts/lightweight/main.go
fi

if [ -f "overheads/wasmtime/JIT/w_opts/primeNums/main.go" ]; then
    echo "Building overheads/wasmtime/JIT/w_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_jit_wopts_PrimeNumbers overheads/wasmtime/JIT/w_opts/primeNums/main.go
fi

if [ -f "overheads/wasmtime/JIT/w_opts/hostFns/main.go" ]; then
    echo "Building overheads/wasmtime/JIT/w_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_jit_wopts_HostFns overheads/wasmtime/JIT/w_opts/hostFns/main.go
fi

# Build overheads wasmtime AOT no_opts implementations
echo -e "\n${GREEN}Building overheads wasmtime AOT no_opts implementations...${NC}"

if [ -f "overheads/wasmtime/AOT/no_opts/fibonacci/main.go" ]; then
    echo "Building overheads/wasmtime/AOT/no_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_aot_noopts_Fibonacci overheads/wasmtime/AOT/no_opts/fibonacci/main.go
fi

if [ -f "overheads/wasmtime/AOT/no_opts/fibonacciTail/main.go" ]; then
    echo "Building overheads/wasmtime/AOT/no_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_aot_noopts_TailFibonacci overheads/wasmtime/AOT/no_opts/fibonacciTail/main.go
fi

if [ -f "overheads/wasmtime/AOT/no_opts/lightweight/main.go" ]; then
    echo "Building overheads/wasmtime/AOT/no_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_aot_noopts_Lightweight overheads/wasmtime/AOT/no_opts/lightweight/main.go
fi

if [ -f "overheads/wasmtime/AOT/no_opts/primeNums/main.go" ]; then
    echo "Building overheads/wasmtime/AOT/no_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_aot_noopts_PrimeNumbers overheads/wasmtime/AOT/no_opts/primeNums/main.go
fi

if [ -f "overheads/wasmtime/AOT/no_opts/hostFns/main.go" ]; then
    echo "Building overheads/wasmtime/AOT/no_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_aot_noopts_HostFns overheads/wasmtime/AOT/no_opts/hostFns/main.go
fi

# Build overheads wasmtime AOT w_opts implementations
echo -e "\n${GREEN}Building overheads wasmtime AOT w_opts implementations...${NC}"

if [ -f "overheads/wasmtime/AOT/w_opts/fibonacci/main.go" ]; then
    echo "Building overheads/wasmtime/AOT/w_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_aot_wopts_Fibonacci overheads/wasmtime/AOT/w_opts/fibonacci/main.go
fi

if [ -f "overheads/wasmtime/AOT/w_opts/fibonacciTail/main.go" ]; then
    echo "Building overheads/wasmtime/AOT/w_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_aot_wopts_TailFibonacci overheads/wasmtime/AOT/w_opts/fibonacciTail/main.go
fi

if [ -f "overheads/wasmtime/AOT/w_opts/lightweight/main.go" ]; then
    echo "Building overheads/wasmtime/AOT/w_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_aot_wopts_Lightweight overheads/wasmtime/AOT/w_opts/lightweight/main.go
fi

if [ -f "overheads/wasmtime/AOT/w_opts/primeNums/main.go" ]; then
    echo "Building overheads/wasmtime/AOT/w_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_aot_wopts_PrimeNumbers overheads/wasmtime/AOT/w_opts/primeNums/main.go
fi

if [ -f "overheads/wasmtime/AOT/w_opts/hostFns/main.go" ]; then
    echo "Building overheads/wasmtime/AOT/w_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wasmtime_aot_wopts_HostFns overheads/wasmtime/AOT/w_opts/hostFns/main.go
fi

# Build overheads wazero AOT no_opts implementations
echo -e "\n${GREEN}Building overheads wazero AOT no_opts implementations...${NC}"

if [ -f "overheads/wazero/AOT/no_opts/fibonacci/main.go" ]; then
    echo "Building overheads/wazero/AOT/no_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_aot_noopts_Fibonacci overheads/wazero/AOT/no_opts/fibonacci/main.go
fi

if [ -f "overheads/wazero/AOT/no_opts/fibonacciTail/main.go" ]; then
    echo "Building overheads/wazero/AOT/no_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_aot_noopts_TailFibonacci overheads/wazero/AOT/no_opts/fibonacciTail/main.go
fi

if [ -f "overheads/wazero/AOT/no_opts/lightweight/main.go" ]; then
    echo "Building overheads/wazero/AOT/no_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_aot_noopts_Lightweight overheads/wazero/AOT/no_opts/lightweight/main.go
fi

if [ -f "overheads/wazero/AOT/no_opts/primeNums/main.go" ]; then
    echo "Building overheads/wazero/AOT/no_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_aot_noopts_PrimeNumbers overheads/wazero/AOT/no_opts/primeNums/main.go
fi

if [ -f "overheads/wazero/AOT/no_opts/hostFns/main.go" ]; then
    echo "Building overheads/wazero/AOT/no_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_aot_noopts_HostFns overheads/wazero/AOT/no_opts/hostFns/main.go
fi

# Build overheads wazero AOT w_opts implementations
echo -e "\n${GREEN}Building overheads wazero AOT w_opts implementations...${NC}"

if [ -f "overheads/wazero/AOT/w_opts/fibonacci/main.go" ]; then
    echo "Building overheads/wazero/AOT/w_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_aot_wopts_Fibonacci overheads/wazero/AOT/w_opts/fibonacci/main.go
fi

if [ -f "overheads/wazero/AOT/w_opts/fibonacciTail/main.go" ]; then
    echo "Building overheads/wazero/AOT/w_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_aot_wopts_TailFibonacci overheads/wazero/AOT/w_opts/fibonacciTail/main.go
fi

if [ -f "overheads/wazero/AOT/w_opts/lightweight/main.go" ]; then
    echo "Building overheads/wazero/AOT/w_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_aot_wopts_Lightweight overheads/wazero/AOT/w_opts/lightweight/main.go
fi

if [ -f "overheads/wazero/AOT/w_opts/primeNums/main.go" ]; then
    echo "Building overheads/wazero/AOT/w_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_aot_wopts_PrimeNumbers overheads/wazero/AOT/w_opts/primeNums/main.go
fi

if [ -f "overheads/wazero/AOT/w_opts/hostFns/main.go" ]; then
    echo "Building overheads/wazero/AOT/w_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_aot_wopts_HostFns overheads/wazero/AOT/w_opts/hostFns/main.go
fi

# Build overheads wazero interpreter no_opts implementations
echo -e "\n${GREEN}Building overheads wazero interpreter no_opts implementations...${NC}"

if [ -f "overheads/wazero/interpreter/no_opts/fibonacci/main.go" ]; then
    echo "Building overheads/wazero/interpreter/no_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_interpreter_noopts_Fibonacci overheads/wazero/interpreter/no_opts/fibonacci/main.go
fi

if [ -f "overheads/wazero/interpreter/no_opts/fibonacciTail/main.go" ]; then
    echo "Building overheads/wazero/interpreter/no_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_interpreter_noopts_TailFibonacci overheads/wazero/interpreter/no_opts/fibonacciTail/main.go
fi

if [ -f "overheads/wazero/interpreter/no_opts/lightweight/main.go" ]; then
    echo "Building overheads/wazero/interpreter/no_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_interpreter_noopts_Lightweight overheads/wazero/interpreter/no_opts/lightweight/main.go
fi

if [ -f "overheads/wazero/interpreter/no_opts/primeNums/main.go" ]; then
    echo "Building overheads/wazero/interpreter/no_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_interpreter_noopts_PrimeNumbers overheads/wazero/interpreter/no_opts/primeNums/main.go
fi

if [ -f "overheads/wazero/interpreter/no_opts/hostFns/main.go" ]; then
    echo "Building overheads/wazero/interpreter/no_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_interpreter_noopts_HostFns overheads/wazero/interpreter/no_opts/hostFns/main.go
fi

# Build overheads wazero interpreter w_opts implementations
echo -e "\n${GREEN}Building overheads wazero interpreter w_opts implementations...${NC}"

if [ -f "overheads/wazero/interpreter/w_opts/fibonacci/main.go" ]; then
    echo "Building overheads/wazero/interpreter/w_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_interpreter_wopts_Fibonacci overheads/wazero/interpreter/w_opts/fibonacci/main.go
fi

if [ -f "overheads/wazero/interpreter/w_opts/fibonacciTail/main.go" ]; then
    echo "Building overheads/wazero/interpreter/w_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_interpreter_wopts_TailFibonacci overheads/wazero/interpreter/w_opts/fibonacciTail/main.go
fi

if [ -f "overheads/wazero/interpreter/w_opts/lightweight/main.go" ]; then
    echo "Building overheads/wazero/interpreter/w_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_interpreter_wopts_Lightweight overheads/wazero/interpreter/w_opts/lightweight/main.go
fi

if [ -f "overheads/wazero/interpreter/w_opts/primeNums/main.go" ]; then
    echo "Building overheads/wazero/interpreter/w_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_interpreter_wopts_PrimeNumbers overheads/wazero/interpreter/w_opts/primeNums/main.go
fi

if [ -f "overheads/wazero/interpreter/w_opts/hostFns/main.go" ]; then
    echo "Building overheads/wazero/interpreter/w_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/overheads_wazero_interpreter_wopts_HostFns overheads/wazero/interpreter/w_opts/hostFns/main.go
fi

# Build native implementations
echo -e "\n${GREEN}Building native implementations...${NC}"

if [ -f "native/fibonacci/main.go" ]; then
    echo "Building native/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/native_Fibonacci native/fibonacci/main.go
fi

if [ -f "native/fibonacciTail/main.go" ]; then
    echo "Building native/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/native_TailFibonacci native/fibonacciTail/main.go
fi

if [ -f "native/lightweight/main.go" ]; then
    echo "Building native/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/native_Lightweight native/lightweight/main.go
fi

if [ -f "native/primeNums/main.go" ]; then
    echo "Building native/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/native_PrimeNumbers native/primeNums/main.go
fi

# Build wasmedge AOT no_opts implementations
echo -e "\n${GREEN}Building wasmedge AOT no_opts implementations...${NC}"

if [ -f "wasmedge/AOT/no_opts/fibonacci/main.go" ]; then
    echo "Building wasmedge/AOT/no_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_aot_noopts_Fibonacci wasmedge/AOT/no_opts/fibonacci/main.go
fi

if [ -f "wasmedge/AOT/no_opts/fibonacciTail/main.go" ]; then
    echo "Building wasmedge/AOT/no_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_aot_noopts_TailFibonacci wasmedge/AOT/no_opts/fibonacciTail/main.go
fi

if [ -f "wasmedge/AOT/no_opts/lightweight/main.go" ]; then
    echo "Building wasmedge/AOT/no_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_aot_noopts_Lightweight wasmedge/AOT/no_opts/lightweight/main.go
fi

if [ -f "wasmedge/AOT/no_opts/primeNums/main.go" ]; then
    echo "Building wasmedge/AOT/no_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_aot_noopts_PrimeNumbers wasmedge/AOT/no_opts/primeNums/main.go
fi

if [ -f "wasmedge/AOT/no_opts/hostFns/main.go" ]; then
    echo "Building wasmedge/AOT/no_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_aot_noopts_HostFns wasmedge/AOT/no_opts/hostFns/main.go
fi

# Build wasmedge AOT w_opts implementations
echo -e "\n${GREEN}Building wasmedge AOT w_opts implementations...${NC}"

if [ -f "wasmedge/AOT/w_opts/fibonacci/main.go" ]; then
    echo "Building wasmedge/AOT/w_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_aot_wopts_Fibonacci wasmedge/AOT/w_opts/fibonacci/main.go
fi

if [ -f "wasmedge/AOT/w_opts/fibonacciTail/main.go" ]; then
    echo "Building wasmedge/AOT/w_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_aot_wopts_TailFibonacci wasmedge/AOT/w_opts/fibonacciTail/main.go
fi

if [ -f "wasmedge/AOT/w_opts/lightweight/main.go" ]; then
    echo "Building wasmedge/AOT/w_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_aot_wopts_Lightweight wasmedge/AOT/w_opts/lightweight/main.go
fi

if [ -f "wasmedge/AOT/w_opts/primeNums/main.go" ]; then
    echo "Building wasmedge/AOT/w_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_aot_wopts_PrimeNumbers wasmedge/AOT/w_opts/primeNums/main.go
fi

if [ -f "wasmedge/AOT/w_opts/hostFns/main.go" ]; then
    echo "Building wasmedge/AOT/w_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_aot_wopts_HostFns wasmedge/AOT/w_opts/hostFns/main.go
fi

# Build wasmedge interpreter no_opts implementations
echo -e "\n${GREEN}Building wasmedge interpreter no_opts implementations...${NC}"

if [ -f "wasmedge/interpreter/no_opts/fibonacci/main.go" ]; then
    echo "Building wasmedge/interpreter/no_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_interpreter_noopts_Fibonacci wasmedge/interpreter/no_opts/fibonacci/main.go
fi

if [ -f "wasmedge/interpreter/no_opts/fibonacciTail/main.go" ]; then
    echo "Building wasmedge/interpreter/no_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_interpreter_noopts_TailFibonacci wasmedge/interpreter/no_opts/fibonacciTail/main.go
fi

if [ -f "wasmedge/interpreter/no_opts/lightweight/main.go" ]; then
    echo "Building wasmedge/interpreter/no_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_interpreter_noopts_Lightweight wasmedge/interpreter/no_opts/lightweight/main.go
fi

if [ -f "wasmedge/interpreter/no_opts/primeNums/main.go" ]; then
    echo "Building wasmedge/interpreter/no_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_interpreter_noopts_PrimeNumbers wasmedge/interpreter/no_opts/primeNums/main.go
fi

if [ -f "wasmedge/interpreter/no_opts/hostFns/main.go" ]; then
    echo "Building wasmedge/interpreter/no_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_interpreter_noopts_HostFns wasmedge/interpreter/no_opts/hostFns/main.go
fi

# Build wasmedge interpreter w_opts implementations
echo -e "\n${GREEN}Building wasmedge interpreter w_opts implementations...${NC}"

if [ -f "wasmedge/interpreter/w_opts/fibonacci/main.go" ]; then
    echo "Building wasmedge/interpreter/w_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_interpreter_wopts_Fibonacci wasmedge/interpreter/w_opts/fibonacci/main.go
fi

if [ -f "wasmedge/interpreter/w_opts/fibonacciTail/main.go" ]; then
    echo "Building wasmedge/interpreter/w_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_interpreter_wopts_TailFibonacci wasmedge/interpreter/w_opts/fibonacciTail/main.go
fi

if [ -f "wasmedge/interpreter/w_opts/lightweight/main.go" ]; then
    echo "Building wasmedge/interpreter/w_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_interpreter_wopts_Lightweight wasmedge/interpreter/w_opts/lightweight/main.go
fi

if [ -f "wasmedge/interpreter/w_opts/primeNums/main.go" ]; then
    echo "Building wasmedge/interpreter/w_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_interpreter_wopts_PrimeNumbers wasmedge/interpreter/w_opts/primeNums/main.go
fi

if [ -f "wasmedge/interpreter/w_opts/hostFns/main.go" ]; then
    echo "Building wasmedge/interpreter/w_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmedge_interpreter_wopts_HostFns wasmedge/interpreter/w_opts/hostFns/main.go
fi

# Build wasmtime JIT no_opts implementations
echo -e "\n${GREEN}Building wasmtime JIT no_opts implementations...${NC}"

if [ -f "wasmtime/JIT/no_opts/fibonacci/main.go" ]; then
    echo "Building wasmtime/JIT/no_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_jit_noopts_Fibonacci wasmtime/JIT/no_opts/fibonacci/main.go
fi

if [ -f "wasmtime/JIT/no_opts/fibonacciTail/main.go" ]; then
    echo "Building wasmtime/JIT/no_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_jit_noopts_TailFibonacci wasmtime/JIT/no_opts/fibonacciTail/main.go
fi

if [ -f "wasmtime/JIT/no_opts/lightweight/main.go" ]; then
    echo "Building wasmtime/JIT/no_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_jit_noopts_Lightweight wasmtime/JIT/no_opts/lightweight/main.go
fi

if [ -f "wasmtime/JIT/no_opts/primeNums/main.go" ]; then
    echo "Building wasmtime/JIT/no_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_jit_noopts_PrimeNumbers wasmtime/JIT/no_opts/primeNums/main.go
fi

if [ -f "wasmtime/JIT/no_opts/hostFns/main.go" ]; then
    echo "Building wasmtime/JIT/no_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_jit_noopts_HostFns wasmtime/JIT/no_opts/hostFns/main.go
fi

# Build wasmtime JIT w_opts implementations
echo -e "\n${GREEN}Building wasmtime JIT w_opts implementations...${NC}"

if [ -f "wasmtime/JIT/w_opts/fibonacci/main.go" ]; then
    echo "Building wasmtime/JIT/w_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_jit_wopts_Fibonacci wasmtime/JIT/w_opts/fibonacci/main.go
fi

if [ -f "wasmtime/JIT/w_opts/fibonacciTail/main.go" ]; then
    echo "Building wasmtime/JIT/w_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_jit_wopts_TailFibonacci wasmtime/JIT/w_opts/fibonacciTail/main.go
fi

if [ -f "wasmtime/JIT/w_opts/lightweight/main.go" ]; then
    echo "Building wasmtime/JIT/w_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_jit_wopts_Lightweight wasmtime/JIT/w_opts/lightweight/main.go
fi

if [ -f "wasmtime/JIT/w_opts/primeNums/main.go" ]; then
    echo "Building wasmtime/JIT/w_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_jit_wopts_PrimeNumbers wasmtime/JIT/w_opts/primeNums/main.go
fi

if [ -f "wasmtime/JIT/w_opts/hostFns/main.go" ]; then
    echo "Building wasmtime/JIT/w_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_jit_wopts_HostFns wasmtime/JIT/w_opts/hostFns/main.go
fi

# Build wasmtime AOT no_opts implementations
echo -e "\n${GREEN}Building wasmtime AOT no_opts implementations...${NC}"

if [ -f "wasmtime/AOT/no_opts/fibonacci/main.go" ]; then
    echo "Building wasmtime/AOT/no_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_aot_noopts_Fibonacci wasmtime/AOT/no_opts/fibonacci/main.go
fi

if [ -f "wasmtime/AOT/no_opts/fibonacciTail/main.go" ]; then
    echo "Building wasmtime/AOT/no_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_aot_noopts_TailFibonacci wasmtime/AOT/no_opts/fibonacciTail/main.go
fi

if [ -f "wasmtime/AOT/no_opts/lightweight/main.go" ]; then
    echo "Building wasmtime/AOT/no_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_aot_noopts_Lightweight wasmtime/AOT/no_opts/lightweight/main.go
fi

if [ -f "wasmtime/AOT/no_opts/primeNums/main.go" ]; then
    echo "Building wasmtime/AOT/no_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_aot_noopts_PrimeNumbers wasmtime/AOT/no_opts/primeNums/main.go
fi

if [ -f "wasmtime/AOT/no_opts/hostFns/main.go" ]; then
    echo "Building wasmtime/AOT/no_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_aot_noopts_HostFns wasmtime/AOT/no_opts/hostFns/main.go
fi

# Build wasmtime AOT w_opts implementations
echo -e "\n${GREEN}Building wasmtime AOT w_opts implementations...${NC}"

if [ -f "wasmtime/AOT/w_opts/fibonacci/main.go" ]; then
    echo "Building wasmtime/AOT/w_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_aot_wopts_Fibonacci wasmtime/AOT/w_opts/fibonacci/main.go
fi

if [ -f "wasmtime/AOT/w_opts/fibonacciTail/main.go" ]; then
    echo "Building wasmtime/AOT/w_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_aot_wopts_TailFibonacci wasmtime/AOT/w_opts/fibonacciTail/main.go
fi

if [ -f "wasmtime/AOT/w_opts/lightweight/main.go" ]; then
    echo "Building wasmtime/AOT/w_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_aot_wopts_Lightweight wasmtime/AOT/w_opts/lightweight/main.go
fi

if [ -f "wasmtime/AOT/w_opts/primeNums/main.go" ]; then
    echo "Building wasmtime/AOT/w_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_aot_wopts_PrimeNumbers wasmtime/AOT/w_opts/primeNums/main.go
fi

if [ -f "wasmtime/AOT/w_opts/hostFns/main.go" ]; then
    echo "Building wasmtime/AOT/w_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wasmtime_aot_wopts_HostFns wasmtime/AOT/w_opts/hostFns/main.go
fi

# Build wazero AOT no_opts implementations
echo -e "\n${GREEN}Building wazero AOT no_opts implementations...${NC}"

if [ -f "wazero/AOT/no_opts/fibonacci/main.go" ]; then
    echo "Building wazero/AOT/no_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_aot_noopts_Fibonacci wazero/AOT/no_opts/fibonacci/main.go
fi

if [ -f "wazero/AOT/no_opts/fibonacciTail/main.go" ]; then
    echo "Building wazero/AOT/no_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_aot_noopts_TailFibonacci wazero/AOT/no_opts/fibonacciTail/main.go
fi

if [ -f "wazero/AOT/no_opts/lightweight/main.go" ]; then
    echo "Building wazero/AOT/no_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_aot_noopts_Lightweight wazero/AOT/no_opts/lightweight/main.go
fi

if [ -f "wazero/AOT/no_opts/primeNums/main.go" ]; then
    echo "Building wazero/AOT/no_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_aot_noopts_PrimeNumbers wazero/AOT/no_opts/primeNums/main.go
fi

if [ -f "wazero/AOT/no_opts/hostFns/main.go" ]; then
    echo "Building wazero/AOT/no_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_aot_noopts_HostFns wazero/AOT/no_opts/hostFns/main.go
fi

# Build wazero AOT w_opts implementations
echo -e "\n${GREEN}Building wazero AOT w_opts implementations...${NC}"

if [ -f "wazero/AOT/w_opts/fibonacci/main.go" ]; then
    echo "Building wazero/AOT/w_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_aot_wopts_Fibonacci wazero/AOT/w_opts/fibonacci/main.go
fi

if [ -f "wazero/AOT/w_opts/fibonacciTail/main.go" ]; then
    echo "Building wazero/AOT/w_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_aot_wopts_TailFibonacci wazero/AOT/w_opts/fibonacciTail/main.go
fi

if [ -f "wazero/AOT/w_opts/lightweight/main.go" ]; then
    echo "Building wazero/AOT/w_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_aot_wopts_Lightweight wazero/AOT/w_opts/lightweight/main.go
fi

if [ -f "wazero/AOT/w_opts/primeNums/main.go" ]; then
    echo "Building wazero/AOT/w_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_aot_wopts_PrimeNumbers wazero/AOT/w_opts/primeNums/main.go
fi

if [ -f "wazero/AOT/w_opts/hostFns/main.go" ]; then
    echo "Building wazero/AOT/w_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_aot_wopts_HostFns wazero/AOT/w_opts/hostFns/main.go
fi

# Build wazero interpreter no_opts implementations
echo -e "\n${GREEN}Building wazero interpreter no_opts implementations...${NC}"

if [ -f "wazero/interpreter/no_opts/fibonacci/main.go" ]; then
    echo "Building wazero/interpreter/no_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_interpreter_noopts_Fibonacci wazero/interpreter/no_opts/fibonacci/main.go
fi

if [ -f "wazero/interpreter/no_opts/fibonacciTail/main.go" ]; then
    echo "Building wazero/interpreter/no_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_interpreter_noopts_TailFibonacci wazero/interpreter/no_opts/fibonacciTail/main.go
fi

if [ -f "wazero/interpreter/no_opts/lightweight/main.go" ]; then
    echo "Building wazero/interpreter/no_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_interpreter_noopts_Lightweight wazero/interpreter/no_opts/lightweight/main.go
fi

if [ -f "wazero/interpreter/no_opts/primeNums/main.go" ]; then
    echo "Building wazero/interpreter/no_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_interpreter_noopts_PrimeNumbers wazero/interpreter/no_opts/primeNums/main.go
fi

if [ -f "wazero/interpreter/no_opts/hostFns/main.go" ]; then
    echo "Building wazero/interpreter/no_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_interpreter_noopts_HostFns wazero/interpreter/no_opts/hostFns/main.go
fi

# Build wazero interpreter w_opts implementations
echo -e "\n${GREEN}Building wazero interpreter w_opts implementations...${NC}"

if [ -f "wazero/interpreter/w_opts/fibonacci/main.go" ]; then
    echo "Building wazero/interpreter/w_opts/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_interpreter_wopts_Fibonacci wazero/interpreter/w_opts/fibonacci/main.go
fi

if [ -f "wazero/interpreter/w_opts/fibonacciTail/main.go" ]; then
    echo "Building wazero/interpreter/w_opts/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_interpreter_wopts_TailFibonacci wazero/interpreter/w_opts/fibonacciTail/main.go
fi

if [ -f "wazero/interpreter/w_opts/lightweight/main.go" ]; then
    echo "Building wazero/interpreter/w_opts/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_interpreter_wopts_Lightweight wazero/interpreter/w_opts/lightweight/main.go
fi

if [ -f "wazero/interpreter/w_opts/primeNums/main.go" ]; then
    echo "Building wazero/interpreter/w_opts/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_interpreter_wopts_PrimeNumbers wazero/interpreter/w_opts/primeNums/main.go
fi

if [ -f "wazero/interpreter/w_opts/hostFns/main.go" ]; then
    echo "Building wazero/interpreter/w_opts/hostFns..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/wazero_interpreter_wopts_HostFns wazero/interpreter/w_opts/hostFns/main.go
fi

echo -e "\n${GREEN}Build complete! Binaries are in the ${OUTPUT_BUILD_DIR}/ directory.${NC}"