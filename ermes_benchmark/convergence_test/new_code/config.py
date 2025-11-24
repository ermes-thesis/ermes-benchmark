relative_files = [
    '../data/full_traversal.zip',
    '../data/full_traversal.zip',
]

out_dir = '../output_img_new/full_traversal_analysis_newcode/'

log_search_key = 'DEFAULT-STRONG-POLICY, transition to idle state' #'DEFAULT-STRONG-POLICY, transition to decision state' 

messages_log_strings = [
    #collection discoverer
    'Received remote access request',
    'Received update propagation request',
    'Received group update propagation request',
    'Received new collection creation request',
    'Received collection removal request',
    'Received remote collection set request',
    #migration manager
    'New gossip message received through HTTP request',
    'New collection received through HTTP request',
    
    
]

ignored_functions = ['functionCreateCollections', 'functionCreateSeqCollections']
default_address = '10.10.101.'
default_port = ':12345'

eq_map = {
    'functionUseSeqCollections-10.10.101.51:12345': '10.10.101.51:12345',
    'functionReadSeqCollections-10.10.101.54:12345': '10.10.101.54:12345',
}

tree = {
    57: [56, 55],
    56: [52, 53, 54],
    55: [50, 51],
}
