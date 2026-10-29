import sys
sys.path.insert(0, '.')
from app.database.session import SessionLocal
from app.models.user import User
from app.services.auth import get_password_hash
from datetime import datetime

db = SessionLocal()

email = 'testadmin@test.com'
existing = db.query(User).filter(User.email == email).first()
if existing:
    print('Admin already exists')
else:
    name = 'Test Admin'
    password_hash = get_password_hash('admin123')
    user_id = 'usr_' + name.lower().replace(' ', '_') + '_' + email.split('@')[0]
    now = datetime.utcnow()
    user = User(
        id=user_id,
        name=name,
        email=email,
        mobile='9999999999',
        password_hash=password_hash,
        account_type='family',
        city='Bangalore',
        area='Whitefield',
        address='Test Address',
        pincode='560001',
        is_admin=True,
        is_collector=False,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    try:
        db.commit()
        print('Admin created successfully:', user.id)
    except Exception as e:
        db.rollback()
        print('Error:', e)

db.close()