#!/usr/bin/env bash
# Helpers shared by the VM-cluster experiments. Each vm/run_*.sh sources this
# file, which loads vm/config.sh and moves into vm/: binaries go to vm/bin/,
# client results to vm/results/<timestamp>/ and node logs to vm/logs/.
#
# Every step follows run_enoki_comparison.sh, the reference VM experiment.
# Like that script, the runners do not use `set -e`: cleaning a fresh remote
# directory or killing a non-existent process returns a non-zero status there.

# shellcheck source=vm/config.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/config.sh"
cd -- "${VM_DIR}" || exit 1

# vm_ssh <ip> <command>
vm_ssh() {
    local ip="$1"; shift
    ssh $JUMP "${SSH_USER}@${ip}" "$@"
}

# build_clients <client-dir>...  (read_write is installed as bin/read-write)
build_clients() {
    local client status=0
    mkdir -p bin
    for client in "$@"; do
        env GOOS=linux GOARCH=amd64 go build -C "${CLIENTS_DIR}/${client}" \
            -ldflags="-s -w" -o "${VM_DIR}/bin/${client//_/-}" . || status=1
    done
    return "${status}"
}

# kill_stale <ip> <process>...
kill_stale() {
    local ip="$1" process; shift
    for process in "$@"; do
        vm_ssh "${ip}" "sudo pkill -f ${process} || true"
    done
}

# clean_remote <ip>...  (creates REMOTE_PATH and removes old logs and CSVs)
clean_remote() {
    local ip
    for ip in "$@"; do
        vm_ssh "${ip}" "mkdir -p ${REMOTE_PATH}; cd ${REMOTE_PATH}; rm -f *.log *.csv"
    done
}

# Writes CLIENT_CONFIG: vm/config.yaml with the GTP address moved to SUBNET.
render_client_config() {
    CLIENT_CONFIG="$(mktemp)"
    trap 'rm -f "${CLIENT_CONFIG}"' EXIT
    sed -E "s#[0-9]+\.[0-9]+\.[0-9]+(\.${GTP_OCTET}:${GTP_PORT})#${SUBNET}\1#" \
        "${VM_DIR}/config.yaml" > "${CLIENT_CONFIG}"
}

# upload <ip> <binary>...  (binaries from bin/ plus the rendered config.yaml)
upload() {
    local ip="$1" binary; shift
    local binaries=()
    for binary in "$@"; do binaries+=("bin/${binary}"); done
    [[ -n "${CLIENT_CONFIG:-}" ]] || render_client_config
    scp $JUMP -q "${binaries[@]}" "${SSH_USER}@${ip}:${REMOTE_PATH}"
    scp $JUMP -q "${CLIENT_CONFIG}" "${SSH_USER}@${ip}:${REMOTE_PATH}/config.yaml"
}

flush_ermes() {
    ANSIBLE_CONFIG="${ERMES_DEPLOY_PATH}/ansible.cfg" \
        ansible-playbook "${ERMES_DEPLOY_PATH}/flush-ermes-nodes.yml"
}

# download_results <ip>...  Sets TIMESTAMP and RESULTS_DIR, fetches the client
# logs and CSVs of every client VM, then the Ermes node logs into ./logs.
download_results() {
    local ip
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    RESULTS_DIR="./results/${TIMESTAMP}"
    mkdir -p "${RESULTS_DIR}"
    echo "   -> Destination folder: ${RESULTS_DIR}"

    for ip in "$@"; do
        scp $JUMP -q "${SSH_USER}@${ip}:${REMOTE_PATH}/*.log" "${RESULTS_DIR}/"
        scp $JUMP -q "${SSH_USER}@${ip}:${REMOTE_PATH}/*.csv" "${RESULTS_DIR}/"
    done

    echo "📥 Downloading the infrastructure logs..."
    "${ERMES_DEPLOY_PATH}/scripts/download_logs.sh"
}

# archive_results <data-subdir> <zip-name> <file>...
archive_results() {
    local destination="${DATA_DIR}/$1" zip_name="$2"; shift 2

    if ! command -v zip >/dev/null 2>&1; then
        echo "⚠️  'zip' command not found. Cannot compress the files."
        return 1
    fi
    mkdir -p "${destination}"
    if zip -q -j "${destination}/${zip_name}" "$@"; then
        echo "✅ Archive created: ${zip_name}"
    else
        echo "❌ Error while creating the zip."
        return 1
    fi
}
