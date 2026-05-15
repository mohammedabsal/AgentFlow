#!/usr/bin/env python3
"""Cancel or update a run status in the database.
Usage: ./cancel_run.py --run <run_id> [--status cancelled] [--message "reason"]
"""
import argparse
import sys
from datetime import datetime

sys.path.insert(0, "./")

from app.database.session import SessionLocal
from app.database.models import Run

parser = argparse.ArgumentParser()
parser.add_argument("--run", required=True, help="Run id to update")
parser.add_argument("--status", default="cancelled", help="Status to set (cancelled|failed|completed)")
parser.add_argument("--message", default="Cancelled by user via script", help="Optional message to store in run.output")
args = parser.parse_args()

db = SessionLocal()
try:
    run = db.get(Run, args.run)
    if run is None:
        print(f"Run {args.run} not found")
        raise SystemExit(2)

    run.status = args.status
    run.output = {"error": args.message, "updated_at": datetime.utcnow().isoformat()}
    run.state = {"phase": args.status}
    db.add(run)
    db.commit()
    db.refresh(run)

    print(f"Updated run {run.id} -> status={run.status}")
finally:
    db.close()
