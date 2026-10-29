@echo off
python -c "import sys; sys.path.insert(0, '.'); import MLproject.ml.training.train_fast; print('import ok')" 2>&1