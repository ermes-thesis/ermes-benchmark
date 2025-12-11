VALUES=("1" "10")
SEEDS=("42" "123")

NODE2_IP="10.10.101.59"
REMOTE_PATH="micro_test"

scp -J ubuntu@100.112.91.33 -q bin/{user,create} config.yaml ../csv_aggregator.py ../test_generator.py run_experiment.sh ubuntu@${NODE2_IP}:${REMOTE_PATH}
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "mkdir -p ${REMOTE_PATH}; cd ${REMOTE_PATH}; rm *.log *.csv 2>/dev/null"

for SEED in "${SEEDS[@]}"; do
  for USERS in "${VALUES[@]}"; do
    for COLLECTIONS in "${VALUES[@]}"; do
        echo "=============================="
        echo "🚀 Avvio test con ${USERS} utenti, ${COLLECTIONS} collections, seed=${SEED}"
        echo "=============================="

        ./run.sh $USERS $COLLECTIONS $SEED

        echo "=============================="
        echo "✅ Test completato per ${USERS} utenti, ${COLLECTIONS} collections, seed=${SEED}"
        echo "=============================="
    done
  done
done

echo "📥Scaricamento dei risultati..."

# 1. Crea una cartella locale univoca con data e ora
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "   -> Timestamp: ${TIMESTAMP}"
RESULTS_DIR="./results/$TIMESTAMP"
mkdir -p "${RESULTS_DIR}"

scp -J ubuntu@100.112.91.33 -q ubuntu@${NODE2_IP}:${REMOTE_PATH}/aggregated*.csv "${RESULTS_DIR}/"
