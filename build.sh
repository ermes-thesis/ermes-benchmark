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

if [ -f "native/fibonacci/main.go" ]; then
    echo "Building native/fibonacci..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/native_fibonacci native/fibonacci/main.go
fi

if [ -f "native/fibonacciTail/main.go" ]; then
    echo "Building native/fibonacciTail..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/native_tailFibonacci native/fibonacciTail/main.go
fi

if [ -f "native/lightweight/main.go" ]; then
    echo "Building native/lightweight..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/native_lightweight native/lightweight/main.go
fi

if [ -f "native/primeNums/main.go" ]; then
    echo "Building native/primeNums..."
    go build "${BUILD_FLAGS[@]}" -o "${OUTPUT_BUILD_DIR}"/native_primeNums native/primeNums/main.go
fi


