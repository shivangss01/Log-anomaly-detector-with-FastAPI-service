"""
Save a chart of the per-minute 5xx error rate with flagged minutes in red.
"""
import matplotlib
matplotlib.use("Agg")  # save to file without needing a display window
import matplotlib.pyplot as plt

from features import build_minute_features
from detect import LOG_PATH, detect

OUTPUT_IMAGE = "anomalies.png"


def plot_anomalies(result, output_path=OUTPUT_IMAGE):
    flagged = result[result["is_anomaly"]]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(result.index, result["error_rate"], color="steelblue", linewidth=1, label="5xx error rate")
    ax.scatter(flagged.index, flagged["error_rate"], color="red", s=30, zorder=3, label="Flagged anomaly")

    ax.set_title("Per-minute 5xx error rate with Isolation Forest anomalies")
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("Error rate")
    ax.set_ylim(0, 1)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    print(f"Saved chart to {output_path}")


def main():
    features = build_minute_features(LOG_PATH)
    result = detect(features)
    plot_anomalies(result)


if __name__ == "__main__":
    main()
