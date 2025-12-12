
NUM_USERS=$1
NUM_COLLECTIONS=$2
SETUP_FILE=$3
SEED=$4

./user $SETUP_FILE > user.log 2>&1

echo "⏳ Test in corso... (Premi Ctrl+C per interrompere)"

python3 csv_aggregator.py . aggregated_results_users_${NUM_USERS}_collections_${NUM_COLLECTIONS}.csv $SEED
