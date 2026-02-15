import typer
import json
import os
import sys
from typing import Optional
from pathlib import Path
import importlib.util

app = typer.Typer(help="Studio CLI: Developer Tools for AI Orchestration")
node_app = typer.Typer(help="Manage and validate custom nodes")
workflow_app = typer.Typer(help="Manage and validate workflows")

app.add_typer(node_app, name="node")
app.add_typer(workflow_app, name="workflow")

@node_app.command("validate")
def validate_node(path: str):
    """
    Check if a Python file is a valid Studio Node.
    """
    typer.echo(f" Validating node at {path}...")
    
    if not os.path.exists(path):
        typer.secho(f" Error: File {path} not found.", fg=typer.colors.RED)
        raise typer.Exit(1)

    try:
        # Dynamic Import
        spec = importlib.util.spec_from_file_location("module.name", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check for BaseNode inheritance
        classes = [cls for name, cls in module.__dict__.items() if isinstance(cls, type)]
        found_node = False
        for cls in classes:
            if any(base.__name__ == "BaseNode" for base in cls.__mro__):
                typer.secho(f" Found valid Node class: {cls.__name__}", fg=typer.colors.GREEN)
                
                # Check for required attributes
                required = ["name", "description", "node_type"]
                for attr in required:
                    if not hasattr(cls, attr):
                        typer.secho(f" Warning: Missing recommended attribute '{attr}' in {cls.__name__}", fg=typer.colors.YELLOW)
                
                found_node = True
        
        if not found_node:
            typer.secho(" Error: No class inheriting from BaseNode found in this file.", fg=typer.colors.RED)
            raise typer.Exit(1)

    except Exception as e:
        typer.secho(f" Critical Error during validation: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

@node_app.command("scaffold")
def scaffold_node(name: str, category: str = "Utilities"):
    """
    Generate a boilerplate Python file for a new node.
    """
    safe_name = name.lower().replace(" ", "_").replace("-", "_")
    class_name = "".join(x.capitalize() for x in name.split()) + "Node"
    
    template = f"""from typing import Any, Dict, Optional
from app.nodes.base import BaseNode
from app.nodes.factory import register_node
from pydantic import BaseModel, Field

class {class_name}Config(BaseModel):
    sample_param: str = Field(default="Hello", description="A sample configuration parameter")

@register_node("{safe_name}")
class {class_name}(BaseNode):
    \"\"\"
    {name} Description
    \"\"\"
    name = "{name}"
    description = "{name} summary"
    category = "{category}"
    node_type = "{safe_name}"
    
    config_model = {class_name}Config

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # Implementation goes here
        return {{"message": f"Hello from {{self.name}}", "input": input_data}}
"""
    
    output_path = f"{safe_name}_node.py"
    with open(output_path, "w") as f:
        f.write(template)
    
    typer.secho(f" Successfully scaffolded {name} at ./{output_path}", fg=typer.colors.GREEN)

@workflow_app.command("check")
def check_workflow(path: str):
    """
    Validate a workflow JSON file against the engine schemas.
    """
    typer.echo(f" Checking workflow at {path}...")
    
    try:
        with open(path, "r") as f:
            workflow = json.load(f)
        
        # We'd need to mock the validator here since it's an async engine thing
        # But for now, check basic structure
        required = ["nodes", "edges"]
        for key in required:
            if key not in workflow:
                typer.secho(f" Error: Missing required key '{key}'", fg=typer.colors.RED)
                raise typer.Exit(1)
        
        typer.secho(f" Workflow structure is valid! Found {len(workflow['nodes'])} nodes.", fg=typer.colors.GREEN)

    except Exception as e:
        typer.secho(f" Error reading/parsing workflow: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
