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
CLIENT1_IP="${SUBNET}.80"
CLIENT2_IP="${SUBNET}.79"

NODE1="${SUBNET}.74:12345"
NODE2="${SUBNET}.71:12345"

REMOTE_PATH="conflict_eventual"

ERMES_DEPLOY_PATH="../../../ermes-deploy"

# --- 1. BUILD (cross-compilation) ---
echo "🚧 [1/6] Building for Linux/AMD64..."

env GOOS=linux GOARCH=amd64 go build -C read_write -ldflags="-s -w" -o ../bin/read-write .
env GOOS=linux GOARCH=amd64 go build -C create -ldflags="-s -w" -o ../bin/create .

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Stopping."
    exit 1
fi
echo "✅ Build completed."

# --- 2. UPLOAD (SCP) ---
echo "🚀 [2/6] Copying the binaries to the client VMs..."

# Kill any stale client process
ssh $JUMP ${SSH_USER}@${CLIENT1_IP} "sudo pkill -f read-write || true"
ssh $JUMP ${SSH_USER}@${CLIENT2_IP} "sudo pkill -f create || true"
ssh $JUMP ${SSH_USER}@${CLIENT2_IP} "sudo pkill -f read-write || true"

ssh $JUMP ${SSH_USER}@${CLIENT1_IP} "mkdir -p ${REMOTE_PATH}; cd ${REMOTE_PATH}; rm *.log *.csv"
ssh $JUMP ${SSH_USER}@${CLIENT2_IP} "mkdir -p ${REMOTE_PATH}; cd ${REMOTE_PATH}; rm *.log *.csv"

# Point the client config's GTP address at the central node of the chosen subnet
CFG_TMP="$(mktemp)"; trap 'rm -f "$CFG_TMP"' EXIT
sed -E "s#[0-9]+\.[0-9]+\.[0-9]+(\.78:8081)#${SUBNET}\1#" config.yaml > "$CFG_TMP"
scp $JUMP -q bin/read-write ${SSH_USER}@${CLIENT1_IP}:${REMOTE_PATH}
scp $JUMP -q "$CFG_TMP" ${SSH_USER}@${CLIENT1_IP}:${REMOTE_PATH}/config.yaml
scp $JUMP -q bin/{read-write,create} ${SSH_USER}@${CLIENT2_IP}:${REMOTE_PATH}
scp $JUMP -q "$CFG_TMP" ${SSH_USER}@${CLIENT2_IP}:${REMOTE_PATH}/config.yaml

echo "✅ Upload completed."

echo "🧹 [3/6] Flushing Ermes"
ANSIBLE_CONFIG=${ERMES_DEPLOY_PATH}/ansible.cfg ansible-playbook ${ERMES_DEPLOY_PATH}/flush-ermes-nodes.yml
echo "✅ Flush completed."

# --- 4. RUN (SSH) ---
echo "⚡ [4/6] Starting the processes..."

# Client 1
ssh $JUMP ${SSH_USER}@${CLIENT2_IP} "cd ${REMOTE_PATH}; ./create $NODE2 colName 0 IT/Rome/LaSapienza eventual > create.log 2>&1"
echo "   -> Collection created on ${CLIENT2_IP}"

ssh $JUMP ${SSH_USER}@${CLIENT1_IP} "cd ${REMOTE_PATH}; ./read-write $NODE1 54321 IT colName> read-write_54321.log 2>&1" &
PID_NODE1=$!
echo "   -> Client 1 started on ${CLIENT1_IP} (local ssh PID: $PID_NODE1)"

# Client 2
ssh $JUMP ${SSH_USER}@${CLIENT2_IP} "cd ${REMOTE_PATH}; ./read-write $NODE2 12345 IT/Rome/LaSapienza colName> read-write_12345.log 2>&1" &
PID_NODE2=$!
echo "   -> Client 2 started on ${CLIENT2_IP} (local ssh PID: $PID_NODE2)"

echo "⏳ Test running... (press Ctrl+C to stop)"

wait $PID_NODE1
wait $PID_NODE2
echo "✅ Test finished."

# --- 5. DOWNLOAD RESULTS ---
echo "📥 [5/6] Downloading the results..."

# Create a unique local folder named after the current date and time
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "   -> Timestamp: ${TIMESTAMP}"
RESULTS_DIR="./results/$TIMESTAMP"
mkdir -p "${RESULTS_DIR}"

echo "   -> Destination folder: ${RESULTS_DIR}"

# Client 1 logs and CSVs
scp $JUMP -q ${SSH_USER}@${CLIENT1_IP}:${REMOTE_PATH}/*.log "${RESULTS_DIR}/"
scp $JUMP -q ${SSH_USER}@${CLIENT1_IP}:${REMOTE_PATH}/*.csv "${RESULTS_DIR}/"

# Client 2 logs and CSVs
scp $JUMP -q ${SSH_USER}@${CLIENT2_IP}:${REMOTE_PATH}/*.log "${RESULTS_DIR}/"
scp $JUMP -q ${SSH_USER}@${CLIENT2_IP}:${REMOTE_PATH}/*.csv "${RESULTS_DIR}/"

echo "📥 Downloading the infrastructure logs..."
$ERMES_DEPLOY_PATH/scripts/download_logs.sh

# --- 6. ZIP ARCHIVE ---
echo "📦 [6/6] Creating the ZIP archive..."

ZIP_FILENAME="conflict_eventual_${TIMESTAMP}.zip"

if command -v zip >/dev/null 2>&1; then
    mkdir -p ../data/conflict_eventual
    zip -q -j ../data/conflict_eventual/"${ZIP_FILENAME}" "${RESULTS_DIR}"/results_log_12345_*.csv "${RESULTS_DIR}"/results_log_54321_*.csv logs/*/general_*.log

    if [ $? -eq 0 ]; then
        echo "✅ Archive created: ${ZIP_FILENAME}"
    else
        echo "❌ Error while creating the zip."
    fi
else
    echo "⚠️  'zip' command not found. Cannot compress the files."
fi
