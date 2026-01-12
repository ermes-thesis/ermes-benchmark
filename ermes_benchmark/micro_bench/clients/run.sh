#!/bin/bash

# --- CONFIGURAZIONE TARGET ---
ERMES_NODES=("10.10.101.50" "10.10.101.51" "10.10.101.52" "10.10.101.53" "10.10.101.54" "10.10.101.55" "10.10.101.56" "10.10.101.57" "10.10.101.58")

# Percorso del file di configurazione sul server remoto
REMOTE_CONFIG_PATH="/etc/ermes-node/config.yaml"

# --- GESTIONE MODALITÀ (DA INPUT) ---
INPUT_MODE=$1

# --- CONFIGURAZIONE PARAMETRI ESPERIMENTO ---
USERS_LIST=("1" "4")
COLLECTIONS_LIST=("1" "10")
SEEDS=("1" "42")
#USERS_LIST=("1024")
#COLLECTIONS_LIST=("1000")
#SEEDS=("91011")
FN_ROUND=25

# Definiamo l'array delle modalità da eseguire
if [[ "$INPUT_MODE" == "all" ]]; then
    TARGET_MODES=("eventual" "sequential")
elif [[ -n "$INPUT_MODE" ]]; then
    TARGET_MODES=("$INPUT_MODE")
else
    # Default se vuoto
    echo "⚠️  Nessuna modalità specificata, uso default: eventual"
    TARGET_MODES=("eventual")
fi

echo "📋 Pianificazione esecuzione per: ${TARGET_MODES[*]}"

# --- FUNZIONI UTILITÀ ---

# Funzione per mostrare la barra di progresso
show_progress() {
    local pid=$1
    local duration=$2
    local interval=1
    local elapsed=0
    local width=40

    # Controlla se il processo esiste (kill -0)
    while kill -0 "$pid" 2>/dev/null; do
        # Calcolo percentuale (max 100%)
        local perc=$(( 100 * elapsed / duration ))
        if [ $perc -gt 100 ]; then perc=100; fi

        # Calcolo barre
        local num_chars=$(( width * perc / 100 ))

        # Costruzione barra visiva
        local bar=""
        for ((i=0; i<num_chars; i++)); do bar+="#"; done
        for ((i=num_chars; i<width; i++)); do bar+="."; done

        # Stampa (Sovrascrive la riga corrente con \r)
        printf "\r⏳ [%s] %3d%% (%ds/%ds) " "$bar" "$perc" "$elapsed" "$duration"

        sleep "$interval"
        elapsed=$((elapsed + interval))
    done

    # Quando finisce, stampa 100% e va a capo
    printf "\r✅ [%s] 100%% (%ds/%ds) - Completato!\n" "$(for ((i=0; i<width; i++)); do echo -n "#"; done)" "$elapsed" "$duration"
}

# Funzione per pulire e configurare i nodi remoti
flush_remote_nodes() {
    local F_THRESH=$1
    local L_THRESH=$2

    echo "🧹 [Global Flush] Configurazione nodi (Follower=${F_THRESH}, Leader=${L_THRESH}) e pulizia..."

    for NODE_IP in "${ERMES_NODES[@]}"; do
        ssh -o StrictHostKeyChecking=no ubuntu@${NODE_IP} "sudo bash -s" -- "$F_THRESH" "$L_THRESH" "$REMOTE_CONFIG_PATH" << 'EOF'

        # Recupero argomenti
        NEW_FOLLOWER_THRESH=$1
        NEW_LEADER_THRESH=$2
        CONFIG_FILE=$3

        # Configurazione
        REDIS_PORT=6379
        REDIS_PASS="very-secure-password"
        LOG_DIR="/var/log/ermes-node/"
        SPECIFIC_LOGS=("/var/log/ermes-node/general.log" "/var/log/ermes-node/ermes-node.err.log" "/var/log/ermes-node/dump.ndjson")

        # 1. Stop servizio
        systemctl stop ermes-node || true

        # 2. Modifica YAML (sed)
        if [ -f "$CONFIG_FILE" ]; then
            # Sostituisce i valori mantenendo l'indentazione originale
            sed -i -E "s/(\s*)followerThreshold:.*/\1followerThreshold: $NEW_FOLLOWER_THRESH/" "$CONFIG_FILE"
            sed -i -E "s/(\s*)leaderThreshold:.*/\1leaderThreshold: $NEW_LEADER_THRESH/" "$CONFIG_FILE"
        else
            echo "⚠️  File config non trovato su questo nodo!"
        fi

        # 3. Pulizia Redis
        REDIS_CMD="redis-cli -p $REDIS_PORT"
        if [ -n "$REDIS_PASS" ]; then REDIS_CMD+=" -a $REDIS_PASS"; fi
        $REDIS_CMD FLUSHALL >/dev/null 2>&1 || true
        $REDIS_CMD FT.DROPINDEX metadata_index >/dev/null 2>&1 || true

        # 4. Gestione Log
        if [ ! -d "$LOG_DIR" ]; then mkdir -p "$LOG_DIR"; chmod 755 "$LOG_DIR"; fi

        find "$LOG_DIR" -maxdepth 1 -name "general-*" -type f -delete || true

        for log_file in "${SPECIFIC_LOGS[@]}"; do
            if [ -f "$log_file" ]; then
                truncate -s 0 "$log_file" || true
            fi
        done

        # 5. Riavvio
        systemctl start ermes-node
EOF
        echo "   ✅ ${NODE_IP} configurato e riavviato."
    done
    sleep 5
}

copy_logs() {
    local NAME_EXP=$1
    for NODE_IP in "${ERMES_NODES[@]}"; do
        ssh -o StrictHostKeyChecking=no ubuntu@${NODE_IP} "sudo bash -s" -- "$NAME_EXP" << 'EOF'
        NAME_EXP=$1
        mkdir -p "/home/ubuntu/experiments_${NAME_EXP}"
        cp /var/log/ermes-node/* "/home/ubuntu/experiments_${NAME_EXP}"
EOF
    done
    sleep 5
}

# Setup cartelle locali
cd "$(dirname "$0")" || exit

rm -rf results user.log create.log
mkdir -p results

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "   -> Timestamp: ${TIMESTAMP}"

echo "🏁 Inizio sequenza esperimenti..."

# --- CICLO ESTERNO PER LA MODALITÀ (eventual, sequential, etc.) ---
for CONSISTENCY_MODE in "${TARGET_MODES[@]}"; do

  echo "##########################################################"
  echo "🔷 CAMBIO MODALITÀ: $CONSISTENCY_MODE"
  echo "##########################################################"

  for USERS in "${USERS_LIST[@]}"; do
    for COLLECTIONS in "${COLLECTIONS_LIST[@]}"; do
      for SEED in "${SEEDS[@]}"; do

        # --- CALCOLO DINAMICO THRESHOLD ---
        # 1. Calcolo il divisore: min(COLLECTIONS, 25)
        if [ "$COLLECTIONS" -lt 25 ]; then
            DIVISOR=$COLLECTIONS
        else
            DIVISOR=25
        fi

        # 2. Calcolo il fattore: min(COLLECTIONS, 4)
        if [ "$COLLECTIONS" -lt 4 ]; then
            FACTOR=$COLLECTIONS
        else
            FACTOR=4
        fi

        # 3. Applico le formule
        # Leader = 450 * FACTOR / DIVISOR
        L_VAL=$(( (450 * FACTOR) / DIVISOR ))

        # Follower = 150 * FACTOR / DIVISOR
        F_VAL=$(( (150 * FACTOR) / DIVISOR ))

        echo "=================================================="
        echo "🚀 Avvio: Mode=${CONSISTENCY_MODE}, U=${USERS}, C=${COLLECTIONS}, Seed=${SEED}"
        echo "🧮 Calcolo Threshold (Divisore=${DIVISOR}, Fattore=${FACTOR}):"
        echo "   -> Leader:   ${L_VAL}"
        echo "   -> Follower: ${F_VAL}"
        echo "=================================================="

        # 1. GENERAZIONE SETUP (Locale)
        python3 test_generator.py --seed "$SEED" --n_collections "$COLLECTIONS" --n_users "$USERS" --fn_per_round "$FN_ROUND"
        SETUP_FILE="tests/setup_experiment_${SEED}_users_${USERS}_collections_${COLLECTIONS}.json"

        # 2. AGGIORNAMENTO CONFIG E PULIZIA (Remoto)
        flush_remote_nodes "$F_VAL" "$L_VAL"

        # 3. PULIZIA LOG LOCALI
        rm user.log create.log 2>/dev/null

        # 4. CREAZIONE DATI
        echo "⏳ Creazione dati in corso ($CONSISTENCY_MODE)..."
        ./create "$SETUP_FILE" "$CONSISTENCY_MODE" > create.log 2>&1
        echo "✅ Creazione dati completata."

        # Rimuove log della creazione
        rm create.log results/results_log_2000_*.csv 2>/dev/null

        # 5. ESECUZIONE TEST (Con Progress Bar)
        echo "⏳ Avvio esperimento (Durata stimata: 2m 30s)..."

        # Esegui in background
        ./user "$SETUP_FILE" > user.log 2>&1 &

        # Cattura PID
        USER_PID=$!

        # Mostra barra
        show_progress $USER_PID 150

        # Attendi fine reale del processo
        wait $USER_PID

        echo "✅ Esperimento completato."

        # Copia log dai nodi remoti
        echo "⏳ Copia log dai nodi remoti..."
        copy_logs "${TIMESTAMP}_mode_${CONSISTENCY_MODE}_users_${USERS}_collections_${COLLECTIONS}_seed_${SEED}"
        echo "✅ Copia log completata."

        echo "✅ Completato round."

        mkdir -p "results/mode_${CONSISTENCY_MODE}_users_${USERS}_collections_${COLLECTIONS}/seed_${SEED}/"
        mv results/results_log_*.csv "results/mode_${CONSISTENCY_MODE}_users_${USERS}_collections_${COLLECTIONS}/seed_${SEED}/"

      done
    done
  done
done

echo "⏳ Aggregazione risultati..."
python3 csv_aggregator.py results

echo "🎉 TUTTI I TEST COMPLETATI."