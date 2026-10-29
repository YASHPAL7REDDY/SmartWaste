import sys
sys.path.insert(0, '.')
from app.database.session import SessionLocal
from app.models.user import User
from app.services.auth import get_password_hash
from datetime import datetime

db = SessionLocal()

# Check if email already exists
email = 'testuser6@test.com'
existing = db.query(User).filter(User.email == email).first()
print('Existing:', existing)

# Try creating user manually
name = 'Test User'
password_hash = get_password_hash('test123')
user_id = 'usr_' + name.lower().replace(' ', '_') + '_' + email.split('@')[0]
now = datetime.utcnow()
user = User(
    id=user_id,
    name=name,
    email=email,
    mobile='9999999999',
    password_hash=password_hash,
    account_type='family',
    area='Whitefield',
    city='Bangalore',
    pincode='560001',
    address='Test Address',
    family_members=4,
    is_admin=False,
    is_collector=False,
    is_active=True,
    created_at=now,
    updated_at=now,
)

db.add(user)
try:
    db.commit()
    print('User created successfully:', user.id)
except Exception as e:
    db.rollback()
    print('Error:', e)

db.close()