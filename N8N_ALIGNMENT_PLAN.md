# Plan: n8n-Style Node Configuration Alignment

This plan outlines the transition from the current heterogeneous node configuration format to a standardized, n8n-inspired property system. This will improve user experience for those transitioning from n8n and ensure consistency across all nodes in the Studio.

## 🎯 Objectives
1.  **Standardize Property Schema**: Use n8n-naming conventions (`displayName`, `name`, `type`, `default`, `displayOptions`).
2.  **Resource/Operation Pattern**: Enforce the pattern where users first select a "Resource" and then an "Operation".
3.  **Dynamic Visibility**: Implement server-side metadata for conditional field visibility (`displayOptions`).
4.  **Legacy Compatibility**: Ensure existing 377 nodes continue to work while being incrementally migrated.

---

## 🏗 Phase 1: Standardized Property Specification
We will define a unified Python schema for node properties that mirrors n8n's `INodeProperties`.

### Proposed Property Structure
```python
{
    "displayName": str,     # Human-readable label
    "name": str,            # Key used in the logic
    "type": str,            # string, number, boolean, options, dateTime, fixedCollection
    "default": any,         # Default value
    "description": str,     # Tooltip/Subtext
    "required": bool,       # Mandatory check
    "options": list,        # For 'options' type: [{"name": "Label", "value": "val"}]
    "displayOptions": dict, # Conditional logic: {"show": {"resource": ["message"]}}
    "placeholder": str,     # UI placeholder
}
```

---

## 🚀 Phase 2: Backend Implementation
1.  **Update `BaseNode`**: Add a `properties` attribute to `BaseNode` in `backend/app/nodes/base.py`.
2.  **Specialized `IntegrationNode`**: Create a subclass specifically for external services (Slack, Gmail, etc.) that pre-defines "Resource" and "Operation" fields.
3.  **Metadata Extraction**: Update `NodeRegistry` to prioritize the new `properties` format over the old `inputs` dict.

---

## 🎨 Phase 3: Frontend Inspector Overhaul
1.  **Conditional Rendering**: Update the right sidebar (`App.jsx`'s Inspector) to evaluate `displayOptions` in real-time.
2.  **Grouping**: Support field grouping to avoid long scrolling lists.
3.  **Component Mapping**: Map property types to specific React components (e.g., `options` -> Searchable Select, `boolean` -> Fancy Toggle).

---

## 🛠 Phase 4: Migration Strategy (The "Big Sync")
Since we have 377+ nodes, we cannot migrate manually.
1.  **Automated Mapping Script**: Create a script `backend/scripts/standardize_node_schemas.py` that:
    *   Converts `display_name` to `displayName`.
    *   Renames `action` to `operation` in integration nodes.
    *   Wraps simple input dicts into the new property list format.
2.  **Component Adapter Update**: Update `LangflowComponentAdapter` to map legacy Langflow `inputs` to the new n8n format dynamically.

---

## 📅 Timeline & Milestones
- **S1 (Core)**: Finalize `BaseNode` property schema and update frontend inspector.
- **S2 (Migration)**: Run the standardization script and verify high-priority nodes (Slack, Gmail).
- **S3 (Polishing)**: Implement advanced n8n features like `fixedCollection` for complex inputs.
