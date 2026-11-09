#!/bin/bash

# Cluster parameters (override via environment):
#   ERMES_SUBNET    first three octets of the cluster subnet (default: 10.10.101)
#   ERMES_JUMP_HOST optional SSH bastion; leave empty for direct connections
#   ERMES_SSH_USER  SSH user on the cluster machines (default: ubuntu)
SUBNET="${ERMES_SUBNET:-10.10.101}"
SSH_USER="${ERMES_SSH_USER:-ubuntu}"
JUMP="${ERMES_JUMP_HOST:+-J ${ERMES_SSH_USER:-ubuntu}@${ERMES_JUMP_HOST}}"

# --- TARGET CONFIGURATION (same nodes as run.sh) ---
ERMES_NODES=(); for o in 70 71 72 73 74 75 76 77 78; do ERMES_NODES+=("${SUBNET}.${o}"); done

clean_remote_experiments() {
    echo "🧹 [Global clean] Removing '/home/ubuntu/experiments_*' folders on the remote nodes..."

    for NODE_IP in "${ERMES_NODES[@]}"; do
        # 'sudo bash -s' is needed because the copied logs are often root-owned
        ssh $JUMP -o StrictHostKeyChecking=no ${SSH_USER}@${NODE_IP} "sudo bash -s" << 'EOF'

        TARGET_PATTERN="/home/ubuntu/experiments_*"

        if ls $TARGET_PATTERN 1> /dev/null 2>&1; then
            rm -rf $TARGET_PATTERN
            echo "      🗑️  Experiment folders removed."
        else
            echo "      ℹ️  No experiment folder found."
        fi
EOF
        echo "   ✅ ${NODE_IP} done."
    done
}

clean_remote_experiments
echo "🎉 Cleanup completed on all nodes."
