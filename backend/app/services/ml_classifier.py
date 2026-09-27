"""
Task #12 (Optional upgrade) — Train an XGBoost classifier for finer
categories, with SHAP explanations for "why" (per Problem Statement 2.3
Step 4: "explains why (which factors mattered most)").

This is OPTIONAL and separate from services/classifier.py's rule-based
baseline. The rule-based classifier always runs and always produces a
result; this module can be trained later once there is enough labeled
history in the `hotspots` table (or from the news-report + simulated-spike
labels described in Problem Statement 2.4) and then swapped in behind the
same classify_hotspot() call signature.

Usage once trained:
    model = load_model()
    category, confidence, shap_reason = predict_with_explanation(model, feature_row)

Training data note (Problem Statement 2.4): no ground-truth "this exact fire
was an accident" dataset exists. Use:
  1. Publicly reported incidents (real refinery-fire news) matched by date/
     location to hotspot rows -> label them accident_explosion.
  2. Clearly-disclosed simulated spikes added to real baseline hotspot data
     for the other under-represented categories.
Keep both sources tagged in a `label_source` column if you extend the model
for training auditability, since NTRO evaluators "care a lot about ... how
the system uses real vs. assumed data" (Problem Statement 2.2).
"""
import logging
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import shap
import xgboost as xgb

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    "brightness",
    "frp",
    "zscore",
    "inside_industrial_buffer",
    "distance_to_site_m",
    "site_match_confidence",
    "nearby_count_same_day",
    "history_length",
    "month",
]

CATEGORIES = [
    "gas_flare",
    "accident_explosion",
    "crop_burning",
    "coal_seam_fire",
    "wildfire",
    "desert_glare_false_alarm",
    "unclassified",
]


def build_feature_frame(rows: List[Dict]) -> pd.DataFrame:
    """rows: list of dicts with keys matching FEATURE_COLUMNS."""
    df = pd.DataFrame(rows)
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0
    df["inside_industrial_buffer"] = df["inside_industrial_buffer"].astype(int)
    return df[FEATURE_COLUMNS].fillna(0)


def train_model(rows: List[Dict], labels: List[str]) -> xgb.XGBClassifier:
    """
    rows: feature dicts (see build_feature_frame).
    labels: category strings, one per row, matching CATEGORIES.
    """
    X = build_feature_frame(rows)
    y = np.array([CATEGORIES.index(l) for l in labels])

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.08,
        objective="multi:softprob",
        num_class=len(CATEGORIES),
        eval_metric="mlogloss",
    )
    model.fit(X, y)
    logger.info("Trained XGBoost classifier on %d rows", len(rows))
    return model


def predict_with_explanation(model: xgb.XGBClassifier, feature_row: Dict) -> Tuple[str, float, str]:
    """
    Returns (category, confidence, reason_string) where reason_string lists
    the top-3 SHAP-driven contributing factors, in plain English — this is
    what satisfies "explains why (which factors mattered most)".
    """
    X = build_feature_frame([feature_row])
    proba = model.predict_proba(X)[0]
    pred_idx = int(np.argmax(proba))
    category = CATEGORIES[pred_idx]
    confidence = float(proba[pred_idx])

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    # shap_values shape: (n_classes, n_samples, n_features) for multiclass
    class_shap = shap_values[pred_idx][0] if isinstance(shap_values, list) else shap_values[0]
    top_features = sorted(
        zip(FEATURE_COLUMNS, class_shap), key=lambda t: abs(t[1]), reverse=True
    )[:3]
    reason = "Top factors: " + ", ".join(
        f"{name} ({'+' if val >= 0 else ''}{val:.2f})" for name, val in top_features
    )
    return category, confidence, reason
