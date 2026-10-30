"""Probes for the Chaos Toolkit experiments in this folder.

Standard library only, so it runs anywhere `chaos` runs (Windows included).
Each command prints a JSON result and exits 0 on success, 1 otherwise.

    python chaos/probes.py wait-for-alert IncidentPulseAvailabilityBudgetBurnFast --timeout 420
    python chaos/probes.py alert-absent IncidentPulseAvailabilityBudgetBurnFast
    python chaos/probes.py wait-for-ready --timeout 120
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PROMETHEUS = "http://localhost:9090"
LB = "http://localhost:8080"


def _firing(prometheus: str, alertname: str) -> bool:
    query = f'ALERTS{{alertname="{alertname}", alertstate="firing"}}'
    url = f"{prometheus}/api/v1/query?" + urllib.parse.urlencode({"query": query})
    with urllib.request.urlopen(url, timeout=5) as resp:
        return len(json.load(resp)["data"]["result"]) > 0


def wait_for_alert(args) -> bool:
    start = time.monotonic()
    while time.monotonic() - start < args.timeout:
        try:
            if _firing(args.prometheus, args.alertname):
                print(json.dumps({"alert": args.alertname, "fired": True,
                                  "seconds_to_fire": round(time.monotonic() - start)}))
                return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(5)
    print(json.dumps({"alert": args.alertname, "fired": False, "waited_seconds": args.timeout}))
    return False


def alert_absent(args) -> bool:
    firing = _firing(args.prometheus, args.alertname)
    print(json.dumps({"alert": args.alertname, "firing": firing}))
    return not firing


def wait_for_ready(args) -> bool:
    start = time.monotonic()
    while time.monotonic() - start < args.timeout:
        try:
            with urllib.request.urlopen(f"{args.url}/ready", timeout=5) as resp:
                if resp.status == 200:
                    print(json.dumps({"ready": True, "seconds": round(time.monotonic() - start)}))
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(2)
    print(json.dumps({"ready": False, "waited_seconds": args.timeout}))
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("wait-for-alert", help="wait until an alert is firing in Prometheus")
    p.add_argument("alertname")
    p.add_argument("--timeout", type=int, default=420)
    p.add_argument("--prometheus", default=PROMETHEUS)
    p.set_defaults(func=wait_for_alert)

    p = sub.add_parser("alert-absent", help="succeed if an alert is not firing")
    p.add_argument("alertname")
    p.add_argument("--prometheus", default=PROMETHEUS)
    p.set_defaults(func=alert_absent)

    p = sub.add_parser("wait-for-ready", help="wait until /ready answers 200 through the load balancer")
    p.add_argument("--url", default=LB)
    p.add_argument("--timeout", type=int, default=120)
    p.set_defaults(func=wait_for_ready)

    args = parser.parse_args()
    return 0 if args.func(args) else 1


if __name__ == "__main__":
    sys.exit(main())
