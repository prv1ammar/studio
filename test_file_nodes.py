import asyncio
import os
import sys

# Setup paths
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(project_root, "backend"))

from app.nodes.factory import NodeFactory

async def test_file_nodes():
    factory = NodeFactory()
    
    # Configuration
    config = {"base_dir": "test_sandbox"}
    
    print("\n--- Testing WriteFileNode ---")
    write_node = factory.get_node("write_file", config)
    if write_node:
        test_file = "hello.txt"
        test_content = "Hello from Studio Testing!"
        
        # We'll set the path in raw_config or pass it in a way the node expects
        write_node.raw_config["file_path"] = test_file
        
        # Test basic write
        result = await write_node.run(test_content, {})
        print(f"Write Result: {result}")
        
        # Test sub-directory write
        write_node.raw_config["file_path"] = "subdir/sub.txt"
        result = await write_node.run("Sub content", {})
        print(f"Subdir Write Result: {result}")

    print("\n--- Testing ReadFileNode ---")
    read_node = factory.get_node("read_file", config)
    if read_node:
        # Test reading the file we just wrote
        result = await read_node.run("hello.txt", {})
        print(f"Read Result: {result}")
        
    print("\n--- Testing Security Sandboxing ---")
    if read_node:
        # Test Directory Traversal (should fail)
        try:
            result = await read_node.run("../../../sensitive.txt", {})
            print(f"Traversal Result (Expected Fail/Error Payload): {result}")
        except Exception as e:
            print(f"Traversal blocked as expected: {e}")
            
        # Test Absolute Path (should fail)
        try:
             result = await read_node.run("C:/Windows/System32/drivers/etc/hosts", {})
             print(f"Absolute Path Result (Expected Fail/Error Payload): {result}")
        except Exception as e:
             print(f"Absolute path blocked as expected: {e}")

    print("\n--- Testing DeleteFileNode ---")
    delete_node = factory.get_node("delete_file", config)
    if delete_node:
        result = await delete_node.run("hello.txt", {})
        print(f"Delete Result: {result}")
        
        # Verify deletion
        verify = await read_node.run("hello.txt", {})
        print(f"Verify Deletion: {verify}")

if __name__ == "__main__":
    asyncio.run(test_file_nodes())
