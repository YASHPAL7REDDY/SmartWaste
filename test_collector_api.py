import requests
import json

# Login as collector
url = "http://localhost:8000/api/v1/auth/login"
data = {
    "email": "collector@test.com",
    "password": "collector123",
    "role": "collector"
}

response = requests.post(url, json=data)
token = response.json()['access_token']
print(f"Collector token: {token[:50]}...")

headers = {"Authorization": f"Bearer {token}"}

# Test collector endpoints
endpoints = [
    "/api/v1/collector/collections?collection_date=2026-08-24",
    "/api/v1/collector/vehicle-info",
    "/api/v1/collector/optimize-route?max_capacity_kg=150",
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
                    print(f"  First item: {json.dumps(data[0], indent=2)[:300]}...")
            elif isinstance(data, dict):
                print(f"  Dict keys: {list(data.keys())}")
                for k, v in data.items():
                    print(f"  {k}: {v}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"\n{endpoint}: Error - {e}")