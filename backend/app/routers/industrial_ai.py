"""
FastAPI Router for Industrial Fire AI Module
Exposes endpoints for thermal anomaly detection, spatial matching alerts,
summary stats, and CSV exports.
"""

import io
import numpy as np
import pandas as pd
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from app.services.industrial_ai import industrial_ai_service

router = APIRouter(prefix="/api/industrial-ai", tags=["industrial-ai"])


@router.get("/summary")
def get_industrial_ai_summary():
    """Returns top-level summary metrics for Industrial AI anomalies & alerts."""
    summary = industrial_ai_service.get_summary()
    return summary


@router.get("/alerts")
def get_industrial_ai_alerts(
    priority: Optional[str] = Query(None, description="Comma-separated priorities e.g. HIGH,MEDIUM,LOW"),
    search: Optional[str] = Query(None, description="Search term for nearest industry name"),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0)
):
    """Returns filtered list of AI-classified industrial thermal alerts."""
    df = industrial_ai_service.load_classified_alerts()
    if df.empty:
        return {"total": 0, "alerts": []}

    filtered_df = df.copy()

    # Filter by priority
    if priority:
        priorities = [p.strip().upper() for p in priority.split(",") if p.strip()]
        if priorities:
            filtered_df = filtered_df[filtered_df["investigation_priority"].isin(priorities)]

    # Filter by search string
    if search:
        search_term = search.strip().lower()
        filtered_df = filtered_df[
            filtered_df["nearest_industry_name"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(search_term)
        ]

    total_count = len(filtered_df)
    sliced_df = filtered_df.iloc[offset : offset + limit]

    # Clean NaNs and infs for JSON serialization
    records = sliced_df.to_dict(orient="records")
    clean_records = []
    for row in records:
        clean_row = {}
        for k, v in row.items():
            if pd.isna(v) or v is None:
                clean_row[k] = None
            elif isinstance(v, (float, np.floating)):
                clean_row[k] = float(v) if not (np.isinf(v) or np.isnan(v)) else None
            elif isinstance(v, (int, np.integer)):
                clean_row[k] = int(v)
            else:
                clean_row[k] = str(v)
        clean_records.append(clean_row)

    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "alerts": clean_records
    }


@router.get("/export-csv")
def export_industrial_ai_csv(
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Generates and downloads a CSV of the filtered industrial AI alerts."""
    df = industrial_ai_service.load_classified_alerts()
    if df.empty:
        raise HTTPException(status_code=44, detail="No alert data available to export")

    filtered_df = df.copy()

    if priority:
        priorities = [p.strip().upper() for p in priority.split(",") if p.strip()]
        if priorities:
            filtered_df = filtered_df[filtered_df["investigation_priority"].isin(priorities)]

    if search:
        search_term = search.strip().lower()
        filtered_df = filtered_df[
            filtered_df["nearest_industry_name"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(search_term)
        ]

    stream = io.StringIO()
    filtered_df.to_csv(stream, index=False)
    stream.seek(0)

    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=filtered_industrial_fire_alerts.csv"
    return response


@router.post("/run-pipeline")
def trigger_ai_pipeline():
    """Triggers an on-demand re-execution of the Isolation Forest & BallTree AI pipeline."""
    raw_df = industrial_ai_service.load_classified_alerts()
    updated_df = industrial_ai_service.run_pipeline(raw_df)
    summary = industrial_ai_service.get_summary(updated_df)
    return {
        "status": "success",
        "message": "Industrial Fire AI pipeline re-executed successfully!",
        "summary": summary
    }
