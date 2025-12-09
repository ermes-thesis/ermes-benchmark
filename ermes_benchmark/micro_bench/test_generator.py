import numpy as np
import json
import os
import argparse


def sample_collection_positions(tree, mu=0, sigma=1.0, n_collections=1, seed=None):
    """
    Sample initial positions for collections in a hierarchical tree using a Gaussian-like distribution.
    
    Args:
        tree (dict): dict parent -> list of children
        mu (float): peak of the Gaussian (level of root)
        sigma (float): standard deviation controlling spread
        n_collections (int): number of collections to place
        seed (int or None): random seed for reproducibility
        
    Returns:
        List of nodes selected for collections
    """
    if seed is not None:
        np.random.seed(seed)
    
    # --- Step 1: compute levels for each node ---
    levels = {}
    
    def assign_levels(node, level):
        levels[node] = level
        for child in tree.get(node, []):
            assign_levels(child, level + 1)

    
    
    # find root (node not appearing as child)
    all_children = set(c for children in tree.values() for c in children)
    all_nodes = set(tree.keys()) | all_children
    root_candidates = list(all_nodes - all_children)
    if not root_candidates:
        raise ValueError("No root found in the tree")
    root = root_candidates[0]
    
    assign_levels(root, 0)

    
    # --- Step 2: compute Gaussian-like weights per node ---
    weights = {node: np.exp(-((level - mu) ** 2) / (2 * sigma ** 2)) 
               for node, level in levels.items()}
    
    # --- Step 3: normalize to probabilities ---
    total_weight = sum(weights.values())
    probs = {node: w / total_weight for node, w in weights.items()}
    
    # --- Step 4: sample nodes ---
    nodes = list(probs.keys())
    probabilities = list(probs.values())
    
    chosen_nodes = np.random.choice(nodes, size=n_collections, replace=True, p=probabilities)
    
    result = {f"collection_{i}": int(node) for i, node in enumerate(chosen_nodes)}

    return result

def assign_users_to_leaf(N_user, tree, seed=None):
    if seed is not None:
        np.random.seed(seed)

    parent_nodes = set(tree.keys())

    child_nodes = set()
    for children in tree.values():
        child_nodes.update(children)

    leaf_nodes = list(child_nodes - parent_nodes)

    # randomly assign users to leaf nodes
    repeats = int(np.ceil(N_user / len(leaf_nodes)))
    assignment_list = leaf_nodes * repeats
    assignment_list = assignment_list[:N_user]

    np.random.shuffle(assignment_list)

    result = {f"user_{i}": int(node) for i, node in enumerate(assignment_list)}

    return result, leaf_nodes

def assign_user_collections(user_assignments, collection_positions, write_prob=0.2, seed=None, function_per_round=50):
    """
    Assegna a ogni user un sottoinsieme di collection (max 50) con diritti read/write.
    
    Args:
        user_assignments (dict): { "user_i": leaf_node }
        collection_positions (dict): { "collection_j": node }
        write_prob (float): probabilità che un accesso sia 'write'
        seed (int or None): random seed
        
    Returns:
        dict: user -> {collection -> right}
    """
    if seed is not None:
        np.random.seed(seed)

    users = list(user_assignments.keys())
    collections = list(collection_positions.keys())

    max_per_user = function_per_round

    user_collection_map = {}

    for user in users:

        # Step 1: random chose collections (linear → uniform)
        chosen = np.random.choice(
            collections,
            size=max_per_user,
            replace= True if len(collections) < max_per_user else False
        )

        # Step 2: assign rights (read/write)
        rights = []
        for col in chosen:
            right = "write" if np.random.rand() < write_prob else "read"
            rights.append({str(col): right})

        user_collection_map[user] = rights

    return user_collection_map


# ---------------- main ----------------
# python3 test_generator.py --seed 123 --n_collections 50 --n_users 10

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Setup experiment generator")

    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    parser.add_argument("--n_collections", type=int, default=20,
                        help="Number of collections")
    parser.add_argument("--n_users", type=int, default=1,
                        help="Number of users")

    args = parser.parse_args()

    seed = args.seed
    n_collections = args.n_collections
    n_users = args.n_users

    tree = {
        57: [56, 55],
        56: [52, 53, 54],
        55: [50, 51],
    }

    write_prob = 0.2

    collection_positions = sample_collection_positions(
        tree,
        mu=0,
        sigma=1.0,
        n_collections=n_collections,
        seed=seed
    )
    print(len(collection_positions), "collections placed.")

    user_assignments, leafs = assign_users_to_leaf(
        n_users,
        tree,
        seed=seed
    )
    print(len(user_assignments), "users assigned.")

    user_collection_map = assign_user_collections(
        user_assignments,
        collection_positions,
        write_prob=write_prob,
        seed=seed
    )

    # ---------------- Save to JSON ----------------
    os.makedirs("tests", exist_ok=True)

    output = {
        "collection_positions": collection_positions,
        "user_assignments": user_assignments,
        "user_collection_map": user_collection_map
    }

    filename = f"tests/setup_experiment_{seed}_users_{n_users}_collections_{n_collections}.json"

    with open(filename, "w") as f:
        json.dump(output, f, indent=4)

    print(f"File saved: {filename}")