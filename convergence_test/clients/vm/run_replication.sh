#!/bin/bash
# State replication: one writer and four concurrent readers on different edges.
# Usage: ./run_replication.sh

source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"

# --- CONFIGURATION ---
WRITER_CLIENT_IP="${CLIENT2_IP}"   # creates the collection and writes
READER_CLIENT_IP="${CLIENT1_IP}"   # hosts the four readers

WRITE_NODE="${NODE_POLIMI}"

# TARGET_NODE;READ_ID
READ_NODES=(
    "${NODE_TORVERGATA};11"
    "${NODE_LASAPIENZA};12"
    "${NODE_BOCCONI};13"
    "${NODE_UNIMI};14"
)

REMOTE_PATH="replication"

# --- 1. BUILD (cross-compilation) ---
echo "🚧 [1/6] Building for Linux/AMD64..."
if ! build_clients read write create; then
    echo "❌ Build failed. Stopping."
    exit 1
fi
echo "✅ Build completed."

# --- 2. UPLOAD (SCP) ---
echo "🚀 [2/6] Copying the binaries to the client VMs..."
kill_stale "${READER_CLIENT_IP}" read
kill_stale "${WRITER_CLIENT_IP}" create write
clean_remote "${WRITER_CLIENT_IP}" "${READER_CLIENT_IP}"
render_client_config
upload "${WRITER_CLIENT_IP}" write create
upload "${READER_CLIENT_IP}" read
echo "✅ Upload completed."

echo "🧹 [3/6] Flushing Ermes"
flush_ermes
echo "✅ Flush completed."

# --- 4. RUN (SSH) ---
echo "⚡ [4/6] Starting the processes..."

vm_ssh "${WRITER_CLIENT_IP}" \
    "cd ${REMOTE_PATH}; ./create ${WRITE_NODE} ${COLLECTION_NAME} 0 IT > create.log 2>&1"
echo "   -> Collection created on target: ${WRITE_NODE}"

vm_ssh "${WRITER_CLIENT_IP}" \
    "cd ${REMOTE_PATH}; ./write ${WRITE_NODE} ${COLLECTION_NAME} 54321 IT > write.log 2>&1" &
PID_WRITE=$!
echo "   -> Writer started on ${WRITER_CLIENT_IP} (local ssh PID: ${PID_WRITE})"

READ_PIDS=()
echo "   -> Starting the readers in parallel..."
for TARGET_NODE in "${READ_NODES[@]}"; do
    IFS=';' read -r target read_id <<< "${TARGET_NODE}"
    vm_ssh "${READER_CLIENT_IP}" \
        "cd ${REMOTE_PATH}; ./read ${target} ${read_id} IT ${COLLECTION_NAME} > read_${read_id}.log 2>&1" &
    READ_PIDS+=($!)
    echo "      Reader started towards ${target} (PID: $!)"
done

echo "⏳ Test running... (press Ctrl+C to stop)"
wait "${PID_WRITE}"
for PID in "${READ_PIDS[@]}"; do
    wait "${PID}"
done
echo "✅ Test finished."

# --- 5. DOWNLOAD RESULTS ---
echo "📥 [5/6] Downloading the results..."
download_results "${WRITER_CLIENT_IP}" "${READER_CLIENT_IP}"

# --- 6. ZIP ARCHIVE ---
echo "📦 [6/6] Creating the ZIP archive..."
archive_results "replication" "replication_${TIMESTAMP}.zip" \
    "${RESULTS_DIR}"/results_log_54321_*.csv \
    "${RESULTS_DIR}"/results_log_1*.csv \
    logs/*/general_*.log
