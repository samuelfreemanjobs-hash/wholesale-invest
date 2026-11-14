import argparse
import json
import sys
from pathlib import Path

from .orchestrator import run_daily_acquisitions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Metro Detroit Acquisition Intelligence v6.0")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Run today's acquisitions pipeline")
    run_parser.add_argument("--config", type=Path, default=None)
    run_parser.add_argument("--output", type=Path, default=Path("exports"))

    args = parser.parse_args(argv)
    if args.command == "run":
        report = run_daily_acquisitions(config_path=args.config, output_dir=args.output)
        print(json.dumps(report, indent=2, default=str))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())