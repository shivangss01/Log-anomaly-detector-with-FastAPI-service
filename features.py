"""
Aggregate parsed log records into per-minute features.

Each row is one minute of traffic with:
- requests: total requests in that minute
- errors_5xx: requests that returned a 5xx status
- error_rate: errors_5xx / requests
"""
import pandas as pd

from parser import parse_file


def build_minute_features(log_path):
    records = list(parse_file(log_path))
    if not records:
        raise ValueError(f"No parseable records found in {log_path}")

    df = pd.DataFrame(records)
    df["minute"] = df["timestamp"].dt.floor("min")
    df["is_5xx"] = (df["status"] >= 500) & (df["status"] < 600)

    minutes = df.groupby("minute").agg(
        requests=("status", "size"),
        errors_5xx=("is_5xx", "sum"),
    )
    minutes["error_rate"] = minutes["errors_5xx"] / minutes["requests"]
    return minutes


if __name__ == "__main__":
    features = build_minute_features("access.log")
    print(f"{len(features)} minutes of traffic")
    print(features.head(10))
    print()
    print("Minutes with the highest error rate:")
    print(features.sort_values("error_rate", ascending=False).head(10))
