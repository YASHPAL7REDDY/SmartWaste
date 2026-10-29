@echo off
python -c "import sys; print('hello stderr', file=sys.stderr); sys.stderr.flush(); print('hello stdout')" 2>&1