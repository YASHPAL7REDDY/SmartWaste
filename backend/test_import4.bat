@echo off
cd /d "C:\Users\Yashpal Reddy\OneDrive\Pictures\Documents\smartwaste\smartwaste-app\backend"
python -c "import sys; sys.path.insert(0, '.'); import MLproject.ml.training.train_fast; print('import ok')" 2>&1