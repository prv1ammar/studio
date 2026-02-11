import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.app.nodes.integrations.transcription.transcription import TranscriptionNode
from backend.app.nodes.integrations.scraping.real_estate_scraper import RealEstateScraperNode

async def test_transcription():
    print("\n--- Testing TranscriptionNode ---")
    node = TranscriptionNode()
    # A small wav file that exists
    sample_audio = "https://github.com/rafaelreis-hotmart/Audio-Sample/raw/master/sample.wav"
    try:
        result = await node.execute(sample_audio)
        print(f"Transcription Result: {result.get('status')}")
        if result.get('status') == "success":
            print(f"Text: {result.get('text')}")
        return result.get("status") == "success"
    except Exception as e:
        print(f"Node execution crashed: {e}")
        return False

async def test_scraper():
    print("\n--- Testing RealEstateScraperNode ---")
    node = RealEstateScraperNode()
    # Sample Avito Link (Casablanca)
    sample_url = "https://www.avito.ma/fr/maarif/appartements/Appartement_de_luxe_%C3%A0_louer_Maarif_53829033.htm"
    try:
        result = await node.execute(sample_url)
        print(f"Result: {result}")
        if result.get("status") == "success":
            print(f"Extracted Property ID: {result.get('property_id')}")
            return True
        return False
    except Exception as e:
        print(f"Node execution crashed: {e}")
        return False

async def run_tests():
    t_success = await test_transcription()
    s_success = await test_scraper()
    
    if t_success and s_success:
        print("\n✅ All specialized nodes verified successfully!")
    else:
        print("\n❌ Verification failed for one or more nodes.")

if __name__ == "__main__":
    asyncio.run(run_tests())
