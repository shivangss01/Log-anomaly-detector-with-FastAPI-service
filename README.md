# Log Anomaly Detector

An Isolation Forest-based anomaly detector for nginx access logs. It groups requests into one-minute windows, counts requests and 5xx errors per window, flags unusual minutes, and serves the results through a FastAPI service.

The project includes synthetic log generation with injected error spikes, so you can check that the detector catches them.

## How it works

1. **Parse:** `parser.py` reads each nginx access log line into timestamp, method, path, status, and size.
2. **Aggregate:** `features.py` counts total requests, 5xx errors, and the error rate for each minute.
3. **Detect:** `detect.py` trains an Isolation Forest on those per-minute features and flags the outliers.
4. **Serve:** `main.py` exposes the results through a FastAPI service. `plot.py` draws the error-rate chart with anomalies marked.

## Project structure

```
log-anomaly-detector/
├── generate_logs.py   # creates a synthetic nginx log with known error spikes
├── parser.py          # parses log lines into structured records
├── features.py        # per-minute request and 5xx counts
├── detect.py          # Isolation Forest anomaly detection
├── plot.py            # saves the error-rate chart
├── main.py            # FastAPI app
├── requirements.txt
├── Dockerfile
└── .gitignore
```

## Run locally

```bash
pip install -r requirements.txt
python generate_logs.py
uvicorn main:app --reload
```

Then open:
- `http://127.0.0.1:8000/anomalies` for flagged minutes as JSON
- `http://127.0.0.1:8000/chart` for the error-rate chart

## Run with Docker

```bash
docker build -t log-anomaly-detector .
docker run -p 8000:8000 log-anomaly-detector
```

The Dockerfile generates the synthetic log during the build, so the image runs without any extra files.

## API

| Endpoint | Description |
| --- | --- |
| `GET /` | Health check and list of endpoints |
| `GET /anomalies` | Flagged minutes as JSON, sorted by anomaly score |
| `GET /chart` | Error-rate chart with anomalies marked, as PNG |

Example response from `/anomalies`:

```json
{
  "total_minutes": 240,
  "flagged_count": 12,
  "anomalies": [
    {
      "minute": "2026-11-04T11:01:00+00:00",
      "requests": 50,
      "errors_5xx": 39,
      "error_rate": 0.78,
      "score": -0.1289
    }
  ]
}
```

## Results on synthetic data

The generator injects two spikes: 11:00 to 11:04 at a 60% 5xx rate, and 12:30 to 12:32 at 80%. The detector flags all 8 spike minutes, with 4 false alarms on normal traffic.

## Note on first load

The live demo runs on Render's free tier, which sleeps after a period of inactivity. The first request may take 30 to 60 seconds while the service starts. Later requests respond quickly.

## Tech stack

Python, pandas, scikit-learn, matplotlib, FastAPI, Uvicorn, Docker.
