import sys
sys.path.insert(0, '.')
from app.database.session import SessionLocal
from app.models.user import User, Collector

db = SessionLocal()
try:
    collectors = db.query(Collector).all()
    print('Collectors:')
    for c in collectors:
        user = db.query(User).filter(User.id == c.user_id).first()
        email = user.email if user else "N/A"
        print(f'  Collector: {c.name}, ID: {c.id}, User ID: {c.user_id}, Email: {email}, Vehicle: {c.vehicle_number}, Capacity: {c.vehicle_capacity_kg}, Areas: {c.assigned_areas}')
    
    collector_users = db.query(User).filter(User.is_collector == True).all()
    print('\nUsers with is_collector=True:')
    for u in collector_users:
        print(f'  User: {u.name}, Email: {u.email}, ID: {u.id}')
finally:
    db.close()