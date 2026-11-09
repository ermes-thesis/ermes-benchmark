#!/bin/bash

# Cluster parameters (override via environment):
#   ERMES_SUBNET    first three octets of the cluster subnet (default: 10.10.101)
#   ERMES_JUMP_HOST optional SSH bastion; leave empty for direct connections
#   ERMES_SSH_USER  SSH user on the cluster machines (default: ubuntu)
SUBNET="${ERMES_SUBNET:-10.10.101}"
SSH_USER="${ERMES_SSH_USER:-ubuntu}"
JUMP="${ERMES_JUMP_HOST:+-J ${ERMES_SSH_USER:-ubuntu}@${ERMES_JUMP_HOST}}"

# $1 = mode (eventual/sequential/all)
# $2 = experiment type (scalability/density/moving) - optional, default: scalability
MODE=$1
EXP_TYPE=${2:-"scalability"}

if [[ "$MODE" != "eventual" && "$MODE" != "sequential" && "$MODE" != "all" ]]; then
    echo "❌ Error: specify the consistency mode."
    echo "   Usage: $0 [ eventual | sequential | all ] [ scalability | density | moving ]"
    exit 1
fi

echo "⚙️  Mode: $MODE | Experiment: $EXP_TYPE"

NODE2_IP="${SUBNET}.79"
REMOTE_PATH="micro_test"

# 1. Build the client binaries for the target machine
echo "🚧 Building Go clients..."
env GOOS=linux GOARCH=amd64 go build -C user -ldflags="-s -w" -o ../bin/user .
env GOOS=linux GOARCH=amd64 go build -C moving_user -ldflags="-s -w" -o ../bin/moving_user .
env GOOS=linux GOARCH=amd64 go build -C create -ldflags="-s -w" -o ../bin/create .

if [ $? -ne 0 ]; then
    echo "❌ Build failed."
    exit 1
fi

# 2. Upload binaries and scripts to the client machine
echo "🚀 Uploading files..."
# Point the client config's GTP address at the central node of the chosen subnet
CFG_TMP="$(mktemp)"; trap 'rm -f "$CFG_TMP"' EXIT
sed -E "s#[0-9]+\.[0-9]+\.[0-9]+(\.78:8081)#${SUBNET}\1#" config.yaml > "$CFG_TMP"
scp $JUMP -q \
    bin/{user,create,moving_user} \
    ../csv_aggregator.py \
    ../test_generator.py \
    run.sh \
    ${SSH_USER}@${NODE2_IP}:${REMOTE_PATH}
scp $JUMP -q "$CFG_TMP" ${SSH_USER}@${NODE2_IP}:${REMOTE_PATH}/config.yaml

# 3. Start the orchestrator inside a tmux session on the client machine
echo "⚡ Starting the orchestrator in tmux..."
ssh $JUMP ${SSH_USER}@${NODE2_IP} "
    tmux kill-session -t experiment 2>/dev/null;
    cd ${REMOTE_PATH};
    chmod +x *.sh;
    tmux new-session -d -s experiment 'ERMES_SUBNET=${SUBNET} ./run.sh $MODE $EXP_TYPE; echo \"Press Enter to close.\"; read'
"

echo "✅ Started! Monitor with: ssh $JUMP -t ${SSH_USER}@${NODE2_IP} 'tmux attach -t experiment'"
