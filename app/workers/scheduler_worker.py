import argparse
import json
import time
from datetime import datetime, timezone

from app.config import settings
from app.db.database import init_db
from app.services.schedule_service import schedule_service


def run_once() -> dict:
    """
    Runs the due-check scheduler once.

    This uses the same logic as:
    POST /scheduler/run-due-checks
    """

    result = schedule_service.run_due_check_ins()

    print("\nScheduler Run")
    print("-------------")
    print(f"Checked at: {datetime.now(timezone.utc).isoformat()}")
    print(json.dumps(result, indent=2))

    return result


def run_loop(interval_seconds: int):
    """
    Runs the scheduler forever on a fixed interval.

    For local development, keep this running in a separate terminal.
    """

    print("Senior Heat Voice Lab Scheduler Worker")
    print("--------------------------------------")
    print(f"Environment: {settings.app_env}")
    print(f"Poll interval: {interval_seconds} seconds")
    print("Press CTRL+C to stop.")
    print("")

    init_db()
    print("Database initialized for scheduler worker.")

    while True:
        try:
            run_once()
        except Exception as exc:
            print("\nScheduler worker error")
            print("----------------------")
            print(str(exc))

        time.sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(
        description="Local scheduler worker for senior heat check-ins."
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Run the scheduler once and exit."
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=settings.scheduler_poll_seconds,
        help="Polling interval in seconds. Default comes from SCHEDULER_POLL_SECONDS."
    )

    args = parser.parse_args()

    init_db()

    if args.once:
        run_once()
        return

    run_loop(interval_seconds=args.interval)


if __name__ == "__main__":
    main()