import joblib
import torch

try:
    feat_scaler = joblib.load('backend/app/ml_assets/scaler_features.pkl')
    print(f"Scaler features: {feat_scaler.n_features_in_}")
    if hasattr(feat_scaler, 'feature_names_in_'):
        print(f"Feature names: {feat_scaler.feature_names_in_}")
    else:
        print("Feature names not stored in scaler.")
except Exception as e:
    print(f"Error loading scaler: {e}")

try:
    state_dict = torch.load('backend/app/ml_assets/dual_lstm_model.pth', map_location='cpu', weights_only=False)
    print("\nModel State Dict Keys:")
    for k, v in state_dict.items():
        print(f"{k}: {v.shape}")
except Exception as e:
    print(f"Error loading model: {e}")
