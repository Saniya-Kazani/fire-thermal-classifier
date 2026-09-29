"""
Industrial Fire AI Service
Integrates Isolation Forest Anomaly Detection, BallTree Spatial Matching,
and Multi-Factor Risk Triage into the FastAPI backend.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import BallTree

logger = logging.getLogger(__name__)

# Locate workspace paths
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_DIR = BACKEND_DIR.parent
INDUSTRIAL_AI_DIR = WORKSPACE_DIR / "Industrial_Fire_AI" if (WORKSPACE_DIR / "Industrial_Fire_AI").exists() else BACKEND_DIR / "Industrial_Fire_AI"

CLASSIFIED_CSV_PATH = INDUSTRIAL_AI_DIR / "industrial_risk_classified.csv"
INDUSTRIES_CSV_PATH = INDUSTRIAL_AI_DIR / "industrial_locations.csv"
HOTSPOTS_EXACT_CSV_PATH = INDUSTRIAL_AI_DIR / "india_hotspots_exact.csv"


class IndustrialAIService:
    def __init__(self):
        self._cached_df: Optional[pd.DataFrame] = None
        self._cached_industries: Optional[pd.DataFrame] = None

    def load_classified_alerts(self) -> pd.DataFrame:
        """Loads pre-classified industrial risk dataset or fallback data."""
        if self._cached_df is not None and not self._cached_df.empty:
            return self._cached_df

        if CLASSIFIED_CSV_PATH.exists():
            try:
                df = pd.read_csv(CLASSIFIED_CSV_PATH)
                # Ensure essential columns exist
                required = [
                    "latitude", "longitude", "acq_date", "satellite", "frp",
                    "brightness", "anomaly_score", "investigation_priority",
                    "nearest_industry_name", "nearest_industry_distance_km",
                    "classification_reason"
                ]
                for col in required:
                    if col not in df.columns:
                        df[col] = "N/A" if col in ["nearest_industry_name", "classification_reason"] else 0.0

                df["investigation_priority"] = df["investigation_priority"].fillna("LOW").astype(str).str.upper()
                self._cached_df = df
                logger.info(f"Loaded {len(df)} industrial risk records from {CLASSIFIED_CSV_PATH}")
                return df
            except Exception as e:
                logger.error(f"Error loading classified CSV: {e}")

        # Fallback empty dataframe with correct structure (do not cache so future calls re-try)
        return pd.DataFrame(columns=[
            "latitude", "longitude", "acq_date", "satellite", "brightness", "frp",
            "anomaly_score", "anomaly_status", "priority", "alert_message",
            "nearest_industry_distance_km", "nearest_industry_name", "nearest_industry_type",
            "industry_proximity", "investigation_priority", "classification_reason"
        ])

    def load_industrial_locations(self) -> pd.DataFrame:
        """Loads mapped industrial locations dataset."""
        if self._cached_industries is not None:
            return self._cached_industries

        if INDUSTRIES_CSV_PATH.exists():
            try:
                df = pd.read_csv(INDUSTRIES_CSV_PATH)
                df = df.dropna(subset=["latitude", "longitude"])
                self._cached_industries = df
                return df
            except Exception as e:
                logger.error(f"Error loading industrial locations CSV: {e}")

        self._cached_industries = pd.DataFrame(columns=["name", "latitude", "longitude", "industrial_type"])
        return self._cached_industries

    def run_pipeline(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Executes full Industrial Fire AI pipeline:
        1. Isolation Forest Anomaly Detection per satellite
        2. BallTree Spatial Join to nearest industrial locations
        3. Risk & Priority Classification
        """
        if raw_df.empty:
            return raw_df

        df = raw_df.copy()

        # Step 1: Feature Prep & Anomaly Detection
        features = ["brightness", "bright_t31", "frp", "scan", "track"]
        for col in features:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                df[col] = 0.0

        df["anomaly"] = 0
        df["anomaly_score"] = 0.0

        if "satellite" in df.columns:
            satellites = df["satellite"].dropna().unique()
        else:
            df["satellite"] = "UNKNOWN"
            satellites = ["UNKNOWN"]

        for sat in satellites:
            mask = df["satellite"] == sat
            sub_data = df.loc[mask, [f for f in features if f in df.columns]].fillna(0)
            if len(sub_data) >= 10:
                model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42, n_jobs=-1)
                preds = model.fit_predict(sub_data)
                scores = -model.decision_function(sub_data)
                df.loc[mask, "anomaly"] = np.where(preds == -1, 1, 0)
                df.loc[mask, "anomaly_score"] = scores
            else:
                df.loc[mask, "anomaly"] = 0
                df.loc[mask, "anomaly_score"] = 0.0

        df["anomaly_status"] = np.where(df["anomaly"] == 1, "Unusual Thermal Detection", "Normal Pattern")

        # Step 2: Priority review flag based on FRP threshold
        frp_thresh = df["frp"].quantile(0.90) if "frp" in df.columns and len(df) > 0 else 50.0
        df["priority"] = np.where(df["frp"] >= frp_thresh, "HIGH_REVIEW", "REVIEW")
        df["alert_message"] = "Unusual thermal detection. Analyst verification required."

        # Step 3: BallTree Spatial Matching with Industrial Locations
        industries = self.load_industrial_locations()
        if not industries.empty and len(df) > 0:
            ind_coords = np.radians(industries[["latitude", "longitude"]].values)
            alert_coords = np.radians(df[["latitude", "longitude"]].values)

            tree = BallTree(ind_coords, metric="haversine")
            distances, indices = tree.query(alert_coords, k=1)

            df["nearest_industry_distance_km"] = distances.flatten() * 6371.0
            nearest_ind = industries.iloc[indices.flatten()].reset_index(drop=True)

            df["nearest_industry_name"] = nearest_ind["name"].values
            df["nearest_industry_type"] = nearest_ind.get("industrial_type", pd.Series(["industrial"] * len(nearest_ind))).values
            df["nearest_industry_latitude"] = nearest_ind["latitude"].values
            df["nearest_industry_longitude"] = nearest_ind["longitude"].values
            df["industry_proximity"] = np.where(
                df["nearest_industry_distance_km"] <= 5.0, "NEAR_INDUSTRY", "NOT_NEAR_INDUSTRY"
            )
        else:
            df["nearest_industry_distance_km"] = 999.0
            df["nearest_industry_name"] = "Unknown"
            df["nearest_industry_type"] = "industrial"
            df["industry_proximity"] = "NOT_NEAR_INDUSTRY"

        # Step 4: Multi-Factor Risk Classification
        def classify_row(row):
            dist = row.get("nearest_industry_distance_km", 999.0)
            prio = row.get("priority", "REVIEW")
            if prio == "HIGH_REVIEW" and dist <= 5.0:
                return "HIGH"
            elif dist <= 5.0:
                return "MEDIUM"
            else:
                return "LOW"

        def reason_row(row):
            prio = row.get("investigation_priority", "LOW")
            dist = row.get("nearest_industry_distance_km", 999.0)
            if prio == "HIGH":
                return f"High FRP review alert within {dist:.1f} km of mapped industry; verify"
            elif prio == "MEDIUM":
                return f"Thermal anomaly within {dist:.1f} km of mapped industry; verify"
            else:
                return f"Thermal anomaly more than 5 km ({dist:.1f} km) from mapped industry"

        df["investigation_priority"] = df.apply(classify_row, axis=1)
        df["classification_reason"] = df.apply(reason_row, axis=1)

        self._cached_df = df
        return df

    def get_summary(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Calculates dashboard summary metrics."""
        if df is None:
            df = self.load_classified_alerts()

        total = len(df)
        high_cnt = int((df["investigation_priority"] == "HIGH").sum()) if total > 0 else 0
        med_cnt = int((df["investigation_priority"] == "MEDIUM").sum()) if total > 0 else 0
        low_cnt = int((df["investigation_priority"] == "LOW").sum()) if total > 0 else 0
        anomalies_cnt = int((df["anomaly_status"] == "Unusual Thermal Detection").sum()) if "anomaly_status" in df.columns else total

        satellite_counts = df["satellite"].value_counts().to_dict() if "satellite" in df.columns else {}

        return {
            "total_records": total,
            "total_anomalies": anomalies_cnt,
            "priority_counts": {
                "HIGH": high_cnt,
                "MEDIUM": med_cnt,
                "LOW": low_cnt
            },
            "satellite_counts": satellite_counts
        }


industrial_ai_service = IndustrialAIService()
