#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.sh"

if [[ ! -r "${CONFIG_FILE}" ]]; then
    echo "Missing configuration file: ${CONFIG_FILE}" >&2
    exit 1
fi

# shellcheck source=/dev/null
source "${CONFIG_FILE}"

require_config() {
    local name="$1"
    local value="${!name:-}"
    if [[ -z "${value}" || "${value}" == \<* ]]; then
        echo "Set ${name} in ${CONFIG_FILE} before running the experiment." >&2
        exit 1
    fi
}

for setting in EDGE_SSH_HOST CLOUD_NODE_IP EDGE_NODE_IP ERMES_NODE_PORT GTP_HOST GTP_PORT; do
    require_config "${setting}"
done

if [[ "${DEPLOY_FUNCTIONS}" == "true" ]]; then
    for setting in FUNCTION_REGISTRY_IP FUNCTION_REGISTRY_PORT SERVERLESS_FUNCTIONS_PATH; do
        require_config "${setting}"
    done
fi

if [[ "${CLOUD_NODE_IP}" == "${EDGE_NODE_IP}" ]]; then
    echo "CLOUD_NODE_IP and EDGE_NODE_IP must identify different machines." >&2
    exit 1
fi

BIN_DIR="${SCRIPT_DIR}/bin"
CLOUD_PATH="${SCRIPT_DIR}/${REMOTE_PATH}"
RESULTS_ROOT="${SCRIPT_DIR}/results"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RESULTS_DIR="${RESULTS_ROOT}/${TIMESTAMP}"
SOURCE_ROOT="${SCRIPT_DIR}/../../clients"
CONFIG_NAME="config.yaml"
RUNTIME_CONFIG="$(mktemp)"
trap 'rm -f "${RUNTIME_CONFIG}"' EXIT

edge_ssh() {
    ssh "${EDGE_SSH_HOST}" "$@"
}

echo "[1/6] Building binaries for the heterogeneous deployment..."
mkdir -p "${BIN_DIR}"
env GOOS=linux GOARCH=amd64 go build -C "${SOURCE_ROOT}/create" -ldflags="-s -w" \
    -o "${BIN_DIR}/create" .
env GOOS=linux GOARCH=arm64 go build -C "${SOURCE_ROOT}/read_write" -ldflags="-s -w" \
    -o "${BIN_DIR}/read_write" .

echo "[2/6] Preparing remote directories..."
mkdir -p "${CLOUD_PATH}"
rm -f "${CLOUD_PATH}"/*.log "${CLOUD_PATH}"/*.csv
edge_ssh "mkdir -p '${REMOTE_PATH}' && rm -f '${REMOTE_PATH}'/*.log '${REMOTE_PATH}'/*.csv"
cp "${BIN_DIR}/create" "${CLOUD_PATH}/create"
cp "${SOURCE_ROOT}/${CONFIG_NAME}" "${BIN_DIR}/"
scp -q "${BIN_DIR}/read_write" "${EDGE_SSH_HOST}:${REMOTE_PATH}/"
scp -q "${SOURCE_ROOT}/${CONFIG_NAME}" "${EDGE_SSH_HOST}:${REMOTE_PATH}/"

if [[ "${FLUSH_ERMES}" == "true" ]]; then
    if [[ -z "${ERMES_DEPLOY_PATH}" || "${ERMES_DEPLOY_PATH}" == "<path-to-ermes-deploy-or-empty>" ]]; then
        echo "FLUSH_ERMES=true requires ERMES_DEPLOY_PATH to be configured." >&2
        exit 1
    fi
    echo "[3/6] Flushing Ermes nodes..."
    ANSIBLE_CONFIG="${ERMES_DEPLOY_PATH}/ansible.cfg" \
        ansible-playbook "${ERMES_DEPLOY_PATH}/flush-ermes-nodes.yml"
else
    echo "[3/6] Skipping Ermes flush (FLUSH_ERMES=false)."
fi

if [[ "${DEPLOY_FUNCTIONS}" == "true" ]]; then
    if [[ ! -x "${SCRIPT_DIR}/deploy_functions.sh" ]]; then
        echo "Missing heterogeneous deployment script: ${SCRIPT_DIR}/deploy_functions.sh" >&2
        exit 1
    fi
    echo "[3/6] Compiling and deploying serverless functions..."
    if ! "${SCRIPT_DIR}/deploy_functions.sh" "${SERVERLESS_FUNCTIONS_PATH}" \
        "${FUNCTION_REGISTRY_IP}" "${FUNCTION_REGISTRY_PORT}"; then
        echo "Serverless function deployment failed." >&2
        exit 1
    fi
else
    echo "[3/6] Skipping serverless function deployment (DEPLOY_FUNCTIONS=false)."
fi

echo "[4/6] Creating the collection on the cloud node..."
(
    cd "${CLOUD_PATH}"
    ./create "${CLOUD_NODE_ADDRESS}" "${COLLECTION_NAME}" "${CREATE_CLIENT_ID}" \
        "${CLOUD_GEOLOCATION}" "${CONSISTENCY}" > create.log 2>&1
) &
CREATE_PID=$!
echo "[4/6] Collection creation started (local PID: ${CREATE_PID})."
if ! wait "${CREATE_PID}"; then
    echo "Collection creation failed." >&2
    exit 1
fi
echo "[4/6] Collection created."

echo "[4/6] Starting read_write on the aarch64 edge node..."
edge_ssh "cd '${REMOTE_PATH}' && ./read_write '${FUNCTION_NODE_ADDRESS}' \
'${READ_WRITE_CLIENT_ID}' '${EDGE_GEOLOCATION}' '${COLLECTION_NAME}' > read_write.log 2>&1" &
READ_WRITE_PID=$!
echo "[4/6] Read_write process started (SSH PID: ${READ_WRITE_PID})."
if ! wait "${READ_WRITE_PID}"; then
    echo "Read_write execution failed." >&2
    exit 1
fi
echo "[4/6] Read_write process completed."

echo "[5/6] Downloading experiment results..."
mkdir -p "${RESULTS_DIR}"
if ! cp "${CLOUD_PATH}"/*.log "${CLOUD_PATH}"/*.csv "${RESULTS_DIR}/"; then
    echo "Could not download cloud results." >&2
    exit 1
fi
if ! scp -q "${EDGE_SSH_HOST}:${REMOTE_PATH}/*.log" \
    "${EDGE_SSH_HOST}:${REMOTE_PATH}/*.csv" "${RESULTS_DIR}/"; then
    echo "Could not download edge results." >&2
    exit 1
fi

if [[ "${DOWNLOAD_INFRASTRUCTURE_LOGS}" == "true" ]]; then
    if [[ -z "${ERMES_DEPLOY_PATH}" || "${ERMES_DEPLOY_PATH}" == "<path-to-ermes-deploy-or-empty>" ]]; then
        echo "DOWNLOAD_INFRASTRUCTURE_LOGS=true requires ERMES_DEPLOY_PATH to be configured." >&2
        exit 1
    fi
    "${ERMES_DEPLOY_PATH}/scripts/download_logs.sh"
fi

echo "[6/6] Experiment completed. Results: ${RESULTS_DIR}"
