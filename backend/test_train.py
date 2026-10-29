import sys
sys.path.insert(0, r'C:\Users\Yashpal Reddy\OneDrive\Pictures\Documents\smartwaste\smartwaste-app\backend')

try:
    import MLproject.ml.training.train_fast as tf
    print("Import successful")
    if hasattr(tf, 'train_fast_models'):
        results, preprocessor = tf.train_fast_models()
        print("Training completed")
    else:
        print("train_fast_models not found")
        print([x for x in dir(tf) if not x.startswith('_')])
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()