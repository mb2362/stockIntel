import joblib
import torch
import numpy as np

# Path relative to backend root
MODEL_PATH = 'app/ml_assets/dual_lstm_model.pth'
SCALER_PATH = 'app/ml_assets/scaler_features.pkl'

print("--- PROBING SCALER ---")
try:
    scaler = joblib.load(SCALER_PATH)
    print(f"Features in: {scaler.n_features_in_}")
    # Recent scikit-learn stores feature names if trained on a DataFrame
    if hasattr(scaler, "feature_names_in_"):
        print(f"Feature Names: {list(scaler.feature_names_in_)}")
    else:
        print("Feature Names: Not available in this scaler version.")
except Exception as e:
    print(f"Scaler Error: {e}")

print("\n--- PROBING MODEL ---")
try:
    sd = torch.load(MODEL_PATH, map_location='cpu', weights_only=False)
    for k, v in sd.items():
        print(f"{k:<30} | {list(v.shape)}")
except Exception as e:
    print(f"Model Error: {e}")
