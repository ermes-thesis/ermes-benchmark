#!/usr/bin/env bash
# Configuration of the heterogeneous deployment (amd64 cloud machine `sola4` +
# aarch64 Raspberry Pi `sola-pi`). Used only by heterogeneous/run_heterogeneous.sh;
# the VM-cluster experiments are configured in ../vm/config.sh.
# Keep CLOUD_NODE_IP:GTP_PORT aligned with GTP_Address in ./config.yaml.

# SSH aliases are resolved by the local ~/.ssh/config.
EDGE_SSH_HOST="sola-pi"
CONFIG_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# Node addresses and service ports.
CLOUD_NODE_IP="10.79.10.134"
EDGE_NODE_IP="10.79.10.243"
ERMES_NODE_PORT="12345"
GTP_PORT="8081"
FUNCTION_REGISTRY_PORT="8080"

# Local paths.
REMOTE_PATH="heterogeneous"
SERVERLESS_FUNCTIONS_PATH="${SERVERLESS_FUNCTIONS_PATH:-${CONFIG_DIR}/../../../serverless_functions}"
ERMES_DEPLOY_PATH="${ERMES_DEPLOY_PATH:-${CONFIG_DIR}/../../../../ermes-deploy}"

# Experiment parameters.
COLLECTION_NAME="heterogeneous_collection"
CREATE_CLIENT_ID="0"
READ_WRITE_CLIENT_ID="54321"
CLOUD_GEOLOCATION="SOLA4"
EDGE_GEOLOCATION="SOLA4/PI"
CONSISTENCY="sequential"
FLUSH_ERMES="false"
DEPLOY_FUNCTIONS="true"
