import requests

url = "http://localhost:8001/auth/register"
payload = {
    "email": "amalmanal239@gmail.com",
    "password": "mypassword123",
    "full_name": "amal",
    "company_name": "tython"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
