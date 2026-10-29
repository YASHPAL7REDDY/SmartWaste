import requests
import json

# Test collector login
url = "http://localhost:8000/api/v1/auth/login"
data = {
    "email": "collector@test.com",
    "password": "collector123",
    "role": "collector"
}

try:
    response = requests.post(url, json=data)
    print(f"Collector login status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Test admin login
data = {
    "email": "admin@smartwaste.io",
    "password": "admin123",
    "role": "admin"
}

try:
    response = requests.post(url, json=data)
    print(f"\nAdmin login status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Test user login
data = {
    "email": "user_whitefield@test.com",
    "password": "test123",
    "role": "user"
}

try:
    response = requests.post(url, json=data)
    print(f"\nUser login status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")