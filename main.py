"""
FastAPI service for the log anomaly detector.

Endpoints:
- GET /           health check and list of endpoints
- GET /anomalies  flagged minutes as JSON
- GET /chart      error-rate chart with anomalies marked, as PNG
"""
import os
from functools import lru_cache

from fastapi import FastAPI
from fastapi.responses import FileResponse

from features import build_minute_features
from detect import LOG_PATH, detect
from plot import plot_anomalies, OUTPUT_IMAGE

app = FastAPI(title="Log Anomaly Detector")


@lru_cache(maxsize=1)
def get_result():
    """Run feature building and detection once, then reuse the result."""
    features = build_minute_features(LOG_PATH)
    return detect(features)


@app.get("/")
def root():
    return {"status": "ok", "endpoints": ["/anomalies", "/chart"]}


@app.get("/anomalies")
def anomalies():
    result = get_result()
    flagged = result[result["is_anomaly"]].sort_values("score")
    return {
        "total_minutes": len(result),
        "flagged_count": len(flagged),
        "anomalies": [
            {
                "minute": minute.isoformat(),
                "requests": int(row["requests"]),
                "errors_5xx": int(row["errors_5xx"]),
                "error_rate": round(float(row["error_rate"]), 3),
                "score": round(float(row["score"]), 4),
            }
            for minute, row in flagged.iterrows()
        ],
    }


@app.get("/chart")
def chart():
    if not os.path.exists(OUTPUT_IMAGE):
        plot_anomalies(get_result(), OUTPUT_IMAGE)
    return FileResponse(OUTPUT_IMAGE, media_type="image/png")
