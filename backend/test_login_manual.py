import sys
sys.path.insert(0, '.')
from app.services.auth import verify_password

# Test collector password
hash1 = '$2b$12$QlVx4d2YZCZPvf5a1blIzOk4Y6FLQSgzFV7YXZRKouktJSIe/PXyW'
print('collector123:', verify_password('collector123', hash1))
print('test123:', verify_password('test123', hash1))

# Admin
hash3 = '$2b$12$b19g5QYlnoMm/jDbwR21YucrKkQ19LYIuwdFouWpI9E260QjKF0Mm'
for p in ['admin123', 'admin', 'Admin123', 'admin@123', 'admin@smartwaste', 'smartwaste', 'smartwaste123', 'Admin@123', 'Admin123!', 'password', 'test123', '123456']:
    if verify_password(p, hash3):
        print(f'Admin password: {p}')
        break