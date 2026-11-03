#!/usr/bin/env bash

# SSH aliases are resolved by the local ~/.ssh/config.
EDGE_SSH_HOST="sola-pi"

# Node addresses and service ports.
CLOUD_NODE_IP="10.79.10.134"
EDGE_NODE_IP="10.79.10.243"
ERMES_NODE_PORT="12345"
GTP_PORT="8081"
FUNCTION_REGISTRY_PORT="8080"

# Local paths.
REMOTE_PATH="heterogeneous"
SERVERLESS_FUNCTIONS_PATH="${HOME}/ermes-benchmark/ermes_benchmark/serverless_functions"
ERMES_DEPLOY_PATH="<path-to-ermes-deploy-or-empty>"

# Experiment parameters.
COLLECTION_NAME="heterogeneous_collection"
CREATE_CLIENT_ID="0"
READ_WRITE_CLIENT_ID="54321"
CLOUD_GEOLOCATION="SOLA4"
EDGE_GEOLOCATION="SOLA4/PI"
CONSISTENCY="sequential"
FLUSH_ERMES="false"
DOWNLOAD_INFRASTRUCTURE_LOGS="false"
DEPLOY_FUNCTIONS="true"
