import json

# Load the node library
with open('backend/data/node_library.json', 'r', encoding='utf-8') as f:
    lib = json.load(f)

# Check Tyboo category
tyboo_nodes = lib.get('Tyboo', [])
print(f"Total Tyboo nodes: {len(tyboo_nodes)}\n")

for i, node in enumerate(tyboo_nodes):
    node_id = node.get('id', 'UNKNOWN')
    label = node.get('label', 'UNKNOWN')
    num_inputs = len(node.get('inputs', []))
    num_outputs = len(node.get('outputs', []))
    print(f"{i}: {node_id} ({label}) - Inputs: {num_inputs}, Outputs: {num_outputs}")

# Find duplicates
from collections import Counter
ids = [n.get('id') for n in tyboo_nodes]
duplicates = {k: v for k, v in Counter(ids).items() if v > 1}
if duplicates:
    print(f"\n⚠️ DUPLICATES FOUND: {duplicates}")
