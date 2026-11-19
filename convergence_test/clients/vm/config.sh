#!/usr/bin/env bash
# Configuration shared by every experiment running on the VM cluster
# (ermes-deploy `inventories/stateful`). Sourced by the vm/run_*.sh scripts.
#
# Environment overrides:
#   ERMES_SUBNET       first three octets of the cluster subnet (default: 10.10.101)
#   ERMES_SSH_USER     SSH user on the cluster machines (default: ubuntu)
#   ERMES_JUMP_HOST    SSH bastion, alias or user@host (default: sola5remote);
#                      set it to an empty string for direct connections
#   ERMES_DEPLOY_PATH  path of the ermes-deploy checkout

VM_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CLIENTS_DIR="$(cd -- "${VM_DIR}/.." && pwd)"   # Go client sources
DATA_DIR="${CLIENTS_DIR}/../data"              # ZIP archives read by code/

SUBNET="${ERMES_SUBNET:-10.10.101}"
SSH_USER="${ERMES_SSH_USER:-ubuntu}"
JUMP_HOST="${ERMES_JUMP_HOST-sola5remote}"
JUMP="${JUMP_HOST:+-J ${JUMP_HOST}}"
ERMES_DEPLOY_PATH="${ERMES_DEPLOY_PATH:-${CLIENTS_DIR}/../../../ermes-deploy}"

# --- Machines (must match ermes-deploy/inventories/stateful) ---
# Central node hosting the GTP; vm/config.yaml is rewritten with ${SUBNET}.
GTP_OCTET="58"
GTP_PORT="8081"

# Client VMs (inventory names client-1 and client-2)
CLIENT1_IP="${SUBNET}.59"
CLIENT2_IP="${SUBNET}.60"

# Ermes nodes, named after their domain (inventories/stateful/group_vars/nodes.yml)
ERMES_NODE_PORT="12345"
NODE_IT="${SUBNET}.57:${ERMES_NODE_PORT}"            # IT (cloud)
NODE_ROME="${SUBNET}.55:${ERMES_NODE_PORT}"          # IT/Rome
NODE_MILAN="${SUBNET}.56:${ERMES_NODE_PORT}"         # IT/Milan
NODE_TORVERGATA="${SUBNET}.50:${ERMES_NODE_PORT}"    # IT/Rome/TorVergata
NODE_LASAPIENZA="${SUBNET}.51:${ERMES_NODE_PORT}"    # IT/Rome/LaSapienza
NODE_BOCCONI="${SUBNET}.52:${ERMES_NODE_PORT}"       # IT/Milan/Bocconi
NODE_UNIMI="${SUBNET}.53:${ERMES_NODE_PORT}"         # IT/Milan/UNIMI
NODE_POLIMI="${SUBNET}.54:${ERMES_NODE_PORT}"        # IT/Milan/POLIMI

# Collection name used by every VM experiment
COLLECTION_NAME="colName"
