import js2py
import multiprocessing
import traceback
from typing import Any, Dict, Optional

def _execute_python_restricted(code: str, inputs: Dict[str, Any], output_dict: Dict[str, Any]):
    """Executes Python code in a restricted global environment."""
    safe_globals = {
        "__builtins__": {
            "print": print,
            "len": len,
            "range": range,
            "dict": dict,
            "list": list,
            "set": set,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "abs": abs,
            "sum": sum,
            "min": min,
            "max": max,
        },
        "inputs": inputs
    }
    try:
        exec(code, safe_globals)
        output_dict["result"] = safe_globals.get("output")
        output_dict["success"] = True
    except Exception as e:
        output_dict["success"] = False
        output_dict["error"] = str(e)

def _execute_js_restricted(code: str, inputs: Dict[str, Any], output_dict: Dict[str, Any]):
    """Executes JavaScript code using js2py."""
    try:
        context = js2py.EvalJs()
        context.inputs = inputs
        # User code should set 'output' variable
        context.execute(code)
        output_dict["result"] = context.output
        output_dict["success"] = True
    except Exception as e:
        output_dict["success"] = False
        output_dict["error"] = str(e)

class Sandbox:
    """
    Runs user-provided code (Python/JS) in a separate process with limited globals.
    """
    @staticmethod
    async def run_python(code: str, inputs: Dict[str, Any], timeout: int = 5) -> Dict[str, Any]:
        return await Sandbox._run_in_process(_execute_python_restricted, code, inputs, timeout)

    @staticmethod
    async def run_js(code: str, inputs: Dict[str, Any], timeout: int = 5) -> Dict[str, Any]:
        return await Sandbox._run_in_process(_execute_js_restricted, code, inputs, timeout)

    @staticmethod
    async def _run_in_process(target_func, code, inputs, timeout):
        manager = multiprocessing.Manager()
        output_dict = manager.dict()
        
        process = multiprocessing.Process(target=target_func, args=(code, inputs, output_dict))
        process.start()
        process.join(timeout=timeout)
        
        if process.is_alive():
            process.terminate()
            return {"success": False, "error": f"Execution timed out after {timeout}s"}
            
        return dict(output_dict)

sandbox = Sandbox()
