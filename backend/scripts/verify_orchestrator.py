from agent_orchestrator.orchestrator import OrchestratorAgent

def test_orchestrator():
    print("Initializing Orchestrator...")
    orchestrator = OrchestratorAgent()
    
    test_inputs = [
        "What are your opening hours?",          # Should route to FAQ
        "I want to book an appointment.",        # Should route to Booking
        "Is Dr. Smith available next Monday?",   # Should route to Availability
        "Create a new patient record for John."  # Should route to Patient
    ]
    
    print("\n--- Starting Tests ---\n")
    
    for text in test_inputs:
        print(f"User: {text}")
        try:
            response = orchestrator.run(text)
            print(f"Orchestrator: {response}\n")
        except Exception as e:
            print(f"Error: {e}\n")

if __name__ == "__main__":
    test_orchestrator()
