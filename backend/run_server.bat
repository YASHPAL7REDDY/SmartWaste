@echo off
cd /d "C:\Users\Yashpal Reddy\OneDrive\Pictures\Documents\smartwaste\smartwaste-app\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000