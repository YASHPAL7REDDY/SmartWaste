import sys
sys.path.insert(0, '.')
from app.services.auth import verify_password

# Test known common passwords
passwords = ['test123', 'password', 'collector123', 'admin123', 'smartwaste', 'Test123', 'Collector123', 'Admin123', 'admin@123', 'admin@smartwaste', 'admin', 'Admin@123', 'Admin123!', 'collectortest', 'test']

# Collector 1
hash1 = '$2b$12$QlVx4d2YZCZPvf5a1blIzOk4Y6FLQSgzFV7YXZRKouktJSIe/PXyW'
# Collector 2
hash2 = '$2b$12$X95vnxRi4tOEMkVEP5q7/ONiNr6ArRuVWsFLSd.Zq8UDP9EX7WXiy'
# Admin
hash3 = '$2b$12$b19g5QYlnoMm/jDbwR21YucrKkQ19LYIuwdFouWpI9E260QjKF0Mm'

for p in passwords:
    for i, h in enumerate([hash1, hash2, hash3]):
        if verify_password(p, h):
            print(f'Password found for hash {i+1}: {p}')