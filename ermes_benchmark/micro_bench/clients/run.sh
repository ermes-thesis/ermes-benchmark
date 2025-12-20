#!/bin/bash

# --- CONFIGURAZIONE TARGET ---
ERMES_NODES=("10.10.101.50" "10.10.101.51" "10.10.101.52" "10.10.101.53" "10.10.101.54" "10.10.101.55" "10.10.101.56" "10.10.101.57")

# --- FUNZIONE FLUSH REMOTA ---
flush_remote_nodes() {
    echo "🧹 [Global Flush] Avvio pulizia su ${#ERMES_NODES[@]} nodi..."

    for NODE_IP in "${ERMES_NODES[@]}"; do
        # Eseguiamo ssh passando il blocco di comandi.
        # "sudo bash -s" esegue tutto il blocco come root sul server remoto.
        ssh -o StrictHostKeyChecking=no ubuntu@${NODE_IP} "sudo bash -s" << 'EOF'

        # --- INIZIO CODICE REMOTO (Eseguito su nodo destinazione) ---

        # Configurazione
        REDIS_PORT=6379
        REDIS_PASS="very-secure-password"
        LOG_DIR="/var/log/ermes-node/"
        SPECIFIC_LOGS=("/var/log/ermes-node/general.log" "/var/log/ermes-node/ermes-node.err.log" "/var/log/ermes-node/dump.ndjson")

        # Costruzione comando Redis
        REDIS_CMD="redis-cli -p $REDIS_PORT"
        if [ -n "$REDIS_PASS" ]; then
            REDIS_CMD+=" -a $REDIS_PASS"
        fi

        systemctl stop ermes-node || true

        $REDIS_CMD FLUSHALL >/dev/null 2>&1 || true

        $REDIS_CMD FT.DROPINDEX metadata_index >/dev/null 2>&1 || true

        if [ ! -d "$LOG_DIR" ]; then
            mkdir -p "$LOG_DIR"
            chmod 755 "$LOG_DIR"
        fi

        find "$LOG_DIR" -maxdepth 1 -name "general-*" -type f -delete || true

        for log_file in "${SPECIFIC_LOGS[@]}"; do
            if [ -f "$log_file" ]; then
                truncate -s 0 "$log_file" || true
            fi
        done

        systemctl start ermes-node

        # --- FINE CODICE REMOTO ---
EOF
        echo "   ✅ ${NODE_IP} pulito."
    done

    sleep 5
}

# --- CONFIGURAZIONE PARAMETRI ---
VALUES=("1" "10" "100" "1000")
SEEDS=("1" "42" "100" "2024" "7" "99" "1234" "5678" "91011" "121314")
#VALUES=("1000")
#SEEDS=("1")
FN_ROUND=25

# Setup cartelle locali (sulla macchina che orchestra)
cd "$(dirname "$0")" || exit
mkdir -p results

echo "🏁 Inizio sequenza esperimenti, numero funzioni: ${FN_ROUND}..."

for SEED in "${SEEDS[@]}"; do
  for USERS in "${VALUES[@]}"; do
    for COLLECTIONS in "${VALUES[@]}"; do

        echo "=================================================="
        echo "🚀 Avvio: Users=${USERS}, Collections=${COLLECTIONS}, Seed=${SEED}"
        echo "=================================================="

        # 1. GENERAZIONE SETUP (Locale)
        python3 test_generator.py --seed "$SEED" --n_collections "$COLLECTIONS" --n_users "$USERS" --fn_per_round "$FN_ROUND"
        SETUP_FILE="tests/setup_experiment_${SEED}_users_${USERS}_collections_${COLLECTIONS}.json"

        # 2. PULIZIA ERMES SU NODI REMOTI
        flush_remote_nodes

        # 3. PULIZIA LOG CLIENT LOCALI
        rm user.log create.log 2>/dev/null

        # 4. CREAZIONE COLLECTIONS
        echo "⏳ Creazione dati in corso..."
        ./create "$SETUP_FILE" > create.log 2>&1
        echo "✅ Creazione dati completata."

        rm create.log results_log_*.csv

        # 5. ESECUZIONE TEST
        echo "⏳ Esperimento in corso..."
        ./user "$SETUP_FILE" > user.log 2>&1
        echo "✅ Esperimento completato."

        echo "⏳ Aggregazione risultati..."
        python3 csv_aggregator.py . "aggregated_results_users_${USERS}_collections_${COLLECTIONS}.csv" "$SEED"

        echo "✅ Completato round."

    done
  done
done

echo "🎉 TUTTI I TEST COMPLETATI."