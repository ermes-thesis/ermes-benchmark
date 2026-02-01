#!/bin/bash

# --- CONFIGURAZIONE ---
CLIENT1_IP="10.10.101.60"
CLIENT2_IP="10.10.101.59"

NODE1="10.10.101.54:12345"
NODE2="10.10.101.51:12345"

REMOTE_PATH="conflict_eventual"

ERMES_DEPLOY_PATH="../../../../ermes-deploy"

# --- 1. COMPILAZIONE (Cross-Compilation) ---
echo "🚧 [1/6] Compilazione per Linux/AMD64..."

env GOOS=linux GOARCH=amd64 go build -C read_write -ldflags="-s -w" -o ../bin/read-write .
env GOOS=linux GOARCH=amd64 go build -C create -ldflags="-s -w" -o ../bin/create .

if [ $? -ne 0 ]; then
    echo "❌ Errore durante la compilazione. Mi fermo."
    exit 1
fi
echo "✅ Compilazione completata."

# --- 2. COPIA DEI BINARI (SCP) ---
echo "🚀 [2/6] Copia dei binari sulle VM..."

# Uccidiamo eventuali vecchi processi rimasti appesi (pulizia)
ssh -J ubuntu@100.112.91.33 ubuntu@${CLIENT1_IP} "sudo pkill -f read-write || true"
ssh -J ubuntu@100.112.91.33 ubuntu@${CLIENT2_IP} "sudo pkill -f create || true"
ssh -J ubuntu@100.112.91.33 ubuntu@${CLIENT2_IP} "sudo pkill -f read-write || true"

ssh -J ubuntu@100.112.91.33 ubuntu@${CLIENT1_IP} "mkdir -p ${REMOTE_PATH}; cd ${REMOTE_PATH}; rm *.log *.csv"
ssh -J ubuntu@100.112.91.33 ubuntu@${CLIENT2_IP} "mkdir -p ${REMOTE_PATH}; cd ${REMOTE_PATH}; rm *.log *.csv"

scp -J ubuntu@100.112.91.33 -q bin/read-write config.yaml ubuntu@${CLIENT1_IP}:${REMOTE_PATH}
scp -J ubuntu@100.112.91.33 -q bin/{read-write,create} config.yaml ubuntu@${CLIENT2_IP}:${REMOTE_PATH}

echo "✅ Upload completato."

echo "🧹 [3/6] Pulisco Ermes"
ANSIBLE_CONFIG=${ERMES_DEPLOY_PATH}/ansible.cfg ansible-playbook ${ERMES_DEPLOY_PATH}/flush-ermes-nodes.yml
echo "✅ Pulizia completata."

# --- 4. ESECUZIONE (SSH) ---
echo "⚡ [4/6] Avvio dei processi..."

# Avvio Nodo 1
ssh -J ubuntu@100.112.91.33 ubuntu@${CLIENT2_IP} "cd ${REMOTE_PATH}; ./create $NODE2 colName 0 IT/Rome/LaSapienza eventual > create.log 2>&1"
echo "   -> Collection creata su ${CLIENT2_IP}"

ssh -J ubuntu@100.112.91.33 ubuntu@${CLIENT1_IP} "cd ${REMOTE_PATH}; ./read-write $NODE1 54321 IT colName> read-write_54321.log 2>&1" &
PID_NODE1=$!
echo "   -> Client 1 avviato su ${CLIENT1_IP} (PID locale ssh: $PID_NODE1)"

# Avvio Nodo 2
ssh -J ubuntu@100.112.91.33 ubuntu@${CLIENT2_IP} "cd ${REMOTE_PATH}; ./read-write $NODE2 12345 IT/Rome/LaSapienza colName> read-write_12345.log 2>&1" &
PID_NODE2=$!
echo "   -> Client 2 avviato su ${CLIENT2_IP} (PID locale ssh: $PID_NODE2)"

echo "⏳ Test in corso... (Premi Ctrl+C per interrompere)"

wait $PID_NODE1
wait $PID_NODE2
echo "✅ Il test è terminato."

# --- 5. DOWNLOAD RISULTATI ---
echo "📥 [5/6] Scaricamento dei risultati..."

# 1. Crea una cartella locale univoca con data e ora
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "   -> Timestamp: ${TIMESTAMP}"
RESULTS_DIR="./results/$TIMESTAMP"
mkdir -p "${RESULTS_DIR}"

echo "   -> Cartella destinazione: ${RESULTS_DIR}"

# 2. Scarica il log dal Nodo 1 (Read)
scp -J ubuntu@100.112.91.33 -q ubuntu@${CLIENT1_IP}:${REMOTE_PATH}/*.log "${RESULTS_DIR}/"
scp -J ubuntu@100.112.91.33 -q ubuntu@${CLIENT1_IP}:${REMOTE_PATH}/*.csv "${RESULTS_DIR}/"

# 3. Scarica il log dal Nodo 2 (Write)
scp -J ubuntu@100.112.91.33 -q ubuntu@${CLIENT2_IP}:${REMOTE_PATH}/*.log "${RESULTS_DIR}/"
scp -J ubuntu@100.112.91.33 -q ubuntu@${CLIENT2_IP}:${REMOTE_PATH}/*.csv "${RESULTS_DIR}/"

echo "📥 Scaricamento logs infrastruttura..."
$ERMES_DEPLOY_PATH/scripts/download_logs.sh

# --- 6. CREAZIONE ZIP ---
echo "📦 [6/6] Creazione archivio ZIP..."

ZIP_FILENAME="conflict_eventual_${TIMESTAMP}.zip"

if command -v zip >/dev/null 2>&1; then
    mkdir -p ../data/conflict_eventual
    zip -q -j ../data/conflict_eventual/"${ZIP_FILENAME}" "${RESULTS_DIR}"/results_log_12345_*.csv "${RESULTS_DIR}"/results_log_54321_*.csv logs/*/general_*.log

    if [ $? -eq 0 ]; then
        echo "✅ Archivio creato correttamente: ${ZIP_FILENAME}"
    else
        echo "❌ Errore durante la creazione dello zip."
    fi
else
    echo "⚠️  Comando 'zip' non trovato. Impossibile comprimere i file."
fi
