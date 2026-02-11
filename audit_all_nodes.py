import json
from collections import defaultdict
from typing import Dict, List, Any

# Load the node library
with open('backend/data/node_library.json', 'r', encoding='utf-8') as f:
    lib = json.load(f)

# Comprehensive audit
total_nodes = sum(len(nodes) for nodes in lib.values())
print(f"=== NODE LIBRARY AUDIT ===")
print(f"Total Categories: {len(lib)}")
print(f"Total Nodes: {total_nodes}\n")

# Analysis metrics
issues = {
    'no_inputs': [],
    'no_outputs': [],
    'missing_types': [],
    'inconsistent_naming': [],
    'missing_descriptions': [],
    'duplicate_ids': defaultdict(list)
}

# Track all node IDs to find duplicates
all_ids = []

# Analyze each category
for category, nodes in lib.items():
    print(f"\n{'='*60}")
    print(f"Category: {category} ({len(nodes)} nodes)")
    print(f"{'='*60}")
    
    for idx, node in enumerate(nodes):
        node_id = node.get('id', 'UNKNOWN')
        all_ids.append((category, idx, node_id))
        
        # Check for issues
        inputs = node.get('inputs', [])
        outputs = node.get('outputs', [])
        
        if not inputs:
            issues['no_inputs'].append(f"{category}/{node_id}")
        
        if not outputs:
            issues['no_outputs'].append(f"{category}/{node_id}")
        
        # Check input/output type definitions
        for inp in inputs:
            if 'types' not in inp and inp.get('type') == 'handle':
                issues['missing_types'].append(f"{category}/{node_id}/input/{inp.get('name')}")
        
        for out in outputs:
            if 'types' not in out:
                issues['missing_types'].append(f"{category}/{node_id}/output/{out.get('name')}")
        
        # Check descriptions
        if not node.get('description'):
            issues['missing_descriptions'].append(f"{category}/{node_id}")
    
    # Show sample nodes from this category
    if nodes:
        sample = nodes[0]
        print(f"\nSample Node: {sample.get('id')}")
        print(f"  Inputs: {len(sample.get('inputs', []))}")
        print(f"  Outputs: {len(sample.get('outputs', []))}")

# Find duplicates
from collections import Counter
id_counts = Counter([node_id for _, _, node_id in all_ids])
duplicates = {k: v for k, v in id_counts.items() if v > 1}

if duplicates:
    print(f"\n{'='*60}")
    print("DUPLICATE NODE IDs FOUND:")
    print(f"{'='*60}")
    for node_id, count in duplicates.items():
        print(f"  {node_id}: {count} occurrences")
        locations = [(cat, idx) for cat, idx, nid in all_ids if nid == node_id]
        for cat, idx in locations:
            print(f"    - {cat}[{idx}]")
        issues['duplicate_ids'][node_id] = locations

# Print summary
print(f"\n{'='*60}")
print("ISSUE SUMMARY:")
print(f"{'='*60}")
print(f"Nodes with no inputs: {len(issues['no_inputs'])}")
print(f"Nodes with no outputs: {len(issues['no_outputs'])}")
print(f"Ports missing type definitions: {len(issues['missing_types'])}")
print(f"Nodes missing descriptions: {len(issues['missing_descriptions'])}")
print(f"Duplicate node IDs: {len(issues['duplicate_ids'])}")

# Save detailed report
with open('node_audit_report.json', 'w', encoding='utf-8') as f:
    json.dump(issues, f, indent=2, ensure_ascii=False)

print(f"\nDetailed report saved to: node_audit_report.json")

# Category breakdown
print(f"\n{'='*60}")
print("NODES PER CATEGORY:")
print(f"{'='*60}")
for category in sorted(lib.keys()):
    print(f"  {category}: {len(lib[category])} nodes")
