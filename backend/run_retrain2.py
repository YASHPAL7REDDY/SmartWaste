import importlib.util
import sys

# Load the training module
spec = importlib.util.spec_from_file_location('train_fast', 'MLproject/ml/training/train_fast.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Run training
results, preprocessor = module.train_fast_models()
print("done")