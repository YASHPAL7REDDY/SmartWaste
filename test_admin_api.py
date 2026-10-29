import requests
import json

# Login as admin
url = "http://localhost:8000/api/v1/auth/login"
data = {
    "email": "admin@smartwaste.io",
    "password": "ChangeMe123!",
    "role": "admin"
}

response = requests.post(url, json=data)
token = response.json()['access_token']
print(f"Admin token: {token[:50]}...")

headers = {"Authorization": f"Bearer {token}"}

# Test all admin endpoints
endpoints = [
    "/api/v1/admin/stats",
    "/api/v1/admin/waste/by-area?days=30",
    "/api/v1/admin/waste/by-type?days=30",
    "/api/v1/admin/waste/by-account-type?days=30",
    "/api/v1/admin/facilities",
    "/api/v1/admin/collectors/performance?days=30",
    "/api/v1/admin/predictions/accuracy",
    "/api/v1/admin/high-waste-areas?limit=10",
    "/api/v1/admin/overflow-risk/summary",
]

for endpoint in endpoints:
    try:
        response = requests.get(f"http://localhost:8000{endpoint}", headers=headers)
        print(f"\n{endpoint}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"  List length: {len(data)}")
                if data:
                    print(f"  First item: {json.dumps(data[0], indent=2)[:200]}...")
            elif isinstance(data, dict):
                print(f"  Dict keys: {list(data.keys())}")
                for k, v in data.items():
                    print(f"  {k}: {v}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"\n{endpoint}: Error - {e}")