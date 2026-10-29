import importlib.util
import sys
import os

# Load the training module
spec = importlib.util.spec_from_file_location('train_fast', 'MLproject/ml/training/train_fast.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Add the project root to sys.path so MLproject imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Call the training function
results, preprocessor = module.train_fast_models()
print("done")