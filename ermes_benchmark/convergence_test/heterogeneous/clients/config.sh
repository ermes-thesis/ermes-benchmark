#!/usr/bin/env bash

# SSH aliases are resolved by the local ~/.ssh/config.
EDGE_SSH_HOST="sola-pi"

# Replace both placeholders with the nodes' reachable IP addresses.
CLOUD_NODE_IP="10.79.10.134"
EDGE_NODE_IP="10.79.10.243"
ERMES_NODE_PORT="12345"
GTP_HOST="10.79.10.134"
GTP_PORT="8081"

# Paths and experiment parameters.
REMOTE_PATH="heterogeneous"
ERMES_DEPLOY_PATH="<path-to-ermes-deploy-or-empty>"
COLLECTION_NAME="heterogeneous_collection"
CREATE_CLIENT_ID="0"
READ_WRITE_CLIENT_ID="54321"
CLOUD_GEOLOCATION="SOLA4"
EDGE_GEOLOCATION="SOLA4/PI"
CONSISTENCY="sequential"
FLUSH_ERMES="false"
DOWNLOAD_INFRASTRUCTURE_LOGS="false"

# Derived addresses. Keep these out of the runner so deployment changes are
# limited to this file.
CLOUD_NODE_ADDRESS="${CLOUD_NODE_IP}:${ERMES_NODE_PORT}"
EDGE_NODE_ADDRESS="${EDGE_NODE_IP}:${ERMES_NODE_PORT}"
FUNCTION_NODE_ADDRESS="${CLOUD_NODE_ADDRESS}"
GTP_ADDRESS="${GTP_HOST}:${GTP_PORT}"
