import argparse
import json
import time
from datetime import datetime, timezone

from app.config import settings
from app.db.database import init_db
from app.services.heat_risk_service import heat_risk_service
from app.services.schedule_service import schedule_service


def run_once(include_heat_risk: bool = True) -> dict:
    schedule_result = schedule_service.run_due_check_ins()

    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "schedule_result": schedule_result,
        "heat_risk_result": None,
    }

    if include_heat_risk:
        result["heat_risk_result"] = heat_risk_service.run_heat_risk_checks()

    print("\nScheduler Run")
    print("-------------")
    print(json.dumps(result, indent=2))

    return result


def run_loop(interval_seconds: int, include_heat_risk: bool):
    print("Senior Heat Voice Lab Scheduler Worker")
    print("--------------------------------------")
    print(f"Environment: {settings.app_env}")
    print(f"Poll interval: {interval_seconds} seconds")
    print(f"Include HeatRisk checks: {include_heat_risk}")
    print("Press CTRL+C to stop.")
    print("")

    init_db()
    print("Database initialized for scheduler worker.")

    while True:
        try:
            run_once(include_heat_risk=include_heat_risk)
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

    parser.add_argument(
        "--no-heat-risk",
        action="store_true",
        help="Disable HeatRisk checks in this worker run."
    )

    args = parser.parse_args()

    init_db()

    include_heat_risk = not args.no_heat_risk

    if args.once:
        run_once(include_heat_risk=include_heat_risk)
        return

    run_loop(
        interval_seconds=args.interval,
        include_heat_risk=include_heat_risk,
    )


if __name__ == "__main__":
    main()