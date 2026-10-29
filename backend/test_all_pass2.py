import sys
sys.path.insert(0, '.')
from app.services.auth import verify_password

# Admin
hash3 = '$2b$12$b19g5QYlnoMm/jDbwR21YucrKkQ19LYIuwdFouWpI9E260QjKF0Mm'
for p in ['admin123', 'admin', 'Admin123', 'admin@123', 'admin@smartwaste', 'smartwaste', 'smartwaste123', 'Admin@123', 'Admin123!', 'password', 'test123', '123456', 'admin@smartwaste.io', 'Admin@smartwaste', 'Smartwaste123', 'admin123!', 'Admin@123!', 'smartwaste@123', 'Smartwaste@123']:
    if verify_password(p, hash3):
        print(f'Admin password: {p}')
        break
else:
    print('No admin password found')

# User test - actual hash from DB
hash_user = '$2b$12$D/CsGrKMK14yJj/Z797pD.Tlxstbl8PUjHJK4mBlD2jNIkqacbMTa'
for p in ['test123', 'password', 'user123', 'test', '123456', 'smartwaste', 'Test123', 'User123', 'whitefield', 'koramangala', 'indiranagar', 'anekal', 'yelahanka']:
    if verify_password(p, hash_user):
        print(f'User password: {p}')
        break
else:
    print('No user password found')