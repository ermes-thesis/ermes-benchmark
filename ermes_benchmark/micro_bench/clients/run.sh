#!/bin/bash

# --- CONTROLLO PARAMETRI ---
if [ "$#" -ne 3 ]; then
    echo "❌ Errore: Devi specificare il numero di utenti e di collections."
    echo "Uso: $0 <NUM_USERS> <NUM_COLLECTIONS> <SEED>"
    echo "Esempio: $0 10 10 42"
    exit 1
fi

NUM_USERS=$1
NUM_COLLECTIONS=$2
SEED=$3

echo "📋 Configurazione: ${NUM_USERS} Utenti, ${NUM_COLLECTIONS} Collections, Seed=${SEED}"

# --- CONFIGURAZIONE ---
NODE2_IP="10.10.101.59"
REMOTE_PATH="micro_test"
ERMES_DEPLOY_PATH="../../../../ermes-deploy"

# --- 1. COMPILAZIONE (Cross-Compilation) ---
echo "🚧 [1/6] Compilazione per Linux/AMD64..."

env GOOS=linux GOARCH=amd64 go build -C user -ldflags="-s -w" -o ../bin/user .
env GOOS=linux GOARCH=amd64 go build -C create -ldflags="-s -w" -o ../bin/create .

if [ $? -ne 0 ]; then
    echo "❌ Errore durante la compilazione. Mi fermo."
    exit 1
fi
echo "✅ Compilazione completata."

# --- 2. COPIA DEI BINARI (SCP) ---
echo "🚀 [2/6] Copia dei binari e config sulle VM..."

# Uccidiamo eventuali vecchi processi rimasti appesi
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "sudo pkill -f create || true"
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "sudo pkill -f user || true"

# SCP usando il file di setup dinamico
scp -J ubuntu@100.112.91.33 -q bin/{user,create} config.yaml ../csv_aggregator.py ../test_generator.py run_experiment.sh ubuntu@${NODE2_IP}:${REMOTE_PATH}

echo "✅ Upload completato."

echo " Genera file di configurazione..."
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "cd ${REMOTE_PATH}; python3 test_generator.py --seed $SEED --n_collections $NUM_COLLECTIONS --n_users $NUM_USERS"
SETUP_FILE="tests/setup_experiment_${SEED}_users_${NUM_USERS}_collections_${NUM_COLLECTIONS}.json"
echo "🧹 [3/6] Pulisco Ermes"
ANSIBLE_CONFIG=${ERMES_DEPLOY_PATH}/ansible.cfg ansible-playbook ${ERMES_DEPLOY_PATH}/flush-ermes-nodes.yml
echo "✅ Pulizia completata."

# --- 4. ESECUZIONE (SSH) ---
echo "⚡ [4/6] Avvio dei processi..."

# Avvio Creazione collections (usando il file dinamico)
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "cd ${REMOTE_PATH}; ./create ${SETUP_FILE} > create.log 2>&1"
echo "   -> Collection creata su ${NODE2_IP}"

# Pulizia cartelle remote
ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "mkdir -p ${REMOTE_PATH}; cd ${REMOTE_PATH}; rm *.log results_log_*.csv 2>/dev/null"

# 4c. Avvio Write (Loop parallelo dinamico)
echo "   -> Avvio ${NUM_USERS} client in parallelo..."

ssh -J ubuntu@100.112.91.33 ubuntu@${NODE2_IP} "cd ${REMOTE_PATH}; ./run_experiment.sh $NUM_USERS $NUM_COLLECTIONS $SETUP_FILE $SEED"

echo "✅ Il test è terminato."

