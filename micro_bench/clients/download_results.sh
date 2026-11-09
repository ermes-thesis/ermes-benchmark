# Cluster parameters (override via environment):
#   ERMES_SUBNET    first three octets of the cluster subnet (default: 10.10.101)
#   ERMES_JUMP_HOST optional SSH bastion; leave empty for direct connections
#   ERMES_SSH_USER  SSH user on the cluster machines (default: ubuntu)
SUBNET="${ERMES_SUBNET:-10.10.101}"
SSH_USER="${ERMES_SSH_USER:-ubuntu}"
JUMP="${ERMES_JUMP_HOST:+-J ${ERMES_SSH_USER:-ubuntu}@${ERMES_JUMP_HOST}}"

NODE2_IP="${SUBNET}.79"
REMOTE_PATH="micro_test/results"

echo "📥 Downloading results..."

# Create a unique local folder named after the current date and time
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "   -> Timestamp: ${TIMESTAMP}"
RESULTS_DIR="./results/$TIMESTAMP"
mkdir -p "${RESULTS_DIR}"

ssh $JUMP ${SSH_USER}@${NODE2_IP} \
"cd ${REMOTE_PATH} && find . -name 'aggregated*.csv' -o -name 'final_*.csv' | tar -cf - -T -" \
| tar -xf - -C "${RESULTS_DIR}"
