import requests
import time
from datetime import date, timedelta

# 1. User login
resp = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'email': 'testuser6@test.com',
    'password': 'test123',
    'role': 'user'
})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}
print('1. Login: OK')

# 2. Collect Waste - Submit waste
submission_data = {
    'submission_date': date.today().isoformat(),
    'submission_time': '10:00:00',
    'people_present': 4,
    'items': [
        {'waste_type': 'wet', 'quantity_kg': 2.5},
        {'waste_type': 'dry', 'quantity_kg': 1.0},
        {'waste_type': 'plastic', 'quantity_kg': 0.5},
        {'waste_type': 'glass', 'quantity_kg': 0.3},
        {'waste_type': 'metal', 'quantity_kg': 0.2},
        {'waste_type': 'medical', 'quantity_kg': 0.1}
    ]
}
resp = requests.post('http://localhost:8000/api/v1/waste/submit', json=submission_data, headers=headers)
print('2. Submit waste:', resp.status_code)
submission = resp.json()
print('   Submission ID:', submission['id'])
print('   Total waste:', submission['total_waste_kg'], 'kg')

# 3. Wait a moment for automatic prediction
time.sleep(2)

# 4. Check predictions
tomorrow = (date.today() + timedelta(days=1)).isoformat()
resp = requests.get(f'http://localhost:8000/api/v1/predictions/my/next-day?prediction_date={tomorrow}', headers=headers)
print('3. Next day prediction:', resp.status_code)
print('   Result:', resp.json())

day_after = (date.today() + timedelta(days=2)).isoformat()
resp = requests.get(f'http://localhost:8000/api/v1/predictions/my/day-after-next?prediction_date={tomorrow}', headers=headers)
print('4. Day after next prediction:', resp.status_code)
print('   Result:', resp.json())