from app.database.session import SessionLocal
from app.models.user import User, Collector

db = SessionLocal()
try:
    collectors = db.query(Collector).all()
    print(f"Total collectors: {len(collectors)}")
    print()
    for c in collectors:
        print(f"ID: {c.id}")
        print(f"  User ID: {c.user_id}")
        print(f"  Employee ID: {c.employee_id}")
        print(f"  Name: {c.name}")
        print(f"  Mobile: {c.mobile}")
        print(f"  Vehicle Number: {c.vehicle_number}")
        print(f"  Assigned Areas: {c.assigned_areas}")
        print(f"  Vehicle Capacity: {c.vehicle_capacity_kg}")
        print(f"  Is Active: {c.is_active}")
        print()
finally:
    db.close()