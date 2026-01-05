#!/bin/bash

MODE=$1

# Verifica che l'utente abbia passato un argomento valido
if [[ "$MODE" != "eventual" && "$MODE" != "sequential" ]]; then
    echo "❌ Errore: Devi specificare la modalità di consistenza."
    echo "   Uso: $0 [eventual | sequential]"
    exit 1
fi

echo "⚙️  Modalità selezionata: $MODE"

# Configurazione connessione
NODE2_IP="10.10.101.59"
JUMP_HOST="100.112.91.33"
REMOTE_PATH="micro_test"

# 1. Compilazione (Localmente)
echo "🚧 Compilazione Go per Linux/AMD64..."
env GOOS=linux GOARCH=amd64 go build -C user -ldflags="-s -w" -o ../bin/user .
env GOOS=linux GOARCH=amd64 go build -C create -ldflags="-s -w" -o ../bin/create .

if [ $? -ne 0 ]; then
    echo "❌ Errore compilazione."
    exit 1
fi

# 2. Upload dei file necessari
echo "🚀 Upload dei binari e degli script sul server..."
scp -J ubuntu@${JUMP_HOST} -q \
    bin/{user,create} \
    config.yaml \
    ../csv_aggregator.py \
    ../test_generator.py \
    run.sh \
    ubuntu@${NODE2_IP}:${REMOTE_PATH}

# 3. Avvio dell'esperimento remoto in una sessione TMUX
echo "⚡ Avvio dell'orchestratore sul server in sessione TMUX..."

# Il comando seguente:
# 1. Chiude la sessione 'experiment' se esiste già (per pulizia)
# 2. Va nella cartella corretta
# 3. Rende eseguibili gli script
# 4. Crea una nuova sessione tmux staccata (-d) chiamata 'experiment'
# 5. Esegue run.sh e alla fine attende un input (read) per non chiudere la finestra subito
ssh -J ubuntu@${JUMP_HOST} ubuntu@${NODE2_IP} "
    tmux kill-session -t experiment 2>/dev/null;
    cd ${REMOTE_PATH};
    chmod +x *.sh;
    tmux new-session -d -s experiment './run.sh $MODE; echo \"Premi Invio per chiudere.\"; read'
"

echo "✅ Esperimento avviato su TMUX!"
echo "=================================================================="
echo "PER VEDERE L'AVANZAMENTO ESEGUI QUESTO COMANDO:"
echo "   ssh -J ubuntu@${JUMP_HOST} -t ubuntu@${NODE2_IP} 'tmux attach -t experiment'"
echo "=================================================================="