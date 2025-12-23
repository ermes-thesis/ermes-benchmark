#!/bin/bash

# Exit on error
set -e

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for ermes-cli requirement
if ! command -v ermes-cli &> /dev/null; then
    echo -e "${RED}Error: 'ermes-cli' could not be found. Please ensure it is installed and in your PATH.${NC}"
    exit 1
fi

# Parse command line arguments
DISABLE_OPTS=true
OUTPUT_BUILD_DIR="bin"
TEST_COMPILED_FILENAME="built_test.test"

while [[ $# -gt 0 ]]; do
    case $1 in
        --enable-opts)
            DISABLE_OPTS=false
            shift
            ;;
        -bd|--output-build-dir)
            shift
            if [[ $# -gt 0 ]]; then
              OUTPUT_BUILD_DIR=$1
              shift
            else
              echo "must specify a valid dir name"
              exit 1
            fi
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
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -eb, --enable-opts              Enable Go compiler optimizations (default: disabled)"
            echo "  -bd, --output-build-dir         Specify output directory (default: bin)"
            echo "  -bf, --output-build-filename    Specify output filename (default: built_test.test)"
            echo "  -h,  --help                     Show this help message"
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

echo "Build binaries..."

echo -e "\n${GREEN}Building go file: "${OUTPUT_BUILD_DIR}/${TEST_COMPILED_FILENAME}"...${NC}"

go test -c "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}/${TEST_COMPILED_FILENAME}" .

# Build native implementations
echo -e "\n${GREEN}Building native implementations...${NC}"

if [ -f "functions/native/fibonacci/main.go" ]; then
    echo "Building native/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/native_fibonacci functions/native/fibonacci/main.go
fi

if [ -f "functions/native/fibonacciTail/main.go" ]; then
    echo "Building native/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/native_tailFibonacci functions/native/fibonacciTail/main.go
fi

if [ -f "functions/native/lightweight/main.go" ]; then
    echo "Building native/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/native_lightweight functions/native/lightweight/main.go
fi

if [ -f "functions/native/primeNums/main.go" ]; then
    echo "Building native/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/native_primeNums functions/native/primeNums/main.go
fi

# Build WASM binaries via ermes-cli
echo -e "\n${GREEN}Building WASM optimized binaries via ermes-cli...${NC}"

# Define the expected source files for the WASM functions based on the benchmarks.
# Adjust these paths if your source structure is different (e.g., if not in 'functions/').
WASM_SOURCES=(
    "wasm/primeNums.go"
    "wasm/fibonacci.go"
    "wasm/tailFibonacci.go"
    "wasm/lightweight.go"
    "wasm/statefulFunction.go"
)

# Collect valid source files
VALID_SOURCES=()
for src_file in "${WASM_SOURCES[@]}"; do
    if [ -f "functions/$src_file" ]; then
        VALID_SOURCES+=("$src_file")
    else
        echo -e "${YELLOW}Warning: Source file '$src_file' not found. Skipping.${NC}"
    fi
done

# Compile all valid sources in a single command if any exist
if [ ${#VALID_SOURCES[@]} -gt 0 ]; then
    echo "Compiling ${#VALID_SOURCES[@]} WASM functions..."
    ermes-cli compile "${VALID_SOURCES[@]}"
else
    echo -e "${YELLOW}No valid WASM source files found to compile.${NC}"
fi

echo -e "\n${GREEN}Build complete.${NC}"

mkdir -p "_WASM_BINARIES/cpuIntensive/fibonacci"
mkdir -p "_WASM_BINARIES/cpuIntensive/primeNums"
mkdir -p "_WASM_BINARIES/cpuIntensive/tailFibonacci"
mkdir -p "_WASM_BINARIES/lightweight"
mkdir -p "_WASM_BINARIES/stateful"

mv "fibonacci/fibonacci@1.0.0.wasm" "_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts.wasm"
mv "primeNums/primeNums@1.0.0.wasm" "_WASM_BINARIES/cpuIntensive/primeNums/primeNums_wOpts.wasm"
mv "tailFibonacci/tailFibonacci@1.0.0.wasm" "_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_wOpts.wasm"
mv "lightweight/lightweight@1.0.0.wasm" "_WASM_BINARIES/lightweight/lightweight_wOpts.wasm"
mv "statefulFunction/statefulFunction@1.0.0.wasm" "_WASM_BINARIES/stateful/statefulFunction_wOpts.wasm"


echo -e "\n${GREEN}Building WASM unoptimized binaries via ermes-cli...${NC}"

# Compile all valid sources in a single command if any exist
if [ ${#VALID_SOURCES[@]} -gt 0 ]; then
    echo "Compiling ${#VALID_SOURCES[@]} WASM functions..."
    ermes-cli compile "${VALID_SOURCES[@]}" -O=false
else
    echo -e "${YELLOW}No valid WASM source files found to compile.${NC}"
fi

echo -e "\n${GREEN}Build complete.${NC}"

mv "fibonacci/fibonacci@1.0.0.wasm" "_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci.wasm"
mv "primeNums/primeNums@1.0.0.wasm" "_WASM_BINARIES/cpuIntensive/primeNums/primeNums.wasm"
mv "tailFibonacci/tailFibonacci@1.0.0.wasm" "_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci.wasm"
mv "lightweight/lightweight@1.0.0.wasm" "_WASM_BINARIES/lightweight/lightweight.wasm"
mv "statefulFunction/statefulFunction@1.0.0.wasm" "_WASM_BINARIES/stateful/statefulFunction.wasm"

echo -e "\n${GREEN}All builds completed successfully.${NC}"

rm -rf fibonacci primeNums tailFibonacci lightweight statefulFunction

# Wasmedge AOT compilation
echo -e "\n${GREEN}Building WASM AOT binaries via wasmedge...${NC}"
wasmedge compile "_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci.wasm" "_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_noOpts_AOTwasmedge.wasm"
wasmedge compile "_WASM_BINARIES/cpuIntensive/primeNums/primeNums.wasm" "_WASM_BINARIES/cpuIntensive/primeNums/primeNums_noOpts_AOTwasmedge.wasm"
wasmedge compile "_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci.wasm" "_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_noOpts_AOTwasmedge.wasm"
wasmedge compile "_WASM_BINARIES/lightweight/lightweight.wasm" "_WASM_BINARIES/lightweight/lightweight_noOpts_AOTwasmedge.wasm"
wasmedge compile "_WASM_BINARIES/stateful/statefulFunction.wasm" "_WASM_BINARIES/stateful/statefulFunction_noOpts_AOTwasmedge.wasm"

wasmedge compile "_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts.wasm" "_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts_AOTwasmedge.wasm"
wasmedge compile "_WASM_BINARIES/cpuIntensive/primeNums/primeNums_wOpts.wasm" "_WASM_BINARIES/cpuIntensive/primeNums/primeNums_wOpts_AOTwasmedge.wasm"
wasmedge compile "_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_wOpts.wasm" "_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_wOpts_AOTwasmedge.wasm"
wasmedge compile "_WASM_BINARIES/lightweight/lightweight_wOpts.wasm" "_WASM_BINARIES/lightweight/lightweight_wOpts_AOTwasmedge.wasm"
wasmedge compile "_WASM_BINARIES/stateful/statefulFunction_wOpts.wasm" "_WASM_BINARIES/stateful/statefulFunction_wOpts_AOTwasmedge.wasm"

# Wasmtime AOT compilation
echo -e "\n${GREEN}Building WASM AOT binaries via wasmtime...${NC}"
wasmtime compile "_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci.wasm" -o "_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_noOpts_AOTwasmtime.wasm"
wasmtime compile "_WASM_BINARIES/cpuIntensive/primeNums/primeNums.wasm" -o "_WASM_BINARIES/cpuIntensive/primeNums/primeNums_noOpts_AOTwasmtime.wasm"
wasmtime compile "_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci.wasm" -o "_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_noOpts_AOTwasmtime.wasm"
wasmtime compile "_WASM_BINARIES/lightweight/lightweight.wasm" -o "_WASM_BINARIES/lightweight/lightweight_noOpts_AOTwasmtime.wasm"
wasmtime compile "_WASM_BINARIES/stateful/statefulFunction.wasm" -o "_WASM_BINARIES/stateful/statefulFunction_noOpts_AOTwasmtime.wasm"

wasmtime compile "_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts.wasm" -o "_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts_AOTwasmtime.wasm"
wasmtime compile "_WASM_BINARIES/cpuIntensive/primeNums/primeNums_wOpts.wasm" -o "_WASM_BINARIES/cpuIntensive/primeNums/primeNums_wOpts_AOTwasmtime.wasm"
wasmtime compile "_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_wOpts.wasm" -o "_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_wOpts_AOTwasmtime.wasm"
wasmtime compile "_WASM_BINARIES/lightweight/lightweight_wOpts.wasm" -o "_WASM_BINARIES/lightweight/lightweight_wOpts_AOTwasmtime.wasm"
wasmtime compile "_WASM_BINARIES/stateful/statefulFunction_wOpts.wasm" -o "_WASM_BINARIES/stateful/statefulFunction_wOpts_AOTwasmtime.wasm"

echo -e "\n${GREEN}All AOT builds completed successfully.${NC}"