import os

data_dir = '../data/'

out_dir = '../output_img/'

# String searched in the node logs to extract policy-transition timestamps
log_search_key = 'DEFAULT-STRONG-POLICY, transition to idle state'

# Setup-phase functions, excluded from the plots
ignored_functions = ['functionCreateCollections', 'functionCreateSeqCollections']

# Cluster subnet: node addresses are "<subnet>.<last-octet>:<port>".
# Override with the ERMES_SUBNET environment variable.
default_address = os.environ.get('ERMES_SUBNET', '10.10.101') + '.'
default_port = ':12345'

# Node domains, keyed by the last octet of the node address.
# Must stay aligned with the ermes-deploy inventories.
domains = {
    77: 'IT',
    75: 'IT/Rome',
    76: 'IT/Milan',
    70: 'IT/Rome/Edge1',
    71: 'IT/Rome/Edge2',
    72: 'IT/Milan/Edge1',
    73: 'IT/Milan/Edge2',
    74: 'IT/Milan/Edge3',
}
