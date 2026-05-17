import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

import argparse
from aggregator.pipeline import run_backfill, run_image_backfill, run_pipeline
from aggregator.scheduler import start as start_scheduler


def main() -> None:
    parser = argparse.ArgumentParser(description="Norwegian News Aggregator")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--once",
        action="store_true",
        help="Run the pipeline once and exit",
    )
    group.add_argument(
        "--serve",
        action="store_true",
        help="Start the web UI (http://localhost:8000)",
    )
    group.add_argument(
        "--backfill",
        action="store_true",
        help="Re-enrich existing articles missing sentiment/entities/topic",
    )
    group.add_argument(
        "--backfill-images",
        action="store_true",
        help="Fetch og:image for existing articles that have no image yet",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for --serve (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port for --serve (default: 8000)")
    args = parser.parse_args()

    if args.once:
        run_pipeline()
    elif args.backfill:
        run_backfill()
    elif args.backfill_images:
        run_image_backfill()
    elif args.serve:
        import uvicorn
        from aggregator.api import app
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        start_scheduler()


if __name__ == "__main__":
    main()
