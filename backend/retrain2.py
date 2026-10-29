import sys
sys.path.insert(0, '.')
from MLproject.ml.training.train_fast import train_fast_models

results, preprocessor = train_fast_models()
print("done")