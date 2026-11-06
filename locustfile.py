"""
Load test for the log anomaly detector API using Locust.

Run against your local server (start it first with: uvicorn main:app):
    locust -f locustfile.py --host http://127.0.0.1:8000

Then open http://localhost:8089, set the number of users and spawn rate, and start.

Or run headless for a quick one-minute test:
    locust -f locustfile.py --headless -u 50 -r 10 -t 1m --host http://127.0.0.1:8000

Install first:
    pip install locust
"""
import os

from locust import HttpUser, between, constant, task

# Default: each simulated user waits 1 to 3 seconds between requests (the earlier results).
# To find the server's real ceiling, set LOCUST_WAIT=0 before running; this removes the wait.
#   PowerShell:  $env:LOCUST_WAIT="0"
WAIT_TIME = constant(0) if os.environ.get("LOCUST_WAIT") == "0" else between(1, 3)


class AnomalyApiUser(HttpUser):
    wait_time = WAIT_TIME

    @task(3)
    def get_anomalies(self):
        # Most traffic goes to the JSON endpoint
        self.client.get("/anomalies", name="/anomalies")

    @task(1)
    def get_chart(self):
        self.client.get("/chart", name="/chart")

    @task(1)
    def health_check(self):
        self.client.get("/", name="/")
