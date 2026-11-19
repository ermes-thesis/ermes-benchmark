#!/bin/bash
# Conflicting updates: two read-write clients on the same collection through
# two different nodes. Replaces run_conflict_1.sh and run_conflict_eventual.sh.
# Usage: ./run_conflict.sh [sequential|eventual]
# (the consistency can also be given through ERMES_CONSISTENCY).
#   sequential -> data/conflict_1/conflict_1_<timestamp>.zip
#   eventual   -> data/conflict_eventual/conflict_eventual_<timestamp>.zip

source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"

CONSISTENCY="${1:-${ERMES_CONSISTENCY:-sequential}}"
case "${CONSISTENCY}" in
    sequential) EXPERIMENT="conflict_1" ;;
    eventual)   EXPERIMENT="conflict_eventual" ;;
    *) echo "Unknown consistency '${CONSISTENCY}' (use sequential or eventual)." >&2; exit 1 ;;
esac

# --- CONFIGURATION ---
CLIENT_A_IP="${CLIENT2_IP}"   # read-write client 54321
CLIENT_B_IP="${CLIENT1_IP}"   # creates the collection, read-write client 12345

NODE_A="${NODE_POLIMI}"
NODE_B="${NODE_LASAPIENZA}"

REMOTE_PATH="${EXPERIMENT}"

# --- 1. BUILD (cross-compilation) ---
echo "🚧 [1/6] Building for Linux/AMD64..."
if ! build_clients read_write create; then
    echo "❌ Build failed. Stopping."
    exit 1
fi
echo "✅ Build completed."

# --- 2. UPLOAD (SCP) ---
echo "🚀 [2/6] Copying the binaries to the client VMs..."
kill_stale "${CLIENT_A_IP}" read-write
kill_stale "${CLIENT_B_IP}" create read-write
clean_remote "${CLIENT_A_IP}" "${CLIENT_B_IP}"
render_client_config
upload "${CLIENT_A_IP}" read-write
upload "${CLIENT_B_IP}" read-write create
echo "✅ Upload completed."

echo "🧹 [3/6] Flushing Ermes"
flush_ermes
echo "✅ Flush completed."

# --- 4. RUN (SSH) ---
echo "⚡ [4/6] Starting the processes (${CONSISTENCY})..."

vm_ssh "${CLIENT_B_IP}" \
    "cd ${REMOTE_PATH}; ./create ${NODE_B} ${COLLECTION_NAME} 0 IT/Rome/LaSapienza ${CONSISTENCY} > create.log 2>&1"
echo "   -> Collection created on ${CLIENT_B_IP}"

vm_ssh "${CLIENT_A_IP}" \
    "cd ${REMOTE_PATH}; ./read-write ${NODE_A} 54321 IT ${COLLECTION_NAME} > read-write_54321.log 2>&1" &
PID_A=$!
echo "   -> Client 54321 started on ${CLIENT_A_IP} (local ssh PID: ${PID_A})"

vm_ssh "${CLIENT_B_IP}" \
    "cd ${REMOTE_PATH}; ./read-write ${NODE_B} 12345 IT/Rome/LaSapienza ${COLLECTION_NAME} > read-write_12345.log 2>&1" &
PID_B=$!
echo "   -> Client 12345 started on ${CLIENT_B_IP} (local ssh PID: ${PID_B})"

echo "⏳ Test running... (press Ctrl+C to stop)"
wait "${PID_A}"
wait "${PID_B}"
echo "✅ Test finished."

# --- 5. DOWNLOAD RESULTS ---
echo "📥 [5/6] Downloading the results..."
download_results "${CLIENT_A_IP}" "${CLIENT_B_IP}"

# --- 6. ZIP ARCHIVE ---
echo "📦 [6/6] Creating the ZIP archive..."
archive_results "${EXPERIMENT}" "${EXPERIMENT}_${TIMESTAMP}.zip" \
    "${RESULTS_DIR}"/results_log_12345_*.csv \
    "${RESULTS_DIR}"/results_log_54321_*.csv \
    logs/*/general_*.log
