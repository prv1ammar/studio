# Node Property Specification (n8n Alignment)

This document defines the standardized structure for node properties to ensure a consistent experience across the Studio.

## 1. Property Core Structure

All nodes should define their configuration using an array of `properties`.

| Field | Type | Description |
| :--- | :--- | :--- |
| `displayName` | `string` | The label shown to the user in the UI. |
| `name` | `string` | The parameter name used in the backend `execute()` method. |
| `type` | `string` | The data type (see below). |
| `default` | `any` | The default value when the node is first added. |
| `description` | `string` | A brief explanation shown below the field. |
| `required` | `boolean` | Whether the field must be filled. |
| `placeholder` | `string` | Ghost text shown when the field is empty. |
| `options` | `array` | Required for `options` type. List of `{ name, value }`. |
| `displayOptions`| `object` | Logic for showing/hiding the field. |

## 2. Supported Types

| Type | UI Component | Notes |
| :--- | :--- | :--- |
| `string` | Text Input | Standard text field. |
| `number` | Numeric Input | Restricts to numbers. |
| `boolean` | Toggle/Switch | Returns `true`/`false`. |
| `options` | Dropdown | Single selection from a list. |
| `multiOptions` | Multi-select | Multiple selection from a list. |
| `dateTime` | Date/Time Picker | Standard ISO string output. |
| `json` | Code Editor | For raw JSON objects or scripts. |
| `notice` | Info Box | UI-only field for instructions/warnings. |

## 3. Dynamic Visibility (`displayOptions`)

Fields can be hidden based on the value of other fields.

**Example: Show "Subject" only when operation is "Send"**
```json
{
  "displayName": "Subject",
  "name": "subject",
  "type": "string",
  "displayOptions": {
    "show": {
      "operation": ["send"]
    }
  }
}
```

## 4. The Resource/Operation Pattern

To prevent configuration clutter, nodes with multiple functions must follow the Resource -> Operation pattern.

1.  **Resource**: The entity being acted upon (e.g., "Message", "User", "File").
2.  **Operation**: The action performed on that entity (e.g., "Create", "Delete", "Get").

This allows the UI to filter relevant fields, keeping the inspector clean.

---

## 5. Implementation in Python

```python
class MyNode(BaseNode):
    node_type = "my_service"
    
    properties = [
        {
            "displayName": "Resource",
            "name": "resource",
            "type": "options",
            "options": [
                {"name": "User", "value": "user"},
            ],
            "default": "user",
        },
        {
            "displayName": "Operation",
            "name": "operation",
            "type": "options",
            "displayOptions": {"show": {"resource": ["user"]}},
            "options": [
                {"name": "Create", "value": "create"},
            ],
            "default": "create",
        }
    ]
```
