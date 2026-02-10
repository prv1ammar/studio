import sys
import os

# Set up paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
agents_dir = os.path.join(project_root, "backend", "app", "agents")
if agents_dir not in sys.path:
    sys.path.append(agents_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

print(f"Project Root: {project_root}")
print(f"Agents Dir: {agents_dir}")

def test_import(name, cmd):
    try:
        exec(cmd)
        print(f"✅ {name} imported successfully")
    except Exception as e:
        print(f"❌ {name} import failed: {e}")
        import traceback
        traceback.print_exc()

test_import("FAQAgent", "from agent_FAQ.agent_FAQ.faq_agent import FAQAgent")
test_import("AvailabilityAgent", "from agent_availability.availability_agent import AvailabilityAgent")
test_import("BookingAgent", "from agent_booking.booking_agent import BookingAgent")
test_import("PatientAgent", "from agent_patient.patient_agent import PatientAgent")
test_import("OrchestratorAgent", "from agent_orchestrator.orchestrator import OrchestratorAgent")
