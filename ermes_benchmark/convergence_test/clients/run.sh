#!/bin/bash

# --- CONFIGURAZIONE ---
NODE1_IP="10.10.101.60"
NODE2_IP="10.10.101.59"

REMOTE_PATH="convergence_test"

ERMES_DEPLOY_PATH="../../../../ermes-deploy"

# --- 1. COMPILAZIONE (Cross-Compilation) ---
echo "🚧 [1/5] Compilazione per Linux/AMD64..."

env GOOS=linux GOARCH=amd64 go build -C read -ldflags="-s -w" -o ../bin/read .
env GOOS=linux GOARCH=amd64 go build -C write -ldflags="-s -w" -o ../bin/write .

if [ $? -ne 0 ]; then
    echo "❌ Errore durante la compilazione. Mi fermo."
    exit 1
fi
echo "✅ Compilazione completata."

# --- 2. COPIA DEI BINARI (SCP) ---
echo "🚀 [2/5] Copia dei binari sulle VM..."

# Uccidiamo eventuali vecchi processi rimasti appesi (pulizia)
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE1_IP} "sudo pkill -f read || true"
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "sudo pkill -f write || true"

ssh -J ubuntu@100.112.91.33 ubuntu@${NODE1_IP} "mkdir -p ${REMOTE_PATH}"
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "mkdir -p ${REMOTE_PATH}"

ssh -J ubuntu@100.112.91.33 ubuntu@${NODE1_IP} "cd ${REMOTE_PATH}; rm read.log *.csv"
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "cd ${REMOTE_PATH}; rm write.log *.csv"

scp -J ubuntu@100.112.91.33 -q bin/read ubuntu@${NODE1_IP}:${REMOTE_PATH}
scp -J ubuntu@100.112.91.33 -q config.yaml ubuntu@${NODE1_IP}:${REMOTE_PATH}

scp -J ubuntu@100.112.91.33 -q bin/write ubuntu@${NODE2_IP}:${REMOTE_PATH}
scp -J ubuntu@100.112.91.33 -q config.yaml ubuntu@${NODE2_IP}:${REMOTE_PATH}

echo "✅ Upload completato."

echo "🧹 [3/5] Pulisco Ermes"
ANSIBLE_CONFIG=${ERMES_DEPLOY_PATH}/ansible.cfg ansible-playbook ${ERMES_DEPLOY_PATH}/flush-ermes-nodes.yml
echo "✅ Pulizia completata."

# --- 4. ESECUZIONE (SSH) ---
echo "⚡ [4/5] Avvio dei processi..."

# Avvio Nodo 1
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE1_IP} "cd ${REMOTE_PATH}; ./read > read.log 2>&1" &
PID_READ=$!
echo "   -> Server avviato su ${NODE1_IP} (PID locale ssh: $PID_READ)"

# Avvio Nodo 2
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "cd ${REMOTE_PATH}; ./write > write.log 2>&1" &
PID_WRITE=$!
echo "   -> Client avviato su ${NODE2_IP} (PID locale ssh: $PID_WRITE)"

echo "⏳ Test in corso... (Premi Ctrl+C per interrompere)"

wait $PID_READ
wait $PID_WRITE
echo "✅ Il test è terminato."

# --- 5. DOWNLOAD RISULTATI ---
echo "📥 [5/5] Scaricamento dei risultati..."

# 1. Crea una cartella locale univoca con data e ora
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="./results/$TIMESTAMP"
mkdir -p "${RESULTS_DIR}"

echo "   -> Cartella destinazione: ${RESULTS_DIR}"

# 2. Scarica il log dal Nodo 1 (Read)
scp -J ubuntu@100.112.91.33 -q ubuntu@${NODE1_IP}:${REMOTE_PATH}/read.log "${RESULTS_DIR}/"
scp -J ubuntu@100.112.91.33 -q ubuntu@${NODE1_IP}:${REMOTE_PATH}/*.csv "${RESULTS_DIR}/"

# 3. Scarica il log dal Nodo 2 (Write)
scp -J ubuntu@100.112.91.33 -q ubuntu@${NODE2_IP}:${REMOTE_PATH}/write.log "${RESULTS_DIR}/"
scp -J ubuntu@100.112.91.33 -q ubuntu@${NODE2_IP}:${REMOTE_PATH}/*.csv "${RESULTS_DIR}/"

# Controllo finale
if [ -f "${RESULTS_DIR}/read.log" ] && [ -f "${RESULTS_DIR}/write.log" ]; then
    echo "✅ Risultati scaricati con successo in ${RESULTS_DIR}"
else
    echo "⚠️  Attenzione: uno o più risultati non sono stati scaricati."
fi

$ERMES_DEPLOY_PATH/scripts/download_logs.sh