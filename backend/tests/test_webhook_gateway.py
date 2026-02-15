import requests
import json
import time

URL = "http://localhost:8001/webhooks/test-webhook-123"

def test_webhook():
    payload = {
        "event": "user_signup",
        "data": {
            "name": "Amine",
            "email": "amine@example.com"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Test-Header": "Tyboo-Studio"
    }
    
    print(f"Sending POST request to {URL}...")
    try:
        response = requests.post(URL, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_webhook()
