import torch
import joblib

MODEL_PATH = 'app/ml_assets/dual_lstm_model.pth'

print("--- PROBING CHECKPOINT KEYS ---")
try:
    obj = torch.load(MODEL_PATH, map_location='cpu', weights_only=False)
    if isinstance(obj, dict):
        print(f"Keys: {list(obj.keys())}")
        if 'feature_cols' in obj:
            print(f"feature_cols: {obj['feature_cols']}")
        if 'input_size' in obj:
            print(f"input_size: {obj['input_size']}")
    else:
        print(f"Loaded object is not a dict, it is a {type(obj)}")
except Exception as e:
    print(f"Error: {e}")
