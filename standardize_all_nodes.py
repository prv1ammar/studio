import json
from typing import Dict, List, Any

print("=== COMPREHENSIVE NODE STANDARDIZATION ===\n")

# Load the node library
with open('backend/data/node_library.json', 'r', encoding='utf-8') as f:
    lib = json.load(f)

# Type inference rules based on port names and contexts
TYPE_INFERENCE_RULES = {
    # LLM and Model types
    'llm': ['LanguageModel', 'LLM'],
    'model': ['LanguageModel', 'LLM'],
    'embedding_model': ['Embeddings'],
    'embedding': ['Embeddings'],
    'embeddings': ['Embeddings'],
    
    # Data types
    'input_data': ['Text', 'Message', 'Data'],
    'data_inputs': ['Data'],
    'ingest_data': ['Data'],
    'input_value': ['Text', 'Data'],
    'data': ['Data'],
    
    # Tool types
    'tools': ['Tool'],
    'tool': ['Tool'],
    'input_tools': ['Tool'],
    'extra_tools': ['Tool'],
    
    # Memory types
    'memory': ['Memory', 'BaseChatMessageHistory'],
    'existing_memory': ['Memory'],
    
    # File types
    'file_path': ['FilePath', 'Text'],
    
    # Agent types
    'agent': ['Agent'],
    'agents': ['Agent'],
    
    # Task types
    'task': ['Task'],
    'tasks': ['Task'],
    'previous_task': ['Task'],
    
    # Vector store types
    'vectorstore': ['VectorStore'],
    'vectorstores': ['VectorStore'],
    'vector_store': ['VectorStore'],
    'input_vectorstore': ['VectorStore'],
    
    # Database types
    'db': ['Database'],
    
    # Retriever types
    'retriever': ['Retriever'],
    
    # Message types
    'message': ['Message', 'Text'],
    'user_message': ['Text', 'Message'],
    
    # Generic text
    'text': ['Text'],
    'markdown': ['Text'],
    'location': ['Text'],
    'matches': ['Data', 'Text'],
    
    # Runnable types
    'runnable': ['Runnable'],
    
    # Query types
    'query': ['Text'],
    'search_query': ['Text'],
    
    # Attribute info
    'attribute_infos': ['AttributeInfo'],
    
    # Global variables
    'global_variables': ['Data'],
    
    # Video/Media
    'videodata': ['Data'],
    'astra_results': ['Data'],
    
    # Score
    'score': ['Data'],
    
    # Input DataFrame
    'input_df': ['DataFrame'],
    
    # Parser
    'output_parser': ['OutputParser'],
    
    # Models list
    'models': ['LanguageModel'],
    
    # Judge LLM
    'judge_llm': ['LanguageModel'],
    
    # Manager
    'manager_agent': ['Agent'],
    'manager_llm': ['LanguageModel'],
    'function_calling_llm': ['LanguageModel'],
    
    # Picture description
    'pic_desc_llm': ['LanguageModel'],
}

# Standard output types for common output names
OUTPUT_TYPE_RULES = {
    'output': ['Text', 'Message'],
    'response': ['Text', 'Message'],
    'result': ['Data'],
    'results': ['Data'],
    'search_results': ['Data'],
    'status': ['Text'],
    'intent': ['Text'],
    'confidence': ['Number'],
    'location': ['Text'],
    'budget_max': ['Number'],
    'bedrooms': ['Number'],
    'property_type': ['Text'],
    'text': ['Text'],
    'markdown': ['Text'],
    'formatted_lead': ['Data'],
    'carousel_json': ['Data'],
    'data': ['Data'],
    'dataframe': ['DataFrame'],
}

# Counters
fixes_applied = {
    'missing_input_types': 0,
    'missing_output_types': 0,
    'added_descriptions': 0,
    'standardized_required_flags': 0
}

# Process each category
for category, nodes in lib.items():
    for node in nodes:
        node_id = node.get('id', 'UNKNOWN')
        
        # Fix missing input types
        for inp in node.get('inputs', []):
            if inp.get('type') == 'handle' and 'types' not in inp:
                port_name = inp.get('name', '').lower()
                
                # Try to infer type from port name
                inferred_types = None
                for pattern, types in TYPE_INFERENCE_RULES.items():
                    if pattern in port_name:
                        inferred_types = types
                        break
                
                # Default fallback
                if not inferred_types:
                    inferred_types = ['Any']
                
                inp['types'] = inferred_types
                fixes_applied['missing_input_types'] += 1
                print(f"[FIX] {category}/{node_id}/input/{inp.get('name')}: Added types {inferred_types}")
        
        # Fix missing output types
        for out in node.get('outputs', []):
            if 'types' not in out:
                port_name = out.get('name', '').lower()
                
                # Try to infer type from port name
                inferred_types = None
                for pattern, types in OUTPUT_TYPE_RULES.items():
                    if pattern in port_name:
                        inferred_types = types
                        break
                
                # Default fallback
                if not inferred_types:
                    inferred_types = ['Data']
                
                out['types'] = inferred_types
                fixes_applied['missing_output_types'] += 1
                print(f"[FIX] {category}/{node_id}/output/{out.get('name')}: Added types {inferred_types}")
        
        # Add missing descriptions
        if not node.get('description'):
            # Generate a basic description from the label
            label = node.get('label', node_id)
            node['description'] = f"{label} component for {category.lower()}."
            fixes_applied['added_descriptions'] += 1
            print(f"[FIX] {category}/{node_id}: Added description")
        
        # Standardize required flags
        for inp in node.get('inputs', []):
            if 'required' not in inp:
                # Mark handle inputs as optional by default
                inp['required'] = False
                fixes_applied['standardized_required_flags'] += 1

# Save the fixed library
with open('backend/data/node_library.json', 'w', encoding='utf-8') as f:
    json.dump(lib, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print("STANDARDIZATION COMPLETE")
print(f"{'='*60}")
print(f"Missing input types fixed: {fixes_applied['missing_input_types']}")
print(f"Missing output types fixed: {fixes_applied['missing_output_types']}")
print(f"Descriptions added: {fixes_applied['added_descriptions']}")
print(f"Required flags standardized: {fixes_applied['standardized_required_flags']}")
print(f"\nTotal fixes applied: {sum(fixes_applied.values())}")
print(f"\nUpdated node library saved to: backend/data/node_library.json")
