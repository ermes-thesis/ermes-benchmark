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
ERMES_CLI="${ERMES_CLI:-${HOME}/go/bin/ermes-cli}"

if [[ ! -d "${FUNCTIONS_PATH}" ]]; then
    echo "Missing serverless functions directory: ${FUNCTIONS_PATH}" >&2
    exit 1
fi
if [[ ! -x "${ERMES_CLI}" ]]; then
    echo "ermes-cli not found or not executable: ${ERMES_CLI}" >&2
    exit 1
fi

FUNCTION_SOURCES=(
    functions/auth_function.go
    functions/functionCreateCollection.go
    functions/functionReadCollection.go
    functions/functionReadTwoCollections.go
    functions/functionWriteCollection.go
    functions/functionWriteTwoCollections.go
)

for source in "${FUNCTION_SOURCES[@]}"; do
    if [[ ! -f "${SERVERLESS_FUNCTIONS_PATH}/${source}" ]]; then
        echo "Missing serverless function source: ${SERVERLESS_FUNCTIONS_PATH}/${source}" >&2
        exit 1
    fi
done

generated_directories=()
cleanup() {
    for directory in "${generated_directories[@]}"; do
        rm -rf "${SERVERLESS_FUNCTIONS_PATH}/${directory}"
    done
}
trap cleanup EXIT

for source in "${FUNCTION_SOURCES[@]}"; do
    base_name="${source##*/}"
    generated_directories+=("${base_name%.go}")
done

echo "Compiling and deploying ${#FUNCTION_SOURCES[@]} serverless functions..."
(
    cd "${SERVERLESS_FUNCTIONS_PATH}"
    "${ERMES_CLI}" compile "${FUNCTION_SOURCES[@]}" -dw -i "${REGISTRY_IP}" -p "${REGISTRY_PORT}"
)

echo "Serverless functions deployed to ${REGISTRY_IP}:${REGISTRY_PORT}."
