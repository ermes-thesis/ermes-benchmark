import os

data_dir = '../data/'

out_dir = '../output_img/'

# String searched in the node logs to extract policy-transition timestamps
log_search_key = 'DEFAULT-STRONG-POLICY, transition to idle state'

# Setup-phase functions, excluded from the plots
ignored_functions = ['functionCreateCollections', 'functionCreateSeqCollections']

# Cluster subnet: node addresses are "<subnet>.<last-octet>:<port>".
# Override with the ERMES_SUBNET environment variable (same variable and
# default as clients/vm/config.sh).
default_address = os.environ.get('ERMES_SUBNET', '10.10.101') + '.'
default_port = ':12345'

# ---------------------------------------------------------------------------
# Node domains, keyed by the last octet of the node address. The plots use them
# to label each client with the domain of the node it is connected to.
# ---------------------------------------------------------------------------

# Current VM cluster: must match the NODE_<DOMAIN> variables in
# clients/vm/config.sh (ermes-deploy inventories/stateful).
vm_domains = {
    57: 'IT',
    55: 'IT/Rome',
    56: 'IT/Milan',
    50: 'IT/Rome/TorVergata',
    51: 'IT/Rome/LaSapienza',
    52: 'IT/Milan/Bocconi',
    53: 'IT/Milan/UNIMI',
    54: 'IT/Milan/POLIMI',
}

# Previous VM cluster (same tree, 20 octets higher): the archives in
# data/replication, data/conflict_1 and data/conflict_eventual were collected
# there. Labels are kept as they were for those figures.
legacy_vm_domains = {
    77: 'IT',
    75: 'IT/Rome',
    76: 'IT/Milan',
    70: 'IT/Rome/Edge1',
    71: 'IT/Rome/Edge2',
    72: 'IT/Milan/Edge1',
    73: 'IT/Milan/Edge2',
    74: 'IT/Milan/Edge3',
}

# The two octet ranges do not overlap, so every VM archive resolves correctly.
domains = {**legacy_vm_domains, **vm_domains}

# Heterogeneous deployment: must match CLOUD_NODE_IP/EDGE_NODE_IP and
# CLOUD_GEOLOCATION/EDGE_GEOLOCATION in clients/heterogeneous/config.sh.
heterogeneous_domains = {
    134: 'SOLA4',      # cloud node (amd64)
    243: 'SOLA4/PI',   # edge node (Raspberry Pi, aarch64)
}
