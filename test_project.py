"""
Tests for the log anomaly detector.

Run from the project folder with:
    python -m pytest -v

Install test dependencies first:
    pip install pytest httpx
"""
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import main
from detect import detect
from features import build_minute_features
from parser import parse_line

VALID_LINE = (
    '192.168.1.10 - - [04/Nov/2026:10:15:32 +0000] '
    '"GET /api/users HTTP/1.1" 200 512 "-" "Mozilla/5.0"'
)


# Parser tests

def test_parse_valid_line():
    record = parse_line(VALID_LINE)
    assert record["ip"] == "192.168.1.10"
    assert record["method"] == "GET"
    assert record["path"] == "/api/users"
    assert record["status"] == 200
    assert record["size"] == 512
    assert record["timestamp"] == datetime(2026, 11, 4, 10, 15, 32, tzinfo=timezone.utc)


def test_parse_dash_size_becomes_zero():
    line = VALID_LINE.replace(" 512 ", " - ")
    assert parse_line(line)["size"] == 0


def test_parse_invalid_line_returns_none():
    assert parse_line("this is not a log line") is None


# Feature aggregation tests

def test_minute_features_count_requests_and_5xx(tmp_path):
    log = tmp_path / "test.log"
    lines = [
        '1.1.1.1 - - [04/Nov/2026:10:00:01 +0000] "GET / HTTP/1.1" 200 10 "-" "x"',
        '1.1.1.1 - - [04/Nov/2026:10:00:30 +0000] "GET / HTTP/1.1" 500 10 "-" "x"',
        '1.1.1.1 - - [04/Nov/2026:10:00:40 +0000] "GET / HTTP/1.1" 404 10 "-" "x"',
        '1.1.1.1 - - [04/Nov/2026:10:01:05 +0000] "GET / HTTP/1.1" 503 10 "-" "x"',
    ]
    log.write_text("\n".join(lines) + "\n")

    features = build_minute_features(str(log))

    assert len(features) == 2
    first_minute = features.iloc[0]
    assert first_minute["requests"] == 3
    assert first_minute["errors_5xx"] == 1  # the 404 is not a 5xx error
    assert first_minute["error_rate"] == pytest.approx(1 / 3)


# Detection tests

def test_detect_flags_injected_spikes():
    rng = np.random.default_rng(0)
    normal = pd.DataFrame({
        "requests": rng.integers(55, 66, size=100),
        "errors_5xx": rng.integers(0, 3, size=100),
    })
    normal["error_rate"] = normal["errors_5xx"] / normal["requests"]

    spikes = pd.DataFrame({"requests": [60, 60, 60], "errors_5xx": [40, 40, 40]})
    spikes["error_rate"] = spikes["errors_5xx"] / spikes["requests"]

    features = pd.concat([normal, spikes], ignore_index=True)
    result = detect(features)

    assert result["is_anomaly"].iloc[-3:].all(), "the three spike minutes should be flagged"


# API tests

@pytest.fixture
def client():
    return TestClient(main.app)


def test_root_returns_ok(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_anomalies_endpoint_returns_flagged_minutes(client):
    if not os.path.exists(main.LOG_PATH):
        pytest.skip("access.log not found; run generate_logs.py first")

    main.get_result.cache_clear()
    response = client.get("/anomalies")

    assert response.status_code == 200
    body = response.json()
    assert body["flagged_count"] > 0
    assert len(body["anomalies"]) == body["flagged_count"]
    assert {"minute", "requests", "errors_5xx", "error_rate", "score"} <= set(body["anomalies"][0])
