"""Meta-Harness Evolution Runner — domain-agnostic autonomous evolution loop.

For text_classification domain, delegates to the existing meta_harness.py
via the text_classification venv to avoid dependency conflicts.
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("meta_harness.main")

TEXT_CLASS_DIR = (
    Path(__file__).resolve().parent / "reference_examples" / "text_classification"
)


def main():
    parser = argparse.ArgumentParser(description="Meta-Harness Evolution Runner")
    parser.add_argument("--domain", type=str, default="text_classification")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--model", type=str, help="Model for proposer")
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--skip-baseline", action="store_true")
    parser.add_argument("--run-name", type=str, default=None)

    args = parser.parse_args()

    if args.domain == "text_classification":
        logger.info(
            "Running text_classification evolution (%s iterations)...", args.iterations
        )
        cmd = [
            "uv",
            "run",
            "python",
            str(TEXT_CLASS_DIR / "meta_harness.py"),
            "--iterations",
            str(args.iterations),
        ]
        if args.fresh:
            cmd.append("--fresh")
        if args.skip_baseline:
            cmd.append("--skip-baseline")
        if args.run_name:
            cmd.extend(["--run-name", args.run_name])
        if args.model:
            os.environ["HERMES_PROPOSER_MODEL"] = args.model
            os.environ.pop("HERMES_PROPOSER_PROVIDER", None)
            os.environ.pop("HERMES_PROPOSER_BASE_URL", None)

        result = subprocess.run(cmd, cwd=str(TEXT_CLASS_DIR), check=False)
        sys.exit(result.returncode)
    else:
        logger.error("Unknown domain: %s", args.domain)


if __name__ == "__main__":
    main()
