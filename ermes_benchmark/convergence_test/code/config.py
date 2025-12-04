data_dir = '../data/'

out_dir = '../output_img/'

log_search_key = 'DEFAULT-STRONG-POLICY, transition to idle state'  # 'DEFAULT-STRONG-POLICY, transition to decision state'

messages_log_strings = [
    # collection discoverer
    ('Received remote access request', 'Remote Access'),
    ('Received update propagation request', 'Update Propagation'),
    ('Received collection creation request', 'Collection Creation'),
    ('Received group update propagation request', 'Group Update Propagation'),
    ('Received new collection creation request', 'New Collection Creation'),
    ('Received collection removal request', 'Collection Removal'),
    ('Received remote collection set request', 'Remote Collection Set'),
    # migration manager
    ('New gossip message received through HTTP request', 'Gossip Message'),
    ('New collection received through HTTP request', 'Collection Received'),
    ('New collection request info message received through HTTP request', 'Collection Request Info'),
    # metadata manager
    ('Received group update new request for metadata', 'Group Update Metadata'),
    ('Received group update propagation request', 'Group Update Propagation Request'),
    ('Received metadata creation request', 'Metadata Creation'),
    ('Received metadata deletion request', 'Metadata Deletion'),
    ('Received collection lookup request', 'Collection Lookup'),
    # scheduler
    ("Received function invocation request", "Function Invocation"),
    ("Received offloaded function invocation request", "Offloaded Function Invocation"),
]

ignored_functions = ['functionCreateCollections', 'functionCreateSeqCollections']
default_address = '10.10.101.'
default_port = ':12345'

eq_state = {
    'full_traversal': {
        'functionUseSeqCollections-10.10.101.51:12345': '10.10.101.51:12345',
        'functionReadSeqCollections-10.10.101.54:12345': '10.10.101.54:12345',
    },
    'bottom_up': {
        'functionUseSeqCollections-10.10.101.50:12345': '10.10.101.50:12345',
        'functionUseSeqCollections-10.10.101.51:12345': '10.10.101.51:12345',
        'functionUseSeqCollections-10.10.101.52:12345': '10.10.101.52:12345',
        'functionUseSeqCollections-10.10.101.53:12345': '10.10.101.53:12345',
        'functionUseSeqCollections-10.10.101.54:12345': '10.10.101.54:12345',
        'functionReadSeqCollections-10.10.101.57:12345': '10.10.101.57:12345',
    },
    'top_down': {
        'functionUseSeqCollections-10.10.101.57:12345': '10.10.101.57:12345',
        'functionReadSeqCollections-10.10.101.50:12345': '10.10.101.50:12345',
        'functionReadSeqCollections-10.10.101.51:12345': '10.10.101.51:12345',
        'functionReadSeqCollections-10.10.101.52:12345': '10.10.101.52:12345',
        'functionReadSeqCollections-10.10.101.53:12345': '10.10.101.53:12345',
        'functionReadSeqCollections-10.10.101.54:12345': '10.10.101.54:12345',
    },
    'conflict_1': {
        'writeCollection-10.10.101.51:12345': '10.10.101.57:12345',
        'writeCollection-10.10.101.54:12345': '10.10.101.57:12345',
        'readCollection-10.10.101.51:12345': '10.10.101.51:12345',
        'readCollection-10.10.101.54:12345': '10.10.101.54:12345',
    },
    'conflict_2': {
        'writeTwoCollections-10.10.101.51:12345': '10.10.101.57:12345',
        'writeTwoCollections-10.10.101.54:12345': '10.10.101.57:12345',
        'readTwoCollections-10.10.101.51:12345': '10.10.101.51:12345',
        'readTwoCollections-10.10.101.54:12345': '10.10.101.54:12345',
    }
}

tree = {
    57: [56, 55],
    56: [52, 53, 54],
    55: [50, 51],
}
