"""
PipelineOps Lightweight Scheduler (Phase 4)
Orchestrates scheduled pipeline runs using APScheduler or built-in interval timer.
Provides daily recurring runs, failure alerts, and execution heartbeat logging.
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python.orchestrator import PipelineOrchestrator, load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PipelineOps.Scheduler")


def execute_pipeline_job():
    """Triggered by the scheduler on each scheduled interval."""
    logger.info("⏰ Scheduler triggering scheduled PipelineOps execution...")
    try:
        orchestrator = PipelineOrchestrator()
        result = orchestrator.run_pipeline(seed_history=False, run_live=True)
        logger.info(f"✅ Scheduled execution finished: {result['run_id']} in {result['duration_seconds']}s")
    except Exception as e:
        logger.error(f"❌ Scheduled execution failed: {e}")


def run_with_apscheduler(interval_hours: int = 24):
    """Schedules using APScheduler BackgroundScheduler / BlockingScheduler."""
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = BlockingScheduler()
        scheduler.add_job(
            execute_pipeline_job,
            trigger=IntervalTrigger(hours=interval_hours),
            id="pipelineops_daily_job",
            name="Daily Job Market Analytics Pipeline",
            replace_existing=True,
            next_run_time=datetime.now() # Run immediately on startup
        )

        logger.info(f"🚀 APScheduler active. Running pipeline every {interval_hours} hours. Press Ctrl+C to stop.")
        scheduler.start()

    except ImportError:
        logger.info("APScheduler not found; falling back to resilient native interval loop...")
        run_native_interval_loop(interval_seconds=interval_hours * 3600)


def run_native_interval_loop(interval_seconds: int = 86400):
    """Fallback native timer loop ensuring 100% zero-dependency scheduling."""
    logger.info(f"🚀 Native scheduler active. Running pipeline every {interval_seconds}s. Press Ctrl+C to stop.")
    while True:
        execute_pipeline_job()
        logger.info(f"Sleeping for {interval_seconds} seconds until next scheduled run...")
        try:
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user.")
            break


def main():
    parser = argparse.ArgumentParser(description="PipelineOps Scheduled Orchestrator")
    parser.add_argument("--interval-hours", type=int, default=24, help="Interval in hours (default: 24)")
    parser.add_argument("--interval-seconds", type=int, default=None, help="Interval in seconds (for quick testing)")
    parser.add_argument("--run-once", action="store_true", help="Execute single run and exit immediately")
    args = parser.parse_args()

    if args.run_once:
        logger.info("Executing single scheduled pipeline run (--run-once)...")
        execute_pipeline_job()
        return

    if args.interval_seconds:
        run_native_interval_loop(interval_seconds=args.interval_seconds)
    else:
        run_with_apscheduler(interval_hours=args.interval_hours)


if __name__ == "__main__":
    main()
