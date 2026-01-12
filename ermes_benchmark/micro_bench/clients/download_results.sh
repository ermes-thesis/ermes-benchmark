NODE2_IP="10.10.101.59"
REMOTE_PATH="micro_test/results"

echo "📥 Scaricamento dei risultati..."

# 1. Crea una cartella locale univoca con data e ora
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "   -> Timestamp: ${TIMESTAMP}"
RESULTS_DIR="./results/$TIMESTAMP"
mkdir -p "${RESULTS_DIR}"

ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} \
"cd ${REMOTE_PATH} && find . -name 'aggregated*.csv' -o -name 'final_global_summary.csv' | tar -cf - -T -" \
| tar -xf - -C "${RESULTS_DIR}"