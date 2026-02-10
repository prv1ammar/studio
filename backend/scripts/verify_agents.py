import os
import sys
from typing import List

# Add the project root to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from agent_FAQ.agent_FAQ.faq_agent import FAQAgent
from agent_availability.availability_agent import AvailabilityAgent
from agent_booking.booking_agent import BookingAgent
from agent_patient.patient_agent import PatientAgent
from utils.base_agent import BaseAgent

def test_agent_interface(agent: BaseAgent, test_input: str):
    print(f"\n--- Testing {agent.agent_name} ---")
    
    # 1. Check metadata
    info = agent.get_info()
    print(f"Agent Info: {info}")
    
    # 2. Run a simple input
    print(f"Input: {test_input}")
    try:
        response = agent.run(test_input)
        print(f"Response: {response[:100]}...")
    except Exception as e:
        print(f"❌ Error running agent: {e}")
        return False

    # 3. Test Reset
    print("Testing reset...")
    try:
        agent.reset()
        print("✅ Reset successful")
    except Exception as e:
        print(f"❌ Error resetting agent: {e}")
        return False
    
    return True

def main():
    agents = [
        (FAQAgent(), "How can I book an appointment?"),
        (AvailabilityAgent(), "Are there slots for tomorrow at 10am?"),
        (BookingAgent(), "I want to see my appointments"),
        (PatientAgent(), "hello")
    ]
    
    success_count = 0
    for agent, test_input in agents:
        if test_agent_interface(agent, test_input):
            success_count += 1
            
    print(f"\nVerification Results: {success_count}/{len(agents)} agents passed.")
    if success_count == len(agents):
        print("🚀 All agents standardized and verified successfully!")
    else:
        print("⚠️ Some agents failed verification.")

if __name__ == "__main__":
    main()
