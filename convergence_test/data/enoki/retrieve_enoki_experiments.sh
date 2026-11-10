JUMP_HOST="sola5remote"
WRITE_HOST="ubuntu@10.10.101.59"
READ_HOST="ubuntu@10.10.101.60"

CLOUD_EXPERIMENTS=("cloud-write.csv" "cloud-read.csv")
REPLICATED_EXPERIMENTS=("replicated-write.csv" "replicated-read.csv")

# Retrieve the cloud experiments
for experiment in "${CLOUD_EXPERIMENTS[@]}"; do
    if [[ "$experiment" == "cloud-write.csv" ]]; then
        scp -o ProxyJump="$JUMP_HOST" "$WRITE_HOST:/opt/enoki/$experiment" "./$experiment"
    else
        scp -o ProxyJump="$JUMP_HOST" "$READ_HOST:/opt/enoki/$experiment" "./$experiment"
    fi
done

# Zip the files
CURRENT_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
zip -r ./cloud_state/cloud_state_${CURRENT_TIMESTAMP}.zip cloud-write.csv cloud-read.csv

echo "Cloud experiments retrieved and zipped successfully in cloud_state/cloud_state_${CURRENT_TIMESTAMP}.zip"

# Remove temporary extracted/downloaded files; the archive is the source of truth.
rm cloud-write.csv cloud-read.csv

# Retrieve the replicated experiments
for experiment in "${REPLICATED_EXPERIMENTS[@]}"; do
    if [[ "$experiment" == "replicated-write.csv" ]]; then
        scp -o ProxyJump="$JUMP_HOST" "$WRITE_HOST:/opt/enoki/$experiment" "./$experiment"
    else
        scp -o ProxyJump="$JUMP_HOST" "$READ_HOST:/opt/enoki/$experiment" "./$experiment"
    fi
done

# Zip the files
zip -r ./replicated_state/replicated_state_${CURRENT_TIMESTAMP}.zip replicated-write.csv replicated-read.csv

echo "Replicated experiments retrieved and zipped successfully in replicated_state/replicated_state_${CURRENT_TIMESTAMP}.zip"

# Remove temporary extracted/downloaded files; the archive is the source of truth.
rm replicated-write.csv replicated-read.csv