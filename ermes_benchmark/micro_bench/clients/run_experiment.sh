#!/bin/bash

# $1 = Mode (eventual/sequential)
# $2 = Experiment Type (scalability/density) - Opzionale, default scalability
MODE=$1
EXP_TYPE=${2:-"scalability"}

if [[ "$MODE" != "eventual" && "$MODE" != "sequential" && "$MODE" != "all" ]]; then
    echo "❌ Errore: Specifica la modalità."
    echo "   Uso: $0 [ eventual | sequential | all ] [ scalability | density ]"
    exit 1
fi

echo "⚙️  Modalità: $MODE | Esperimento: $EXP_TYPE"

NODE2_IP="10.10.101.59"
JUMP_HOST="100.112.91.33"
REMOTE_PATH="micro_test"

# 1. Compilazione
echo "🚧 Compilazione Go..."
env GOOS=linux GOARCH=amd64 go build -C user -ldflags="-s -w" -o ../bin/user .
env GOOS=linux GOARCH=amd64 go build -C create -ldflags="-s -w" -o ../bin/create .

if [ $? -ne 0 ]; then
    echo "❌ Errore compilazione."
    exit 1
fi

# 2. Upload
echo "🚀 Upload file..."
scp -J ubuntu@${JUMP_HOST} -q \
    bin/{user,create} \
    config.yaml \
    ../csv_aggregator.py \
    ../test_generator.py \
    run.sh \
    ubuntu@${NODE2_IP}:${REMOTE_PATH}

# 3. Avvio TMUX con i DUE argomenti
echo "⚡ Avvio orchestratore su TMUX..."
ssh -J ubuntu@${JUMP_HOST} ubuntu@${NODE2_IP} "
    tmux kill-session -t experiment 2>/dev/null;
    cd ${REMOTE_PATH};
    chmod +x *.sh;
    tmux new-session -d -s experiment './run.sh $MODE $EXP_TYPE; echo \"Premi Invio per chiudere.\"; read'
"

echo "✅ Avviato! Controlla con: ssh -J ubuntu@${JUMP_HOST} -t ubuntu@${NODE2_IP} 'tmux attach -t experiment'"