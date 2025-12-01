#!/bin/bash

# --- CONFIGURAZIONE ---
NODE1_IP="10.10.101.60"
NODE2_IP="10.10.101.59"

# TARGET_NODE;CREATE_ID;WRITE_ID;GEOLOCATION
WRITE_NODES=(
    "10.10.101.50:12345;11;21;col_1;IT/Rome/TorVergata"
    "10.10.101.51:12345;12;22;col_2;IT/Rome/LaSapienza"
    "10.10.101.52:12345;13;23;col_3;IT/Milan/Bocconi"
    "10.10.101.53:12345;14;24;col_4;IT/Milan/UNIMI"
    "10.10.101.54:12345;15;25;col_5;IT/Milan/POLIMI"
)

READ_NODE="10.10.101.57:12345"

REMOTE_PATH="bottom_up"
ERMES_DEPLOY_PATH="../../../../ermes-deploy"

# --- 1. COMPILAZIONE (Cross-Compilation) ---
echo "🚧 [1/6] Compilazione per Linux/AMD64..."

env GOOS=linux GOARCH=amd64 go build -C read -ldflags="-s -w" -o ../bin/read .
env GOOS=linux GOARCH=amd64 go build -C write -ldflags="-s -w" -o ../bin/write .
env GOOS=linux GOARCH=amd64 go build -C create -ldflags="-s -w" -o ../bin/create .

if [ $? -ne 0 ]; then
    echo "❌ Errore durante la compilazione. Mi fermo."
    exit 1
fi
echo "✅ Compilazione completata."

# --- 2. COPIA DEI BINARI (SCP) ---
echo "🚀 [2/6] Copia dei binari sulle VM..."

# Uccidiamo eventuali vecchi processi rimasti appesi
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE1_IP} "sudo pkill -f read || true"
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "sudo pkill -f create || true"
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "sudo pkill -f write || true"

# Pulizia cartelle remote
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE1_IP} "mkdir -p ${REMOTE_PATH}; cd ${REMOTE_PATH}; rm *.log *.csv"
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "mkdir -p ${REMOTE_PATH}; cd ${REMOTE_PATH}; rm *.log *.csv"

# Upload file
scp -J ubuntu@100.112.91.33 -q bin/read config.yaml ubuntu@${NODE1_IP}:${REMOTE_PATH}
scp -J ubuntu@100.112.91.33 -q bin/{write,create} config.yaml ubuntu@${NODE2_IP}:${REMOTE_PATH}

echo "✅ Upload completato."

echo "🧹 [3/6] Pulisco Ermes"
ANSIBLE_CONFIG=${ERMES_DEPLOY_PATH}/ansible.cfg ansible-playbook ${ERMES_DEPLOY_PATH}/flush-ermes-nodes.yml
echo "✅ Pulizia completata."

# --- 4. ESECUZIONE (SSH) ---
echo "⚡ [4/6] Avvio dei processi..."

# 4a. Avvio Creazione (Loop sequenziale per sicurezza, o parallelo se preferisci)
echo "   -> Creazione collection sui nodi..."
for TARGET_NODE in "${WRITE_NODES[@]}"; do
    IFS=';' read -r target create_id _ colName geolocation <<< "$TARGET_NODE"

    ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} \
        "cd ${REMOTE_PATH}; ./create $target $colName $create_id $geolocation > create_$colName.log 2>&1"

    echo "      Collection creata su target: ${target}"
done

# 4b. Avvio Read (Singola istanza come prima)
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE1_IP} "cd ${REMOTE_PATH}; ./read $READ_NODE 54321 IT col_1 col_2 col_3 col_4 col_5 > read.log 2>&1" &
PID_READ=$!
echo "   -> Read avviato su ${NODE1_IP} (PID locale ssh: $PID_READ)"

# 4c. Avvio Write (Loop parallelo)
WRITE_PIDS=()
echo "   -> Avvio scritture in parallelo..."

for TARGET_NODE in "${WRITE_NODES[@]}"; do
    # Esegue write in background per ogni nodo target
    IFS=';' read -r target _ write_id colName geolocation <<< "$TARGET_NODE"

    ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} \
        "cd ${REMOTE_PATH}; ./write $target $colName $write_id $geolocation > write_$colName.log 2>&1" &

    CURRENT_PID=$!
    WRITE_PIDS+=($CURRENT_PID)
    echo "      Write avviato verso ${target} (PID: $CURRENT_PID)"
done

echo "⏳ Test in corso... (Premi Ctrl+C per interrompere)"

# Attesa READ
wait $PID_READ

# Attesa di tutti i processi WRITE
for PID in "${WRITE_PIDS[@]}"; do
    wait $PID
done

echo "✅ Il test è terminato."

# --- 5. DOWNLOAD RISULTATI ---
echo "📥 [5/6] Scaricamento dei risultati..."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="./results/$TIMESTAMP"
mkdir -p "${RESULTS_DIR}"
echo "   -> Cartella destinazione: ${RESULTS_DIR}"

# Scarica log Read
scp -J ubuntu@100.112.91.33 -q ubuntu@${NODE1_IP}:${REMOTE_PATH}/*.log "${RESULTS_DIR}/"
scp -J ubuntu@100.112.91.33 -q ubuntu@${NODE1_IP}:${REMOTE_PATH}/*.csv "${RESULTS_DIR}/"

# Scarica log Write (tutti quelli generati dal loop)
scp -J ubuntu@100.112.91.33 -q ubuntu@${NODE2_IP}:${REMOTE_PATH}/*.log "${RESULTS_DIR}/"
scp -J ubuntu@100.112.91.33 -q ubuntu@${NODE2_IP}:${REMOTE_PATH}/*.csv "${RESULTS_DIR}/"

echo "📥 Scaricamento logs infrastruttura..."
$ERMES_DEPLOY_PATH/scripts/download_logs.sh

# --- 6. CREAZIONE ZIP ---
echo "📦 [6/6] Creazione archivio ZIP..."

ZIP_FILENAME="bottom_up_${TIMESTAMP}.zip"

if command -v zip >/dev/null 2>&1; then
    mkdir -p ../data/bottom_up

    zip -q -j ../data/bottom_up/"${ZIP_FILENAME}" \
        "${RESULTS_DIR}"/results_log_54321_*.csv \
        "${RESULTS_DIR}"/results_log_2*.csv \
        logs/*/general_*.log

    if [ $? -eq 0 ]; then
        echo "✅ Archivio creato correttamente: ${ZIP_FILENAME}"
    else
        echo "❌ Errore durante la creazione dello zip."
    fi
else
    echo "⚠️  Comando 'zip' non trovato. Impossibile comprimere i file."
fi