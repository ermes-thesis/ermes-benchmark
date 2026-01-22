WASM_SOURCES=(
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
    ermes-cli compile "${VALID_SOURCES[@]}" -dw -i 100.112.91.33 -p 8080
else
    echo -e "${YELLOW}No valid WASM source files found to compile.${NC}"
fi

# Clean up intermediate files
echo "Cleaning up intermediate files..."
for src_file in "${VALID_SOURCES[@]}"; do
    base_name=$(basename "$src_file" .go)
    rm -r "${base_name}"
done