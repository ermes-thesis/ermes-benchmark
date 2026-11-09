#!/bin/bash

# --- TARGET CONFIGURATION ---
# ERMES_SUBNET is injected by run_experiment.sh; the Go clients read it too.
export ERMES_SUBNET="${ERMES_SUBNET:-10.10.101}"
SUBNET="$ERMES_SUBNET"
ERMES_NODES=(); for o in 70 71 72 73 74 75 76 77 78; do ERMES_NODES+=("${SUBNET}.${o}"); done
REMOTE_CONFIG_PATH="/etc/ermes-node/config.yaml"

# --- INPUT ---
# $1 = consistency mode (eventual, sequential, all)
# $2 = experiment type (scalability, density, moving) - default: scalability
INPUT_MODE=$1
EXP_TYPE=${2:-"scalability"}

# --- GENERAL PARAMETERS ---
FN_ROUND=25
SEEDS=("1" "42" "100")

# --- MIGRATION THRESHOLD CONFIGURATION ---
# REF_USERS: reference ("baseline") number of users
# DAMPING: damping factor (the higher, the less the thresholds change with the load)
# MIN_TH: absolute minimum threshold value
REF_USERS=1024
DAMPING=200
MIN_TH=1

if [[ "$INPUT_MODE" == "all" ]]; then
    TARGET_MODES=("eventual" "sequential")
elif [[ -n "$INPUT_MODE" ]]; then
    TARGET_MODES=("$INPUT_MODE")
else
    echo "⚠️  No mode specified, using default: eventual"
    TARGET_MODES=("eventual")
fi

# --- UTILITY FUNCTIONS ---

# Compute the leader/follower migration thresholds (L_VAL, F_VAL) for a given load
calculate_thresholds() {
    local u_in=$1
    local c_in=$2

    if [ -z "$u_in" ] || [ "$u_in" -lt 1 ]; then u_in=1; fi
    if [ -z "$c_in" ] || [ "$c_in" -lt 1 ]; then c_in=1; fi

    # Base values, scaled by the number of collections
    local div
    local fac

    if [ "$c_in" -lt 25 ]; then div=$c_in; else div=25; fi
    if [ "$div" -eq 0 ]; then div=1; fi

    if [ "$c_in" -lt 4 ]; then fac=$c_in; else fac=4; fi

    local l_base=$(( (450 * fac) / div ))
    local f_base=$(( (150 * fac) / div ))

    # Damped user factor: base * (users + damping) / (ref_users + damping)
    local num=$(( u_in + DAMPING ))
    local den=$(( REF_USERS + DAMPING ))

    L_VAL=$(( (l_base * num) / den ))
    F_VAL=$(( (f_base * num) / den ))

    if [ "$L_VAL" -lt "$MIN_TH" ]; then L_VAL=$MIN_TH; fi
    if [ "$F_VAL" -lt "$MIN_TH" ]; then F_VAL=$MIN_TH; fi
}

show_progress() {
    local pid=$1
    local duration=$2
    local interval=1
    local elapsed=0
    local width=40

    while kill -0 "$pid" 2>/dev/null; do
        local perc=$(( 100 * elapsed / duration ))
        if [ $perc -gt 100 ]; then perc=100; fi

        local num_chars=$(( width * perc / 100 ))

        local bar=""
        for ((i=0; i<num_chars; i++)); do bar+="#"; done
        for ((i=num_chars; i<width; i++)); do bar+="."; done

        printf "\r⏳ [%s] %3d%% (%ds/%ds) " "$bar" "$perc" "$elapsed" "$duration"

        sleep "$interval"
        elapsed=$((elapsed + interval))
    done
    printf "\r✅ [%s] 100%% (%ds/%ds) - Done!\033[K\n" "DONE" "$elapsed" "$duration"
}

# Reset every node between iterations: update thresholds, flush Redis, clear logs, restart
flush_remote_nodes() {
    local F_THRESH=$1
    local L_THRESH=$2

    echo "🧹 [Global flush] Configuring nodes (Follower=${F_THRESH}, Leader=${L_THRESH}) and cleaning up..."

    for NODE_IP in "${ERMES_NODES[@]}"; do
        ssh -o StrictHostKeyChecking=no ${ERMES_SSH_USER:-ubuntu}@${NODE_IP} "sudo bash -s" -- "$F_THRESH" "$L_THRESH" "$REMOTE_CONFIG_PATH" << 'EOF'

        NEW_FOLLOWER_THRESH=$1
        NEW_LEADER_THRESH=$2
        CONFIG_FILE=$3

        REDIS_PORT=6379
        REDIS_PASS="very-secure-password"
        LOG_DIR="/var/log/ermes-node/"
        SPECIFIC_LOGS=("/var/log/ermes-node/general.log" "/var/log/ermes-node/ermes-node.err.log" "/var/log/ermes-node/dump.ndjson")

        # 1. Stop the service
        systemctl stop ermes-node || true

        # 2. Update the thresholds in the YAML config (preserving indentation)
        if [ -f "$CONFIG_FILE" ]; then
            sed -i -E "s/(\s*)followerThreshold:.*/\1followerThreshold: $NEW_FOLLOWER_THRESH/" "$CONFIG_FILE"
            sed -i -E "s/(\s*)leaderThreshold:.*/\1leaderThreshold: $NEW_LEADER_THRESH/" "$CONFIG_FILE"
        else
            echo "⚠️  Config file not found on this node!"
        fi

        # 3. Flush Redis
        REDIS_CMD="redis-cli -p $REDIS_PORT"
        if [ -n "$REDIS_PASS" ]; then REDIS_CMD+=" -a $REDIS_PASS"; fi
        $REDIS_CMD FLUSHALL >/dev/null 2>&1 || true
        $REDIS_CMD FT.DROPINDEX metadata_index >/dev/null 2>&1 || true

        # 4. Clear logs
        if [ ! -d "$LOG_DIR" ]; then mkdir -p "$LOG_DIR"; chmod 755 "$LOG_DIR"; fi

        find "$LOG_DIR" -maxdepth 1 -name "general-*" -type f -delete || true

        for log_file in "${SPECIFIC_LOGS[@]}"; do
            if [ -f "$log_file" ]; then
                truncate -s 0 "$log_file" || true
            fi
        done

        # 5. Restart the service
        systemctl start ermes-node
EOF
    done
    sleep 5
}

copy_logs() {
    local NAME_EXP=$1
    for NODE_IP in "${ERMES_NODES[@]}"; do
        ssh -o StrictHostKeyChecking=no ${ERMES_SSH_USER:-ubuntu}@${NODE_IP} "sudo bash -s" -- "$NAME_EXP" << 'EOF'
        NAME_EXP=$1
        mkdir -p "/home/ubuntu/experiments_${NAME_EXP}"
        cp /var/log/ermes-node/* "/home/ubuntu/experiments_${NAME_EXP}"
EOF
    done
}

# --- EXPERIMENTS ---

# 1. SCALABILITY (Fig. 11 sweep + Fig. 13 temporal evolution at u1024/c1000)
run_scalability() {
    echo "🏁 STARTING SCALABILITY TEST (varying users/collections)..."
    USERS_LIST=("1" "4" "16" "64" "256" "512" "1024")
    COLLECTIONS_LIST=("1" "10" "100" "1000")
    # Cloud-Only note: Fig. 11 does not include the Cloud-Only baseline, so for
    # that configuration only the u1024/c1000 point is needed (Fig. 13):
    # USERS_LIST=("1024")
    # COLLECTIONS_LIST=("1000")

    echo "🏁 Starting experiment sequence..."

    for CONSISTENCY_MODE in "${TARGET_MODES[@]}"; do
      echo "##########################################################"
      echo "🔷 SWITCHING MODE: $CONSISTENCY_MODE"
      echo "##########################################################"

      NUM_ROUNDS=10
      if [ "$CONSISTENCY_MODE" == "sequential" ]; then
          NUM_ROUNDS=15
      fi

      for USERS in "${USERS_LIST[@]}"; do
        for COLLECTIONS in "${COLLECTIONS_LIST[@]}"; do
          for SEED in "${SEEDS[@]}"; do

            calculate_thresholds "$USERS" "$COLLECTIONS"

            echo "🚀 [SCALABILITY] Mode=$CONSISTENCY_MODE, U=$USERS, C=$COLLECTIONS, Seed=$SEED (L=$L_VAL F=$F_VAL)"

            # 1. Generate the experiment setup
            python3 test_generator.py --seed "$SEED" --n_collections "$COLLECTIONS" --n_users "$USERS" --fn_per_round "$FN_ROUND"
            SETUP_FILE="tests/setup_experiment_${SEED}_users_${USERS}_collections_${COLLECTIONS}.json"

            # 2. Update node configs and clean up
            flush_remote_nodes "$F_VAL" "$L_VAL"

            # 3. Create the collections
            echo "⏳ Creating data ($CONSISTENCY_MODE)..."
            ./create "$SETUP_FILE" "$CONSISTENCY_MODE" > create.log 2>&1
            echo "✅ Data creation completed."

            # Drop the creation-phase logs
            rm results/results_log_2000_*.csv 2>/dev/null

            # 4. Run the workload
            ./user "$SETUP_FILE" "1" "$NUM_ROUNDS" > user.log 2>&1 &

            DURATION=$(( NUM_ROUNDS * 15 ))
            show_progress $! $DURATION
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

# 2. MOVING USERS (Fig. 14): fixed u64/c1000, users migrate across edges every 5 epochs
run_scalability_moving_users() {
    echo "🏁 STARTING MOVING-USERS TEST..."
    USERS_LIST=("64")
    COLLECTIONS_LIST=("1000")

    echo "🏁 Starting experiment sequence..."

    for CONSISTENCY_MODE in "${TARGET_MODES[@]}"; do

      echo "##########################################################"
      echo "🔷 SWITCHING MODE: $CONSISTENCY_MODE"
      echo "##########################################################"

      for USERS in "${USERS_LIST[@]}"; do
        for COLLECTIONS in "${COLLECTIONS_LIST[@]}"; do
          for SEED in "${SEEDS[@]}"; do

            calculate_thresholds "$USERS" "$COLLECTIONS"

            echo "🚀 [SCALABILITY MOVING] Mode=$CONSISTENCY_MODE, U=$USERS, C=$COLLECTIONS, Seed=$SEED (L=$L_VAL F=$F_VAL)"

            # 1. Generate the experiment setup
            python3 test_generator.py --seed "$SEED" --n_collections "$COLLECTIONS" --n_users "$USERS" --fn_per_round "$FN_ROUND"
            SETUP_FILE="tests/setup_experiment_${SEED}_users_${USERS}_collections_${COLLECTIONS}.json"

            # 2. Update node configs and clean up
            flush_remote_nodes "$F_VAL" "$L_VAL"

            # 3. Create the collections
            echo "⏳ Creating data ($CONSISTENCY_MODE)..."
            ./create "$SETUP_FILE" "$CONSISTENCY_MODE" > create.log 2>&1
            echo "✅ Data creation completed."

            # Drop the creation-phase logs
            rm results/results_log_2000_*.csv 2>/dev/null

            # 4. Run the workload (20 epochs x 15s = 300s)
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

# 3. DENSITY (Fig. 12): fixed u64/c100, varying state operations per function
run_density() {
    echo "🏁 STARTING DENSITY TEST (varying state operations per function)..."
    FIXED_USERS="64"
    FIXED_COLLECTIONS="100"
    ACCESSES_LIST=("1" "2" "4" "6" "8" "10")

    for CONSISTENCY_MODE in "${TARGET_MODES[@]}"; do

      NUM_ROUNDS=10
      if [ "$CONSISTENCY_MODE" == "sequential" ]; then
          NUM_ROUNDS=15
      fi

      for ACC in "${ACCESSES_LIST[@]}"; do
        for SEED in "${SEEDS[@]}"; do

            calculate_thresholds "$FIXED_USERS" "$FIXED_COLLECTIONS"

            echo "🚀 [DENSITY] Mode=$CONSISTENCY_MODE, Accesses=$ACC, Seed=$SEED (L=$L_VAL F=$F_VAL)"

            python3 test_generator.py --seed "$SEED" --n_collections "$FIXED_COLLECTIONS" --n_users "$FIXED_USERS" --fn_per_round "$FN_ROUND"
            SETUP_FILE="tests/setup_experiment_${SEED}_users_${FIXED_USERS}_collections_${FIXED_COLLECTIONS}.json"

            flush_remote_nodes "$F_VAL" "$L_VAL"

            echo "⏳ Creating data ($CONSISTENCY_MODE)..."
            ./create "$SETUP_FILE" "$CONSISTENCY_MODE" "$ACC" > create.log 2>&1
            echo "✅ Data creation completed."

            rm results/results_log_*.csv 2>/dev/null

            ./user "$SETUP_FILE" "$ACC" "$NUM_ROUNDS" > user.log 2>&1 &

            DURATION=$(( NUM_ROUNDS * 15 ))
            show_progress $! $DURATION
            wait $!

            LOG_ID="density_mode_${CONSISTENCY_MODE}_acc${ACC}_s${SEED}"
            copy_logs "${TIMESTAMP}_${LOG_ID}"

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
    echo "❌ Unknown experiment type: $EXP_TYPE (use 'scalability', 'density' or 'moving')"
    exit 1
fi

echo "⏳ Aggregating results..."
python3 csv_aggregator.py results
echo "🎉 ALL TESTS COMPLETED."
