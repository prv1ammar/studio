import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(PROJECT_ROOT)

from backend.app.core.engine import engine

# 1. Test Calculator Integration (Scraped Component)
print("--- Testing Calculator Component (Dynamic Load) ---")
calc_config = {
    "id": "calc_test_node",
    "execution_metadata": {
        "module": "lfx.components.utilities.calculator_core.CalculatorComponent"
    },
    "expression": "40 + 2" # The component uses 'expression' attribute
}

try:
    result = engine.execute_dynamic_node(calc_config, "")
    print(f"Calculator Result (Input: 40+2): {result}")
    
    if "42" in str(result) or "42.0" in str(result):
        print("SUCCESS: Calculator output matches expected value.")
    else:
        print("FAILURE: Unexpected output.")

except Exception as e:
    print(f"FAILURE: Exception during execution: {e}")
    import traceback
    traceback.print_exc()

print("\n--- Test Complete ---")
