
NUM_USERS=$1
NUM_COLLECTIONS=$2
SETUP_FILE=$3
WRITE_PIDS=()
# Ciclo da 0 a NUM_USERS - 1

for (( i=0; i<NUM_USERS; i++ )); do
    target="user_$i"

    ./user $SETUP_FILE $target > $target.log 2>&1 &

    CURRENT_PID=$!
    WRITE_PIDS+=($CURRENT_PID)
    echo "      Write avviato verso ${target} (PID: $CURRENT_PID)"
done

echo "⏳ Test in corso... (Premi Ctrl+C per interrompere)"

# Attesa di tutti i processi WRITE
for PID in "${WRITE_PIDS[@]}"; do
    wait $PID
done

python3 csv_aggregator.py . aggregated_results_users_${NUM_USERS}_collections_${NUM_COLLECTIONS}.csv
