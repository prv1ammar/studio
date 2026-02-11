"""
End-to-End Test for EasySpace AI Real Estate Automation
Tests the complete workflow from user input to agent response.
"""
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from backend.app.nodes.agents.easyspace.node import EasySpaceAgentNode

async def test_easyspace_agent():
    print("\n" + "="*60)
    print("🏠 EasySpace AI - End-to-End Test")
    print("="*60)
    
    # Initialize the agent
    agent = EasySpaceAgentNode(config={})
    
    # Test 1: Empty input (should return help message)
    print("\n[Test 1] Empty Input Test")
    result = await agent.execute(None)
    print(f"Response: {result}")
    
    # Test 2: General inquiry
    print("\n[Test 2] General Real Estate Inquiry")
    result = await agent.execute("Je cherche un appartement à louer à Maarif, Casablanca")
    print(f"Response: {result}")
    
    # Test 3: Link scraping request
    print("\n[Test 3] Property Link Scraping")
    avito_link = "https://www.avito.ma/fr/maarif/appartements/Appartement_de_luxe_%C3%A0_louer_Maarif_53829033.htm"
    result = await agent.execute(f"Peux-tu extraire les informations de ce lien: {avito_link}")
    print(f"Response: {result[:500]}...")  # Truncate for readability
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_easyspace_agent())
