import re
from matplotlib import pyplot as plt
import numpy as np


def plot_stacked_bar_chart(node_map):

    nodes = list(node_map.keys())
    
    def extract_last_octet(ip_str):
        match = re.search(r'(\d+)$', ip_str.split(':')[0])
        return match.group(1) if match else ip_str

    node_labels = [extract_last_octet(node) for node in nodes]

    message_types = sorted({msg for sub in node_map.values() for msg in sub.keys()})
    
    data = {msg: [] for msg in message_types}
    for node in nodes:
        for msg in message_types:
            data[msg].append(node_map[node].get(msg, 0))

    x = np.arange(len(nodes))
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    bottom = np.zeros(len(nodes))
    
    for msg in message_types:
        ax.bar(x, data[msg], bottom=bottom, label=msg)
        bottom += np.array(data[msg])
    
    ax.set_xlabel('Node (last IP octet)')
    ax.set_ylabel('Message Count')
    ax.set_title('Stacked Bar Chart of Messages per Node')
    ax.set_xticks(x)
    ax.set_xticklabels(node_labels, rotation=45, ha='right')
    ax.legend(title='Message Types', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()