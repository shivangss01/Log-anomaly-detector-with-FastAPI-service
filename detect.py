"""
Train an Isolation Forest on per-minute log features and flag anomalous minutes.

Because generate_logs.py injected known spikes, we can also check how many
of the flagged minutes fall inside those spike windows.
"""
import pandas as pd
from sklearn.ensemble import IsolationForest

from features import build_minute_features
from generate_logs import SPIKES, START_TIME
from datetime import timedelta, timezone

LOG_PATH = "access.log"
FEATURE_COLUMNS = ["requests", "errors_5xx", "error_rate"]
CONTAMINATION = 0.05  # expect roughly 5% of minutes to be anomalous


def ground_truth_minutes():
    """Return the set of minutes where spikes were injected."""
    truth = set()
    utc_start = START_TIME.replace(tzinfo=timezone.utc)
    for start, length, _ in SPIKES:
        for offset in range(length):
            truth.add(utc_start + timedelta(minutes=start + offset))
    return truth


def detect(features):
    model = IsolationForest(contamination=CONTAMINATION, random_state=42)
    labels = model.fit_predict(features[FEATURE_COLUMNS])
    scores = model.decision_function(features[FEATURE_COLUMNS])

    result = features.copy()
    result["is_anomaly"] = labels == -1
    result["score"] = scores
    return result


def main():
    features = build_minute_features(LOG_PATH)
    result = detect(features)

    flagged = result[result["is_anomaly"]].sort_values("score")
    print(f"Flagged {len(flagged)} of {len(result)} minutes as anomalous:\n")
    print(flagged[["requests", "errors_5xx", "error_rate", "score"]])

    truth = ground_truth_minutes()
    flagged_minutes = set(flagged.index)
    caught = flagged_minutes & truth
    missed = truth - flagged_minutes
    false_alarms = flagged_minutes - truth

    print()
    print(f"Injected spike minutes: {len(truth)}")
    print(f"Caught: {len(caught)}")
    print(f"Missed: {len(missed)}")
    print(f"False alarms: {len(false_alarms)}")

    if missed:
        print("\nMissed minutes:")
        for minute in sorted(missed):
            print(f"  {minute:%H:%M}")


if __name__ == "__main__":
    main()
