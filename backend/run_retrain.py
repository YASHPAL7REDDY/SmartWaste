import sys
sys.path.insert(0, 'C:/Users/Yashpal Reddy/OneDrive/Pictures/Documents/smartwaste/smartwaste-app/backend')
from MLproject.ml.training.train_fast import train_fast_models

results, preprocessor = train_fast_models()
print("done")