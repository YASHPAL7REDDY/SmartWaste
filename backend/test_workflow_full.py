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

# 2. Collect Waste - Submit new waste
submission_data = {
    'submission_date': date.today().isoformat(),
    'submission_time': '14:00:00',
    'people_present': 3,
    'items': [
        {'waste_type': 'wet', 'quantity_kg': 3.0},
        {'waste_type': 'dry', 'quantity_kg': 1.5},
        {'waste_type': 'plastic', 'quantity_kg': 0.8},
        {'waste_type': 'glass', 'quantity_kg': 0.4},
        {'waste_type': 'metal', 'quantity_kg': 0.3},
        {'waste_type': 'medical', 'quantity_kg': 0.2}
    ]
}
resp = requests.post('http://localhost:8000/api/v1/waste/submit', json=submission_data, headers=headers)
print('2. Submit waste:', resp.status_code)
submission = resp.json()
print('   ID:', submission['id'])
print('   Total:', submission['total_waste_kg'], 'kg')

# 3. Wait for automatic prediction
time.sleep(2)

# 4. Check predictions
tomorrow = (date.today() + timedelta(days=1)).isoformat()
resp = requests.get(f'http://localhost:8000/api/v1/predictions/my/next-day?prediction_date={tomorrow}', headers=headers)
pred = resp.json()
print('3. Next day prediction:', resp.status_code)
if pred:
    print('   Total:', pred['predicted_waste_kg'], 'kg')
    print('   Model:', pred['model'])
    for item in pred['waste_type_breakdown']:
        print('   ', item['waste_type'], ':', item['predicted_kg'], 'kg')

resp = requests.get(f'http://localhost:8000/api/v1/predictions/my/day-after-next?prediction_date={tomorrow}', headers=headers)
pred2 = resp.json()
print('4. Day after next prediction:', resp.status_code)
if pred2:
    print('   Total:', pred2['predicted_waste_kg'], 'kg')
    print('   Model:', pred2['model'])

# 5. Verify predictions saved in database
import sys
sys.path.insert(0, '.')
from app.database.session import SessionLocal
from app.models.prediction import WastePrediction
db = SessionLocal()
preds = db.query(WastePrediction).filter(WastePrediction.user_id == 'usr_test_user_testuser6').all()
print('5. Database predictions for user:', len(preds))
for p in preds:
    print('   ', p.prediction_date, '(', p.horizon, '):', p.predicted_waste_kg, 'kg -', p.model)
db.close()