from database_manager.config_manager import get_config_manager
from agent_FAQ.agent_FAQ.faq_agent import FAQAgent
import os

def test_dynamic_config():
    manager = get_config_manager()
    agent_name = "FAQ Agent"
    
    print(f"--- Testing Dynamic Config for {agent_name} ---")
    
    # 1. Get original config
    original_config = manager.get_config(agent_name)
    original_prompt = original_config.get("SYSTEM_PROMPT")
    
    # 2. Modify prompt in DB
    test_prompt = "YOU ARE A TEST BOT. REPLY ONLY WITH 'TEST_SUCCESS'."
    print("Updating prompt in database to test dynamic loading...")
    manager.save_config(agent_name, {
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL"),
        "SYSTEM_PROMPT": test_prompt
    })
    
    # 3. Instantiate agent and run
    print("Instantiating agent (should load new prompt)...")
    agent = FAQAgent()
    response = agent.run("Hello")
    print(f"Agent Response: {response}")
    
    # 4. Cleanup: Restore original prompt
    print("Restoring original prompt...")
    manager.save_config(agent_name, original_config)
    
    if "TEST_SUCCESS" in response.upper():
        print("\n✅ Verification SUCCESS: Agent dynamically loaded the new prompt from Supabase!")
    else:
        print("\n❌ Verification FAILED: Agent did not use the database prompt.")

if __name__ == "__main__":
    test_dynamic_config()
