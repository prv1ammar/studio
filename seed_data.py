import json
import requests

# ==========================================
# CREDENTIALS
# ==========================================
SUPABASE_URL = "https://vvqbtimkusvbujuocgbg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ2cWJ0aW1rdXN2YnVqdW9jZ2JnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODMwMTk1MCwiZXhwIjoyMDgzODc3OTUwfQ.EmiTItlzYA0eHBFFAWy8_5zAu37notDOtkee6h0w8Jk"

EMBEDDING_API_KEY = "sk-RVApjtnPznKZ4UXosZYEOQ"
EMBEDDING_BASE_URL = "https://toknroutertybot.tybotflow.com/"
EMBEDDING_MODEL = "text-embedding-3-small"

# ==========================================
# DATA (No manual ID)
# ==========================================
PROPERTIES = [
    {
        "title": "Apartment in Maarif Extension",
        "description": "Luxurious 2-bedroom apartment in the heart of Maarif. 85m2, modern finish, balcony, and elevator.",
        "price": 8500,
        "location": "Maarif, Casablanca",
        "bedrooms": 2,
        "surface_m2": 85,
        "property_type": "Apartment",
        "status": "available"
    },
    {
        "title": "Studio near Twin Center",
        "description": "Cozy 1-bedroom studio in Gauthier, fully furnished. Ideal for professionals. 45m2.",
        "price": 5500,
        "location": "Gauthier, Casablanca",
        "bedrooms": 1,
        "surface_m2": 45,
        "property_type": "Studio",
        "status": "available"
    },
    {
        "title": "Modern Villa in Ain Diab",
        "description": "Stunning villa with garden and pool. 4 bedrooms, 3 bathrooms. 5-minute walk to the beach.",
        "price": 35000,
        "location": "Ain Diab, Casablanca",
        "bedrooms": 4,
        "surface_m2": 400,
        "property_type": "Villa",
        "status": "available"
    }
]

def get_embedding(text):
    try:
        url = f"{EMBEDDING_BASE_URL.rstrip('/')}/embeddings"
        headers = {"Authorization": f"Bearer {EMBEDDING_API_KEY}", "Content-Type": "application/json"}
        payload = {"input": text, "model": EMBEDDING_MODEL}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()["data"][0]["embedding"]
    except Exception as e:
        print(f"Error: Embedding failed - {e}")
        return None

def seed():
    print("START: Seeding Data...")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    for p in PROPERTIES:
        print(f"PROCESS: {p['title']}...")
        search_text = f"{p['title']} {p['description']} {p['location']}"
        embedding = get_embedding(search_text)
        
        if not embedding: continue
            
        p["embedding"] = embedding
        
        response = requests.post(f"{SUPABASE_URL}/rest/v1/properties", json=p, headers=headers)
        
        if response.status_code in [200, 201]:
            print(f"SUCCESS: Saved {p['title']}")
        else:
            print(f"FAILURE: {response.status_code} - {response.text}")

if __name__ == "__main__":
    seed()
    print("FINISH: Seeding complete.")
