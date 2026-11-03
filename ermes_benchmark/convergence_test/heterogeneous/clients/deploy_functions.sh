#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
    echo "Usage: $0 <serverless-functions-path> <registry-ip> <registry-port>" >&2
    exit 1
fi

SERVERLESS_FUNCTIONS_PATH="$1"
REGISTRY_IP="$2"
REGISTRY_PORT="$3"
FUNCTIONS_PATH="${SERVERLESS_FUNCTIONS_PATH}/functions"

if [[ ! -d "${FUNCTIONS_PATH}" ]]; then
    echo "Missing serverless functions directory: ${FUNCTIONS_PATH}" >&2
    exit 1
fi
if ! command -v ermes-cli >/dev/null 2>&1; then
    echo "ermes-cli is required to deploy serverless functions." >&2
    exit 1
fi

FUNCTION_SOURCES=(
    auth_function.go
    functionCreateCollection.go
    functionReadCollection.go
    functionReadTwoCollections.go
    functionWriteCollection.go
    functionWriteTwoCollections.go
)

for source in "${FUNCTION_SOURCES[@]}"; do
    if [[ ! -f "${FUNCTIONS_PATH}/${source}" ]]; then
        echo "Missing serverless function source: ${FUNCTIONS_PATH}/${source}" >&2
        exit 1
    fi
done

generated_directories=()
cleanup() {
    for directory in "${generated_directories[@]}"; do
        rm -rf "${FUNCTIONS_PATH}/${directory}"
    done
}
trap cleanup EXIT

for source in "${FUNCTION_SOURCES[@]}"; do
    generated_directories+=("${source%.go}")
done

echo "Compiling and deploying ${#FUNCTION_SOURCES[@]} serverless functions..."
(
    cd "${FUNCTIONS_PATH}"
    ${HOME}/go/bin/ermes-cli compile "${FUNCTION_SOURCES[@]}" -dw -i "${REGISTRY_IP}" -p "${REGISTRY_PORT}"
)

echo "Serverless functions deployed to ${REGISTRY_IP}:${REGISTRY_PORT}."
