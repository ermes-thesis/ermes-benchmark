NODE2_IP="10.10.101.59"
REMOTE_PATH="micro_test"

echo "📥 Scaricamento dei risultati..."

# 1. Crea una cartella locale univoca con data e ora
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "   -> Timestamp: ${TIMESTAMP}"
RESULTS_DIR="./results/$TIMESTAMP"
mkdir -p "${RESULTS_DIR}"

scp -J ubuntu@100.112.91.33 -q ubuntu@${NODE2_IP}:${REMOTE_PATH}/aggregated*.csv "${RESULTS_DIR}/"
