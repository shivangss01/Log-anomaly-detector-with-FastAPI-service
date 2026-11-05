"""
Generate a synthetic nginx-style access log with injected error spikes.

The spike windows are printed at the end so you know the ground truth
and can check whether detect.py finds them.
"""
import random
from datetime import datetime, timedelta

random.seed(42)

OUTPUT_FILE = "access.log"
START_TIME = datetime(2026, 11, 4, 10, 0, 0)
DURATION_MINUTES = 240
BASE_REQUESTS_PER_MINUTE = 60

ENDPOINTS = ["/", "/api/users", "/api/products", "/api/orders", "/login", "/static/app.js"]
METHODS = ["GET", "POST"]
CLIENT_IPS = [f"192.168.1.{i}" for i in range(1, 50)]
USER_AGENTS = ["Mozilla/5.0", "curl/8.4.0", "PostmanRuntime/7.36"]

# Each spike: (start minute offset, length in minutes, fraction of requests that fail with 5xx)
SPIKES = [
    (60, 5, 0.60),
    (150, 3, 0.80),
]

BASELINE_5XX_RATE = 0.01
BASELINE_404_RATE = 0.03


def spike_error_rate(minute_offset):
    """Return the injected 5xx rate for this minute, or None if no spike is active."""
    for start, length, rate in SPIKES:
        if start <= minute_offset < start + length:
            return rate
    return None


def make_line(timestamp, status):
    ip = random.choice(CLIENT_IPS)
    method = random.choice(METHODS)
    path = random.choice(ENDPOINTS)
    size = random.randint(200, 4000)
    agent = random.choice(USER_AGENTS)
    ts = timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000")
    return f'{ip} - - [{ts}] "{method} {path} HTTP/1.1" {status} {size} "-" "{agent}"'


def generate():
    lines = []
    for minute in range(DURATION_MINUTES):
        minute_start = START_TIME + timedelta(minutes=minute)
        # Vary request volume a little around the baseline
        count = max(1, int(random.gauss(BASE_REQUESTS_PER_MINUTE, 6)))
        error_rate = spike_error_rate(minute)

        for _ in range(count):
            # Spread requests randomly within the minute
            ts = minute_start + timedelta(seconds=random.randint(0, 59))
            roll = random.random()
            five_xx_rate = error_rate if error_rate is not None else BASELINE_5XX_RATE

            if roll < five_xx_rate:
                status = 500
            elif roll < five_xx_rate + BASELINE_404_RATE:
                status = 404
            else:
                status = 200

            lines.append((ts, make_line(ts, status)))

    lines.sort(key=lambda pair: pair[0])
    return [line for _, line in lines]


def main():
    log_lines = generate()
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(log_lines) + "\n")

    print(f"Wrote {len(log_lines)} lines to {OUTPUT_FILE}")
    print("Injected spike windows (ground truth):")
    for start, length, rate in SPIKES:
        window_start = START_TIME + timedelta(minutes=start)
        window_end = window_start + timedelta(minutes=length - 1)
        print(f"  {window_start:%H:%M} to {window_end:%H:%M}  (5xx rate {rate:.0%})")


if __name__ == "__main__":
    main()
