import asyncio
import os
import sys

# Setup paths
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(project_root, "backend"))

from app.nodes.factory import NodeFactory

async def test_db_nodes():
    factory = NodeFactory()
    
    # Configuration for a local SQLite database
    config = {"database_url": "sqlite:///test_studio.db"}
    
    print("\n--- Testing DatabaseQueryNode ---")
    query_node = factory.get_node("database_query", config)
    if query_node:
        # First, ensure table exists (we'll use a raw execution for setup)
        from sqlalchemy import create_engine, text
        engine = create_engine(config["database_url"])
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)"))
            conn.execute(text("DELETE FROM test_table")) # Clear it
        
        # Test Query
        result = await query_node.run("SELECT 1 as test", {})
        print(f"Query Result: {result}")

    print("\n--- Testing DatabaseInsertNode ---")
    # Pass 'table' in the config during instantiation
    insert_config = {**config, "table": "test_table"}
    insert_node = factory.get_node("database_insert", insert_config)
    if insert_node:
        test_data = {"id": 1, "name": "Studio Test"}
        result = await insert_node.run(test_data, {})
        print(f"Insert Result: {result}")

    print("\n--- Testing DatabaseUpdateNode ---")
    update_node = factory.get_node("database_update", config)
    if update_node:
        update_data = {"name": "Studio Updated"}
        # We pass 'where' and 'params' in config or context/input
        # Our implementation uses get_config for 'where'
        update_node.raw_config["table"] = "test_table"
        update_node.raw_config["where"] = "id = :id"
        update_node.raw_config["params"] = {"id": 1}
        
        result = await update_node.run(update_data, {})
        print(f"Update Result: {result}")
        
    # Verify final state
    print("\n--- Verifying Final State ---")
    final_result = await query_node.run("SELECT * FROM test_table", {})
    print(f"Final Data: {final_result}")

if __name__ == "__main__":
    asyncio.run(test_db_nodes())
