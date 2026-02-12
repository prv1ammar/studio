import json

with open("NODE_AUDIT_REPORT.json", "r") as f:
    report = json.load(f)

for node in report["details"]:
    if "hardcoded_secrets" in node["issues"]:
        print(f"FOUND SECRET IN: {node['file']}")
        print(f"Node: {node['node']}")
