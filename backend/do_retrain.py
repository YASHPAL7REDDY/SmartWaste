import sys
sys.path.insert(0, r'C:\Users\Yashpal Reddy\OneDrive\Pictures\Documents\smartwaste\smartwaste-app\backend')

import importlib.util

spec = importlib.util.spec_from_file_location(
    'train_fast',
    r'C:\Users\Yashpal Reddy\OneDrive\Pictures\Documents\smartwaste\MLproject\ml\training\train_fast.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

if hasattr(module, 'train_fast_models'):
    results, preprocessor = module.train_fast_models()
    print("Training completed successfully!")
else:
    print("Function train_fast_models not found in module")
    print("Available attributes:", [x for x in dir(module) if not x.startswith('_')])