import requests
import json

# Test admin login with README credentials
url = "http://localhost:8000/api/v1/auth/login"
data = {
    "email": "admin@smartwaste.io",
    "password": "ChangeMe123!",
    "role": "admin"
}

try:
    response = requests.post(url, json=data)
    print(f"Admin login status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Test with admin@smartwaste.local
data = {
    "email": "admin@smartwaste.local",
    "password": "ChangeMe123!",
    "role": "admin"
}

try:
    response = requests.post(url, json=data)
    print(f"\nAdmin login (local) status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Test user login with README credentials
data = {
    "email": "family1@example.com",
    "password": "Password123",
    "role": "user"
}

try:
    response = requests.post(url, json=data)
    print(f"\nUser login status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")