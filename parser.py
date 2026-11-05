"""
Parse nginx-style access log lines into structured records.

Expected format (the same one generate_logs.py writes):
192.168.1.10 - - [04/Nov/2026:10:15:32 +0000] "GET /api/users HTTP/1.1" 200 512 "-" "Mozilla/5.0"
"""
import re
from datetime import datetime

LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ '
    r'\[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) [^"]*" '
    r'(?P<status>\d{3}) (?P<size>\d+|-) '
    r'"[^"]*" "[^"]*"$'
)

TIMESTAMP_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


def parse_line(line):
    """Return a dict for one log line, or None if the line doesn't match the format."""
    match = LOG_PATTERN.match(line.strip())
    if match is None:
        return None

    fields = match.groupdict()
    return {
        "ip": fields["ip"],
        "timestamp": datetime.strptime(fields["timestamp"], TIMESTAMP_FORMAT),
        "method": fields["method"],
        "path": fields["path"],
        "status": int(fields["status"]),
        "size": 0 if fields["size"] == "-" else int(fields["size"]),
    }


def parse_file(path):
    """Yield parsed records from a log file, skipping lines that don't match."""
    skipped = 0
    with open(path) as f:
        for line in f:
            record = parse_line(line)
            if record is None:
                skipped += 1
                continue
            yield record
    if skipped:
        print(f"Warning: skipped {skipped} unparseable lines in {path}")


if __name__ == "__main__":
    # Quick check: parse the first few lines of access.log
    for i, record in enumerate(parse_file("access.log")):
        print(record)
        if i >= 4:
            break
