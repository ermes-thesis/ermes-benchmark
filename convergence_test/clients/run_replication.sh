#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "${SCRIPT_DIR}"

# Cluster parameters (override via environment):
#   ERMES_SUBNET    first three octets of the cluster subnet (default: 10.10.101)
#   ERMES_JUMP_HOST optional SSH bastion; leave empty for direct connections
#   ERMES_SSH_USER  SSH user on the cluster machines (default: ubuntu)
SUBNET="${ERMES_SUBNET:-10.10.101}"
SSH_USER="${ERMES_SSH_USER:-ubuntu}"
JUMP="${ERMES_JUMP_HOST:+-J ${ERMES_SSH_USER:-ubuntu}@${ERMES_JUMP_HOST}}"

# --- CONFIGURATION ---
NODE1_IP="${SUBNET}.80"
NODE2_IP="${SUBNET}.79"

# TARGET_NODE;READ_ID
READ_NODES=(
    "${SUBNET}.70:12345;11"
    "${SUBNET}.71:12345;12"
    "${SUBNET}.72:12345;13"
    "${SUBNET}.73:12345;14"
)

WRITE_NODE="${SUBNET}.74:12345"

REMOTE_PATH="replication"
ERMES_DEPLOY_PATH="../../../ermes-deploy"

# --- 1. BUILD (cross-compilation) ---
echo "🚧 [1/6] Building for Linux/AMD64..."

env GOOS=linux GOARCH=amd64 go build -C read -ldflags="-s -w" -o ../bin/read .
env GOOS=linux GOARCH=amd64 go build -C write -ldflags="-s -w" -o ../bin/write .
env GOOS=linux GOARCH=amd64 go build -C create -ldflags="-s -w" -o ../bin/create .

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Stopping."
    exit 1
fi
echo "✅ Build completed."

# --- 2. UPLOAD (SCP) ---
echo "🚀 [2/6] Copying the binaries to the client VMs..."

# Kill any stale client process
ssh $JUMP ${SSH_USER}@${NODE2_IP} "sudo pkill -f read || true"
ssh $JUMP ${SSH_USER}@${NODE1_IP} "sudo pkill -f create || true"
ssh $JUMP ${SSH_USER}@${NODE1_IP} "sudo pkill -f write || true"

# Clean the remote folders
ssh $JUMP ${SSH_USER}@${NODE1_IP} "mkdir -p ${REMOTE_PATH}; cd ${REMOTE_PATH}; rm *.log *.csv"
ssh $JUMP ${SSH_USER}@${NODE2_IP} "mkdir -p ${REMOTE_PATH}; cd ${REMOTE_PATH}; rm *.log *.csv"

# Upload the files
# Point the client config's GTP address at the central node of the chosen subnet
CFG_TMP="$(mktemp)"; trap 'rm -f "$CFG_TMP"' EXIT
sed -E "s#[0-9]+\.[0-9]+\.[0-9]+(\.78:8081)#${SUBNET}\1#" config.yaml > "$CFG_TMP"
scp $JUMP -q bin/{write,create} ${SSH_USER}@${NODE1_IP}:${REMOTE_PATH}
scp $JUMP -q "$CFG_TMP" ${SSH_USER}@${NODE1_IP}:${REMOTE_PATH}/config.yaml
scp $JUMP -q bin/read ${SSH_USER}@${NODE2_IP}:${REMOTE_PATH}
scp $JUMP -q "$CFG_TMP" ${SSH_USER}@${NODE2_IP}:${REMOTE_PATH}/config.yaml

echo "✅ Upload completed."

echo "🧹 [3/6] Flushing Ermes"
ANSIBLE_CONFIG=${ERMES_DEPLOY_PATH}/ansible.cfg ansible-playbook ${ERMES_DEPLOY_PATH}/flush-ermes-nodes.yml
echo "✅ Flush completed."

# --- 4. RUN (SSH) ---
echo "⚡ [4/6] Starting the processes..."

# 4a. Create the collection
ssh $JUMP ${SSH_USER}@${NODE1_IP} \
    "cd ${REMOTE_PATH}; ./create $WRITE_NODE colName 0 IT > create.log 2>&1"

echo "   -> Collection created on target: ${WRITE_NODE}"

# 4b. Start the writer
ssh $JUMP ${SSH_USER}@${NODE1_IP} "cd ${REMOTE_PATH}; ./write $WRITE_NODE colName 54321 IT > write.log 2>&1" &
PID_WRITE=$!
echo "   -> Writer started on ${NODE1_IP} (local ssh PID: $PID_WRITE)"

# 4c. Start the readers (parallel loop)
READ_PIDS=()
echo "   -> Starting the readers in parallel..."

for TARGET_NODE in "${READ_NODES[@]}"; do
    IFS=';' read -r target read_id <<< "$TARGET_NODE"

    ssh $JUMP ${SSH_USER}@${NODE2_IP} \
        "cd ${REMOTE_PATH}; ./read $target $read_id IT colName > read_$read_id.log 2>&1" &

    CURRENT_PID=$!
    READ_PIDS+=($CURRENT_PID)
    echo "      Reader started towards ${target} (PID: $CURRENT_PID)"
done

echo "⏳ Test running... (press Ctrl+C to stop)"

# Wait for the writer
wait $PID_WRITE

# Wait for all the readers
for PID in "${READ_PIDS[@]}"; do
    wait $PID
done

echo "✅ Test finished."

# --- 5. DOWNLOAD RESULTS ---
echo "📥 [5/6] Downloading the results..."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="./results/$TIMESTAMP"
mkdir -p "${RESULTS_DIR}"
echo "   -> Destination folder: ${RESULTS_DIR}"

# Client logs and CSVs
scp $JUMP -q ${SSH_USER}@${NODE1_IP}:${REMOTE_PATH}/*.log "${RESULTS_DIR}/"
scp $JUMP -q ${SSH_USER}@${NODE1_IP}:${REMOTE_PATH}/*.csv "${RESULTS_DIR}/"
scp $JUMP -q ${SSH_USER}@${NODE2_IP}:${REMOTE_PATH}/*.log "${RESULTS_DIR}/"
scp $JUMP -q ${SSH_USER}@${NODE2_IP}:${REMOTE_PATH}/*.csv "${RESULTS_DIR}/"

echo "📥 Downloading the infrastructure logs..."
$ERMES_DEPLOY_PATH/scripts/download_logs.sh

# --- 6. ZIP ARCHIVE ---
echo "📦 [6/6] Creating the ZIP archive..."

ZIP_FILENAME="replication_${TIMESTAMP}.zip"

if command -v zip >/dev/null 2>&1; then
    mkdir -p ../data/replication

    zip -q -j ../data/replication/"${ZIP_FILENAME}" \
        "${RESULTS_DIR}"/results_log_54321_*.csv \
        "${RESULTS_DIR}"/results_log_1*.csv \
        logs/*/general_*.log

    if [ $? -eq 0 ]; then
        echo "✅ Archive created: ${ZIP_FILENAME}"
    else
        echo "❌ Error while creating the zip."
    fi
else
    echo "⚠️  'zip' command not found. Cannot compress the files."
fi
