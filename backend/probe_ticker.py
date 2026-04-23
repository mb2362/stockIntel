import torch
import joblib
import numpy as np

# Probe the per-ticker AAPL checkpoint
CKPT = 'models/AAPL/dual_lstm_model.pth'
SX   = 'models/AAPL/scaler_features.pkl'
SY   = 'models/AAPL/scaler_price.pkl'

print("--- CHECKPOINT KEYS ---")
ckpt = torch.load(CKPT, map_location='cpu', weights_only=False)
print(f"Top-level keys: {list(ckpt.keys())}")
if 'ensemble_configs' in ckpt:
    print(f"Num ensemble members: {len(ckpt['ensemble_configs'])}")
    for i, cfg in enumerate(ckpt['ensemble_configs']):
        print(f"  Config {i}: {cfg}")
if 'ensemble_weights' in ckpt:
    print(f"Weights: {ckpt['ensemble_weights']}")
if 'threshold' in ckpt:
    print(f"Threshold: {ckpt['threshold']}")
if 'feature_cols' in ckpt:
    print(f"Feature cols: {ckpt['feature_cols']}")

print("\n--- FIRST MODEL STATE DICT KEYS ---")
if 'ensemble_model_state_dicts' in ckpt:
    sd = ckpt['ensemble_model_state_dicts'][0]
    for k, v in sd.items():
        print(f"  {k:<35} | {list(v.shape)}")

print("\n--- SCALERS ---")
sx = joblib.load(SX)
sy = joblib.load(SY)
print(f"scalers_X type: {type(sx)}, len={len(sx) if isinstance(sx,list) else 'N/A'}")
print(f"scalers_y type: {type(sy)}, len={len(sy) if isinstance(sy,list) else 'N/A'}")
if isinstance(sx, list):
    for i, s in enumerate(sx):
        print(f"  scalers_X[{i}]: n_features={s.n_features_in_}")
