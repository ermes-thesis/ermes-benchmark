#!/bin/bash

# --- CONFIGURAZIONE TARGET ---
ERMES_NODES=("10.10.101.50" "10.10.101.51" "10.10.101.52" "10.10.101.53" "10.10.101.54" "10.10.101.55" "10.10.101.56" "10.10.101.57" "10.10.101.58")
REMOTE_CONFIG_PATH="/etc/ermes-node/config.yaml"

# --- INPUT ---
# $1 = Modalità consistenza (eventual, sequential, all)
# $2 = Tipo esperimento (scalability, density) - Default: scalability
INPUT_MODE=$1
EXP_TYPE=${2:-"scalability"}

# --- PARAMETRI GENERALI ---
FN_ROUND=25
SEEDS=("1" "42" "100" "2024" "7" "99" "1234" "5678" "91011" "121314")
#SEEDS=("1") # Debug veloce

# --- CONFIGURAZIONE THRESHOLD ---
# REF_USERS: Numero di utenti "standard" (baseline)
# DAMPING: Fattore di smorzamento (più è alto, meno la threshold cambia drasticamente)
# MIN_TH: Valore minimo assoluto per le threshold
REF_USERS=1024
DAMPING=200
MIN_TH=1

if [[ "$INPUT_MODE" == "all" ]]; then
    TARGET_MODES=("eventual" "sequential")
elif [[ -n "$INPUT_MODE" ]]; then
    TARGET_MODES=("$INPUT_MODE")
else
    echo "⚠️  Nessuna modalità specificata, uso default: eventual"
    TARGET_MODES=("eventual")
fi

# --- FUNZIONI UTILITÀ ---

# Funzione centrale per calcolare L_VAL e F_VAL
calculate_thresholds() {
    local u_in=$1
    local c_in=$2

    # Sanitizzazione Input
    if [ -z "$u_in" ] || [ "$u_in" -lt 1 ]; then u_in=1; fi
    if [ -z "$c_in" ] || [ "$c_in" -lt 1 ]; then c_in=1; fi

    # --- Calcolo Logica Base (Originale basata sulle Collection) ---
    local div
    local fac

    if [ "$c_in" -lt 25 ]; then div=$c_in; else div=25; fi
    if [ "$div" -eq 0 ]; then div=1; fi

    if [ "$c_in" -lt 4 ]; then fac=$c_in; else fac=4; fi

    local l_base=$(( (450 * fac) / div ))
    local f_base=$(( (150 * fac) / div ))

    # --- Applicazione Fattore Utenti Smorzato ---
    # Formula: ValoreBase * (Utenti + Cuscino) / (Riferimento + Cuscino)
    local num=$(( u_in + DAMPING ))
    local den=$(( REF_USERS + DAMPING ))

    # Assegnazione variabili GLOBALI
    L_VAL=$(( (l_base * num) / den ))
    F_VAL=$(( (f_base * num) / den ))

    # --- Controllo Minimo (Safety) ---
    if [ "$L_VAL" -lt "$MIN_TH" ]; then L_VAL=$MIN_TH; fi
    if [ "$F_VAL" -lt "$MIN_TH" ]; then F_VAL=$MIN_TH; fi
}

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
    printf "\r✅ [%s] 100%% (%ds/%ds) - Completato!\033[K\n" "DONE" "$elapsed" "$duration"
}

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
}

# --- FUNZIONI CORE ESPERIMENTI ---

# 1. ESPERIMENTO SCALABILITÀ
run_scalability() {
    echo "🏁 AVVIO TEST SCALABILITÀ (Varia User/Coll)..."
    USERS_LIST=("1" "4" "16" "64" "256" "512" "1024")
    COLLECTIONS_LIST=("1" "10" "100" "1000")

    echo "🏁 Inizio sequenza esperimenti..."

    for CONSISTENCY_MODE in "${TARGET_MODES[@]}"; do
      echo "##########################################################"
      echo "🔷 CAMBIO MODALITÀ: $CONSISTENCY_MODE"
      echo "##########################################################"

      for USERS in "${USERS_LIST[@]}"; do
        for COLLECTIONS in "${COLLECTIONS_LIST[@]}"; do
          for SEED in "${SEEDS[@]}"; do

            # CALCOLO THRESHOLD
            calculate_thresholds "$USERS" "$COLLECTIONS"

            echo "🚀 [SCALABILITY] Mode=$CONSISTENCY_MODE, U=$USERS, C=$COLLECTIONS, Seed=$SEED (L=$L_VAL F=$F_VAL)"

            # 1. GENERAZIONE SETUP
            python3 test_generator.py --seed "$SEED" --n_collections "$COLLECTIONS" --n_users "$USERS" --fn_per_round "$FN_ROUND"
            SETUP_FILE="tests/setup_experiment_${SEED}_users_${USERS}_collections_${COLLECTIONS}.json"

            # 2. AGGIORNAMENTO CONFIG E PULIZIA
            flush_remote_nodes "$F_VAL" "$L_VAL"

            # 3. CREAZIONE DATI
            echo "⏳ Creazione dati in corso ($CONSISTENCY_MODE)..."
            ./create "$SETUP_FILE" "$CONSISTENCY_MODE" > create.log 2>&1
            echo "✅ Creazione dati completata."

            # Rimuove log della creazione
            rm results/results_log_2000_*.csv 2>/dev/null

            # 4. ESECUZIONE
            ./user "$SETUP_FILE" "1" > user.log 2>&1 &
            show_progress $! 150
            wait $!

            LOG_ID="scalability_mode_${CONSISTENCY_MODE}_u${USERS}_c${COLLECTIONS}_s${SEED}"
            copy_logs "${TIMESTAMP}_${LOG_ID}"

            CONFIG_DIR="results/mode_${CONSISTENCY_MODE}_users_${USERS}_collections_${COLLECTIONS}"
            SEED_DIR="${CONFIG_DIR}/seed_${SEED}"

            mkdir -p "$SEED_DIR"
            mv results/results_log_*.csv results/*.log "$SEED_DIR/"
          done
        done
      done
    done
}

run_scalability_moving_users() {
    echo "🏁 AVVIO TEST SCALABILITÀ MOVING USERS..."
    USERS_LIST=("64")
    COLLECTIONS_LIST=("1000")

    echo "🏁 Inizio sequenza esperimenti..."

    for CONSISTENCY_MODE in "${TARGET_MODES[@]}"; do

      echo "##########################################################"
      echo "🔷 CAMBIO MODALITÀ: $CONSISTENCY_MODE"
      echo "##########################################################"

      for USERS in "${USERS_LIST[@]}"; do
        for COLLECTIONS in "${COLLECTIONS_LIST[@]}"; do
          for SEED in "${SEEDS[@]}"; do

            # CALCOLO THRESHOLD
            calculate_thresholds "$USERS" "$COLLECTIONS"

            echo "🚀 [SCALABILITY MOVING] Mode=$CONSISTENCY_MODE, U=$USERS, C=$COLLECTIONS, Seed=$SEED (L=$L_VAL F=$F_VAL)"

            # 1. GENERAZIONE SETUP
            python3 test_generator.py --seed "$SEED" --n_collections "$COLLECTIONS" --n_users "$USERS" --fn_per_round "$FN_ROUND"
            SETUP_FILE="tests/setup_experiment_${SEED}_users_${USERS}_collections_${COLLECTIONS}.json"

            # 2. FLUSH
            flush_remote_nodes "$F_VAL" "$L_VAL"

            # 3. CREATE
            echo "⏳ Creazione dati in corso ($CONSISTENCY_MODE)..."
            ./create "$SETUP_FILE" "$CONSISTENCY_MODE" > create.log 2>&1
            echo "✅ Creazione dati completata."

            # Rimuove log della creazione
            rm results/results_log_2000_*.csv 2>/dev/null

            # 4. ESECUZIONE
            ./moving_user "$SETUP_FILE" "1" > user.log 2>&1 &
            show_progress $! 300
            wait $!

            LOG_ID="scalability_mode_${CONSISTENCY_MODE}_u${USERS}_c${COLLECTIONS}_s${SEED}"
            copy_logs "${TIMESTAMP}_${LOG_ID}"

            CONFIG_DIR="results/mode_${CONSISTENCY_MODE}_users_${USERS}_collections_${COLLECTIONS}"
            SEED_DIR="${CONFIG_DIR}/seed_${SEED}"

            mkdir -p "$SEED_DIR"
            mv results/results_log_*.csv results/*.log "$SEED_DIR/"
          done
        done
      done
    done
}

# 2. ESPERIMENTO DENSITÀ
run_density() {
    echo "🏁 AVVIO TEST DENSITÀ (Varia numero di accessi alla collection per funzione)..."
    FIXED_USERS="64"
    FIXED_COLLECTIONS="100"
    ACCESSES_LIST=("1" "5" "10")

    for CONSISTENCY_MODE in "${TARGET_MODES[@]}"; do
      for ACC in "${ACCESSES_LIST[@]}"; do
        for SEED in "${SEEDS[@]}"; do

            # CALCOLO THRESHOLD (Uso valori fissi)
            calculate_thresholds "$FIXED_USERS" "$FIXED_COLLECTIONS"

            echo "🚀 [DENSITY] Mode=$CONSISTENCY_MODE, Accesses=$ACC, Seed=$SEED (L=$L_VAL F=$F_VAL)"

            python3 test_generator.py --seed "$SEED" --n_collections "$FIXED_COLLECTIONS" --n_users "$FIXED_USERS" --fn_per_round "$FN_ROUND"
            SETUP_FILE="tests/setup_experiment_${SEED}_users_${FIXED_USERS}_collections_${FIXED_COLLECTIONS}.json"

            flush_remote_nodes "$F_VAL" "$L_VAL"

            echo "⏳ Creazione dati in corso ($CONSISTENCY_MODE)..."
            ./create "$SETUP_FILE" "$CONSISTENCY_MODE" "$ACC" > create.log 2>&1
            echo "✅ Creazione dati completata."

            rm results/results_log_*.csv 2>/dev/null

            # ESECUZIONE
            ./user "$SETUP_FILE" "$ACC" > user.log 2>&1 &
            show_progress $! 150
            wait $!

            LOG_ID="density_mode_${CONSISTENCY_MODE}_acc${ACC}_s${SEED}"
            copy_logs "${TIMESTAMP}_${LOG_ID}"

            # Salvataggio CSV Risultati
            CONFIG_DIR="results/mode_${CONSISTENCY_MODE}_accesses_${ACC}"
            SEED_DIR="${CONFIG_DIR}/seed_${SEED}"

            mkdir -p "$SEED_DIR"
            mv results/results_log_*.csv results/*.log "$SEED_DIR/"
          done
      done
    done
}

# --- MAIN ---

cd "$(dirname "$0")" || exit
rm -rf results user.log create.log
mkdir -p results
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [[ "$EXP_TYPE" == "scalability" ]]; then
    run_scalability
elif [[ "$EXP_TYPE" == "density" ]]; then
    run_density
elif [[ "$EXP_TYPE" == "moving" ]]; then
    run_scalability_moving_users
else
    echo "❌ Tipo esperimento sconosciuto: $EXP_TYPE (usa 'scalability', 'density' o 'moving')"
    exit 1
fi

echo "⏳ Aggregazione risultati..."
python3 csv_aggregator.py results
echo "🎉 TUTTI I TEST COMPLETATI."