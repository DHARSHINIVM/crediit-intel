"""
ML module: trains a LightGBM regressor on synthetic labels, saves model, and
provides prediction + SHAP explainability.

- train_model_if_needed(db): if model file missing, gather training data, synth labels, train, dump to models/lgbm_model.pkl
- predict_and_explain(db, issuer_id): compute features, load model, return prediction and per-feature SHAP contributions.
"""

import os
import logging
from typing import Tuple, Dict, Any, List

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
import shap

from .database import SessionLocal
from .features import compute_features_for_issuer

MODEL_DIR = os.path.join(os.getcwd(), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "lgbm_model.pkl")
EXPLAINER_PATH = os.path.join(MODEL_DIR, "shap_explainer.pkl")

logger = logging.getLogger(__name__)

def _ensure_model_dir():
    os.makedirs(MODEL_DIR, exist_ok=True)

def _synthesize_label_from_row(df_row: pd.Series) -> float:
    """
    Heuristic label generation for training (synthetic):
    credit_score_base = 600
    - penalty for high debt_to_ebitda
    + bonus for positive revenue growth and avg_sentiment and ebitda_margin
    Map final to range [300, 850].
    """
    base = 600.0
    debt_penalty = 100.0 * min(df_row.get("debt_to_ebitda", 0.0), 10.0) / 10.0  # 0..100
    growth_bonus = 150.0 * max(min(df_row.get("revenue_growth", 1.0), 1.0), -1.0)  # can be negative
    margin_bonus = 100.0 * max(min(df_row.get("ebitda_margin", 1.0), 1.0), -1.0)
    sentiment_bonus = 100.0 * max(min(df_row.get("avg_sentiment", 1.0), 1.0), -1.0)
    noise = np.random.normal(0, 25)
    score = base - debt_penalty + growth_bonus + margin_bonus + sentiment_bonus + noise
    # clamp
    return float(max(300.0, min(850.0, score)))

def build_training_dataframe(db) -> pd.DataFrame:
    """
    Build a small DataFrame of features per issuer using current DB rows.
    If not enough data, we duplicate or perturb entries to create a modest dataset.
    """
    issuers = db.query.__self__.query  # not used; better to query Issuer models via ORM
    # We'll import ORM models lazily to avoid circular imports
    from . import models
    import math

    rows = []
    issuer_objs = db.query(models.Issuer).all()
    for iss in issuer_objs:
        feats = compute_features_for_issuer(db, iss.id)
        feats["issuer_id"] = iss.id
        feats["issuer_name"] = iss.name
        rows.append(feats)

    if len(rows) == 0:
        # fallback: create two synthetic issuers
        rows = [
            {"issuer_id": 0, "debt_to_ebitda": 2.0, "ebitda_margin": 0.1, "revenue_growth": 0.05, "avg_sentiment": 0.1, "recent_revenue": 100.0, "recent_total_debt": 200.0},
            {"issuer_id": 1, "debt_to_ebitda": 6.0, "ebitda_margin": 0.02, "revenue_growth": -0.1, "avg_sentiment": -0.2, "recent_revenue": 10.0, "recent_total_debt": 150.0},
        ]
    df = pd.DataFrame(rows)
    # If dataset too small, augment by adding small noise
    if len(df) < 8:
        extra = []
        for i in range(20):  # create ~20 rows by jittering
            base = df.sample(n=1).iloc[0]
            jitter = {
                "issuer_id": int(base.get("issuer_id", 0)),
                "debt_to_ebitda": max(0.0, float(base["debt_to_ebitda"]) * (1.0 + np.random.normal(0, 0.2))),
                "ebitda_margin": float(base["ebitda_margin"]) * (1.0 + np.random.normal(0, 0.2)),
                "revenue_growth": float(base["revenue_growth"]) * (1.0 + np.random.normal(0, 0.3)),
                "avg_sentiment": float(base["avg_sentiment"]) + np.random.normal(0, 0.1),
                "recent_revenue": float(base["recent_revenue"]) * (1.0 + np.random.normal(0, 0.2)),
                "recent_total_debt": float(base["recent_total_debt"]) * (1.0 + np.random.normal(0, 0.2)),
            }
            extra.append(jitter)
        df = pd.concat([df, pd.DataFrame(extra)], ignore_index=True)
    return df

def train_and_save_model(db):
    _ensure_model_dir()
    logger.info("Building training dataframe...")
    df = build_training_dataframe(db)
    feature_cols = ["debt_to_ebitda", "ebitda_margin", "revenue_growth", "avg_sentiment", "recent_revenue", "recent_total_debt"]
    X = df[feature_cols].fillna(0.0).astype(float)
    y = df.apply(_synthesize_label_from_row, axis=1).astype(float)

    logger.info("Training LightGBM on %d examples...", len(X))
    model = LGBMRegressor(n_estimators=200, learning_rate=0.05, max_depth=6, random_state=42)
    model.fit(X, y)

    # Save model
    joblib.dump({"model": model, "feature_cols": feature_cols}, MODEL_PATH)
    logger.info("Saved LightGBM model to %s", MODEL_PATH)

    # Build a SHAP explainer (TreeExplainer) and save it (explainer + expected_value)
    try:
        explainer = shap.TreeExplainer(model)
        # Note: saving full explainer can be large; but we save for convenience
        joblib.dump({"explainer": explainer}, EXPLAINER_PATH)
        logger.info("Saved SHAP explainer to %s", EXPLAINER_PATH)
    except Exception as e:
        logger.exception("Failed to build/save SHAP explainer: %s", e)

def load_model_and_info():
    if not os.path.exists(MODEL_PATH):
        return None
    obj = joblib.load(MODEL_PATH)
    return obj  # dict with 'model' and 'feature_cols'

def load_explainer():
    if not os.path.exists(EXPLAINER_PATH):
        return None
    try:
        ex_obj = joblib.load(EXPLAINER_PATH)
        return ex_obj.get("explainer")
    except Exception:
        return None

def train_model_if_needed(db):
    if not os.path.exists(MODEL_PATH):
        logger.info("Model not found; training new model...")
        train_and_save_model(db)
    else:
        logger.info("Model already exists at %s", MODEL_PATH)

def predict_and_explain(db, issuer_id: int) -> Dict[str, Any]:
    """
    Returns dict:
    {
        "score": float,
        "raw_score": float,
        "features": {name: val, ...},
        "shap": [{ "feature": name, "value": val, "shap_value": shap_val }, ...]
    }
    """
    model_obj = load_model_and_info()
    if model_obj is None:
        # fallback: train now
        train_and_save_model(db)
        model_obj = load_model_and_info()
    model = model_obj["model"]
    feature_cols = model_obj["feature_cols"]

    feats = compute_features_for_issuer(db, issuer_id)
    X = pd.DataFrame([feats])[feature_cols].fillna(0.0).astype(float)

    raw_pred = model.predict(X)[0]
    # map raw_pred to normalized score between 300..850 already in synth labels (so raw_pred is that)
    score = float(max(300.0, min(850.0, raw_pred)))

    # SHAP explanation
    explainer = load_explainer()
    shap_values = None
    shap_list = []
    try:
        if explainer is None:
            explainer = shap.TreeExplainer(model)
        # shap_values for single sample -> array shape (1, n_features) or list for multioutput
        sv = explainer.shap_values(X)
        # shap_values for regression is 1d array per feature
        # shap returns array or list; normalize to 2D
        if isinstance(sv, list):
            # sometimes shap returns a list (one per output), pick first
            sv = sv[0]
        sv_arr = np.array(sv).reshape(1, -1)
        for i, fname in enumerate(feature_cols):
            shap_list.append({
                "feature": fname,
                "value": float(X.iloc[0][fname]),
                "shap_value": float(sv_arr[0, i])
            })
    except Exception as e:
        logger.exception("SHAP explanation error: %s", e)
        # fallback: no shap data
        shap_list = []

    # sort by absolute impact descending
    shap_list_sorted = sorted(shap_list, key=lambda x: abs(x.get("shap_value", 0.0)), reverse=True)

    return {
        "score": score,
        "raw_score": raw_pred,
        "features": feats,
        "shap": shap_list_sorted
    }
