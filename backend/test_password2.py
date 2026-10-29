import sys
sys.path.insert(0, '.')
from app.services.auth import verify_password

# Test known common passwords for users
passwords = ['test123', 'password', 'user123', 'test', '123456', 'smartwaste', 'Test123', 'User123', 'whitefield', 'koramangala', 'indiranagar', 'anekal', 'yelahanka']

# User hashes
hashes = {
    'user_whitefield@test.com': '$2b$12$D/CsGrKMK14yJj/Z797pD.Tlxstbl8PUjHJK4mBlD2j8U4WQBqWyFe',
    'user_koramangala@test.com': '$2b$12$mMafiXhw2HyfWgYzsOfMrOBKzoNgNiUxJSGzRCAJBBI5r6Xf6DzKZ6',
    'user_indiranagar@test.com': '$2b$12$o.wFzsXtNWEErnap9NWW8uAY18VtSxeXy8UcHrklfABU.QN8gQnWm',
    'user_anekal@test.com': '$2b$12$RK975VdweK2XnkqrwREd6uuVVIGW4Q0qw901.oXVyxHYQKz6Xf6DzKZ6',
    'user_yelahanka@test.com': '$2b$12$4.N7d6U90WaHsBd1b4U.tuCFg6iabw0FpSA0mgzu9BJ5r6Xf6DzKZ6',
    'wastetest@example.com': '$2b$12$QE5b2B5Z8KqKyiFaNQIHF.m0wIvqNm.JHsMCl.MIup35r6Xf6DzKZ6',
}

for email, h in hashes.items():
    for p in passwords:
        if verify_password(p, h):
            print(f'Password found for {email}: {p}')
            break
    else:
        print(f'No password found for {email}')

# Admin hashes
admin_hash = '$2b$12$b19g5QYlnoMm/jDbwR21YucrKkQ19LYIuwdFouWpI9E260QjKF0Mm'
admin_passwords = ['admin123', 'admin', 'Admin123', 'admin@123', 'admin@smartwaste', 'smartwaste', 'smartwaste123', 'Admin@123', 'Admin123!', 'password', 'test123', '123456']
for p in admin_passwords:
    if verify_password(p, admin_hash):
        print(f'Admin password: {p}')
        break
else:
    print('No admin password found')