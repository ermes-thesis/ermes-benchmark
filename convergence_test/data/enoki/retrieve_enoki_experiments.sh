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
zip -r ./cloud_state/cloud_state.zip cloud-write.csv cloud-read.csv

echo "Cloud experiments retrieved and zipped successfully in cloud_state/cloud_state.zip"

# Remove the files after zipping
# rm cloud-write.csv cloud-read.csv

# Retrieve the replicated experiments
for experiment in "${REPLICATED_EXPERIMENTS[@]}"; do
    if [[ "$experiment" == "replicated-write.csv" ]]; then
        scp -o ProxyJump="$JUMP_HOST" "$WRITE_HOST:/opt/enoki/$experiment" "./$experiment"
    else
        scp -o ProxyJump="$JUMP_HOST" "$READ_HOST:/opt/enoki/$experiment" "./$experiment"
    fi
done

# Zip the files
zip -r ./replicated_state/replicated_state.zip replicated-write.csv replicated-read.csv

echo "Replicated experiments retrieved and zipped successfully in replicated_state/replicated_state.zip"

# Remove the files after zipping
# rm replicated-write.csv replicated-read.csv