"""Text classification evaluator implementing the Evaluator protocol.

Wraps the existing reference_examples/text_classification/benchmark.py.
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict

from .evaluator import Evaluator

TEXT_CLASS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "reference_examples"
    / "text_classification"
)
TEXT_CLASS_PARENT = TEXT_CLASS_DIR.parent  # reference_examples/


class TextClassificationEvaluator(Evaluator):
    """Evaluator for text classification memory system evolution."""

    def __init__(self, logs_dir: str = None, model: str = None):
        self.logs_dir = Path(logs_dir or TEXT_CLASS_DIR / "logs")
        self.model = model or "gpt-oss-120b"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def run_benchmark(self, system_name: str, test: bool = False) -> Dict[str, Any]:
        """Run benchmark for a memory system. Returns dict with accuracy and metadata."""
        args = ["--memory", system_name, "--logs-dir", str(self.logs_dir)]
        if test:
            args.append("--test")

        subprocess.run(
            ["uv", "run", "python", "benchmark.py"] + args,
            cwd=str(TEXT_CLASS_DIR),
            capture_output=True,
            text=True,
            timeout=3600,
            check=True,
        )

        # Parse val.json output files for accuracy
        scores = {}
        for val_file in self.logs_dir.rglob("val.json"):
            try:
                data = json.loads(val_file.read_text())
                for key, entry in data.items():
                    if system_name in key and "accuracy" in entry:
                        scores[key] = entry["accuracy"]
            except (json.JSONDecodeError, KeyError):
                continue

        avg_accuracy = sum(scores.values()) / len(scores) if scores else 0.0
        return {"accuracy": avg_accuracy, "per_dataset": scores}

    def validate_candidate(self, name: str) -> bool:
        """Check if a candidate agent imports cleanly."""
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-c",
                f"from text_classification.agents.{name} import *; print('OK')",
            ],
            cwd=str(TEXT_CLASS_PARENT),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return result.returncode == 0 and "OK" in result.stdout

    def get_frontier_score(self, results: Dict[str, Any]) -> float:
        """Extract accuracy from benchmark results for frontier comparison."""
        return results.get("accuracy", 0.0)
