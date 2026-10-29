import sys
sys.path.insert(0, 'C:/Users/Yashpal Reddy/OneDrive/Pictures/Documents/smartwaste/smartwaste-app/backend')
import importlib.util

spec = importlib.util.spec_from_file_location('train_fast', 'C:/Users/Yashpal Reddy/OneDrive/Pictures/Documents/smartwaste/MLproject/ml/training/train_fast.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

print('train_fast_models' in dir(module))

if hasattr(module, 'train_fast_models'):
    results, preprocessor = module.train_fast_models()
    print("done")
else:
    print("Function not found")