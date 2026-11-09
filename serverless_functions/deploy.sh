#!/usr/bin/env bash
# Function Registry endpoint reachable from this machine (override via env).
# Behind a bastion, tunnel it and keep 127.0.0.1 (see the top-level README).
FR_HOST="${ERMES_FR_HOST:-127.0.0.1}"
FR_PORT="${ERMES_FR_PORT:-8080}"

WASM_SOURCES=(
    "auth_function.go"
    "functionCreateCollection.go"
    "functionReadCollection.go"
    "functionReadTwoCollections.go"
    "functionWriteCollection.go"
    "functionWriteTwoCollections.go"
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
    echo "Compiling and deploying ${#VALID_SOURCES[@]} WASM functions..."
    ermes-cli compile "${VALID_SOURCES[@]}" -dw -i "$FR_HOST" -p "$FR_PORT"
else
    echo -e "${YELLOW}No valid WASM source files found to compile.${NC}"
fi

# Clean up intermediate files
echo "Cleaning up intermediate files..."
for src_file in "${VALID_SOURCES[@]}"; do
    base_name=$(basename "$src_file" .go)
    rm -r "${base_name}"
done