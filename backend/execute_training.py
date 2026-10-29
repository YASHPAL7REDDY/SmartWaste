import sys
sys.path.insert(0, r'C:\Users\Yashpal Reddy\OneDrive\Pictures\Documents\smartwaste\smartwaste-app\backend')

import MLproject.ml.training.train_fast as tf

print('Module loaded')
print('Has train_fast_models:', hasattr(tf, 'train_fast_models'))

if hasattr(tf, 'train_fast_models'):
    results, preprocessor = tf.train_fast_models()
    print('Training done')