import asyncio
import time
import json
from typing import List, Dict, Any
from app.nodes.factory import NodeFactory

class AgentEvaluator:
    """
    Benchmarking suite for Tyboo Studio Agents.
    Measures accuracy, latency, and tool-calling efficiency.
    """

    def __init__(self):
        self.factory = NodeFactory()
        self.results = []

    async def evaluate_agent(self, agent_id: str, test_cases: List[Dict[str, Any]], config: Dict[str, Any] = None):
        """
        Runs a series of tests against a specific agent config.
        """
        print(f"\n[Benchmarking Agent]: {agent_id} ({config.get('agent_pattern', 'standard')})")
        
        # Simulating a Studio Graph where an LLM is connected to the Agent
        llm_node_id = "mock_llm_id"
        context = {
            "graph_data": {
                "nodes": [
                    {
                        "id": llm_node_id,
                        "data": {"id": "openai_chat", "model_name": "gpt-3.5-turbo"}
                    },
                    {
                        "id": "agent_id_within_graph",
                        "data": config or {"id": agent_id}
                    }
                ],
                "edges": [
                    {"source": llm_node_id, "target": "agent_id_within_graph"}
                ]
            },
            "node_id": "agent_id_within_graph",
            "chat_history": []
        }

        for case in test_cases:
            user_input = case["input"]
            expected_keywords = case.get("keywords", [])
            
            start_time = time.time()
            try:
                # Instantiate node via factory
                agent_node = self.factory.get_node(agent_id, config or {"id": agent_id})
                if not agent_node:
                    raise Exception(f"Could not instantiate agent {agent_id}")
                
                # Execute
                response = await agent_node.execute(user_input, context)
                latency = time.time() - start_time
                
                # Validation
                found_keywords = [k for k in expected_keywords if k.lower() in response.lower()]
                accuracy = len(found_keywords) / len(expected_keywords) if expected_keywords else 1.0
                
                result = {
                    "input": user_input,
                    "response_preview": str(response)[:100] + "...",
                    "latency_sec": round(latency, 2),
                    "accuracy": accuracy,
                    "status": "PASS" if accuracy > 0.5 else "FAIL"
                }
                print(f"  OK: Case: '{user_input[:30]}...' -> {result['status']} ({latency:.2f}s)")
                self.results.append(result)

            except Exception as e:
                print(f"  ERR: Case: '{user_input[:30]}...' -> ERROR: {e}")
                self.results.append({
                    "input": user_input,
                    "error": str(e),
                    "status": "ERROR"
                })

    def generate_report(self):
        print("\n" + "="*50)
        print("AGENT BENCHMARK REPORT")
        print("="*50)
        
        passes = len([r for r in self.results if r.get("status") == "PASS"])
        errors = len([r for r in self.results if r.get("status") == "ERROR"])
        total = len(self.results)
        
        avg_latency = sum([r.get("latency_sec", 0) for r in self.results]) / (total - errors or 1)
        
        print(f"Total Tests: {total}")
        print(f"Pass Rate:   {(passes/total)*100:.1f}%")
        print(f"Avg Latency: {avg_latency:.2f}s")
        print("="*50)

# Example Benchmarking Run
async def run_benchmark():
    evaluator = AgentEvaluator()
    
    # Define Test Cases
    faq_tests = [
        {"input": "What is your refund policy?", "keywords": ["refund", "policy", "days"]},
        {"input": "How do I contact support?", "keywords": ["support", "email", "contact"]},
    ]
    
    # Evaluate Simple Agent
    await evaluator.evaluate_agent(
        "faq_node", 
        faq_tests, 
        config={"agent_pattern": "simple"}
    )
    
    # Evaluate Planner Agent (Logic intensive)
    await evaluator.evaluate_agent(
        "faq_node", 
        [{"input": "Compare the standard and premium plans step by step.", "keywords": ["compare", "premium", "standard"]}], 
        config={"agent_pattern": "planner"}
    )
    
    evaluator.generate_report()

if __name__ == "__main__":
    # Ensure we are in backend root
    import sys
    import os
    sys.path.append(os.getcwd())
    asyncio.run(run_benchmark())
