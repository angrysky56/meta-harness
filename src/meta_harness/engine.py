import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from .wrapper import HermesWrapper


# Fall back to the text_classification wrapper when running in that domain
def _get_wrapper(domain: str, **kwargs):
    if domain == "text_classification":
        import sys

        tc_dir = (
            Path(__file__).resolve().parent.parent.parent
            / "reference_examples"
            / "text_classification"
        )
        if str(tc_dir) not in sys.path:
            sys.path.insert(0, str(tc_dir))
        import hermes_wrapper as tc_wrapper

        return tc_wrapper.HermesWrapper(**kwargs)
    return HermesWrapper(**kwargs)


logger = logging.getLogger("meta_harness.engine")


@dataclass
class Candidate:
    name: str
    hypothesis: str
    axis: str = "?"
    components: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Evaluator(Protocol):
    def run_benchmark(self, system_name: str, test: bool = False) -> Dict[str, Any]: ...

    def validate_candidate(self, name: str) -> bool: ...

    def get_frontier_score(self, results: Dict[str, Any]) -> float: ...


@dataclass
class EvolutionConfig:
    iterations: int = field(
        default_factory=lambda: int(os.environ.get("META_HARNESS_ITERATIONS", "20"))
    )
    run_name: Optional[str] = None
    model: str = field(
        default_factory=lambda: os.environ.get(
            "META_HARNESS_MODEL",
            os.environ.get("HERMES_PROPOSER_MODEL", "deepseek/deepseek-v4-flash"),
        )
    )
    propose_timeout: int = field(
        default_factory=lambda: int(os.environ.get("META_HARNESS_TIMEOUT", "2400"))
    )
    fresh: bool = field(
        default_factory=lambda: os.environ.get("META_HARNESS_FRESH", "").lower()
        == "true"
    )
    skip_baseline: bool = field(
        default_factory=lambda: os.environ.get("META_HARNESS_SKIP_BASELINE", "").lower()
        == "true"
    )
    logs_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("META_HARNESS_LOGS_DIR", "logs"))
    )


class EvolutionEngine:
    def __init__(
        self, evaluator: Evaluator, config: EvolutionConfig, wrapper: HermesWrapper
    ):
        self.evaluator = evaluator
        self.config = config
        self.wrapper = wrapper

        self.run_name = config.run_name or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = config.logs_dir / self.run_name
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.summary_path = self.run_dir / "evolution_summary.jsonl"
        self.frontier_path = self.run_dir / "frontier_val.json"
        self.pending_path = self.run_dir / "pending_eval.json"

        if config.fresh:
            self._fresh_start()

    def _fresh_start(self):
        logger.info("Performing fresh start...")
        # Domain-specific cleanup should be handled by evaluator or manually
        if self.summary_path.exists():
            self.summary_path.unlink()
        if self.frontier_path.exists():
            self.frontier_path.unlink()
        if self.pending_path.exists():
            self.pending_path.unlink()

    def run(self):
        logger.info("Starting evolution run: %s", self.run_name)

        # Phase 0: Baselines
        if not self.config.skip_baseline:
            self._run_baselines()

        # Phase 1..N: Evolution
        start_iter = self._count_iterations() + 1
        for i in range(self.config.iterations):
            iteration = start_iter + i
            self._step(iteration)

        # Phase Final: Test evaluation
        self._run_test_eval()

    def _step(self, iteration: int):
        logger.info("Iteration %s starting...", iteration)

        # 1. Propose
        task_prompt = self._render_task_prompt(iteration)
        logger.info("Proposing new candidates...")

        result = self.wrapper.run(
            prompt=task_prompt,
            name=f"iter{iteration}",
            # system_prompt can be customized per domain
        )

        if result.exit_code != 0:
            logger.error("Proposer failed at iteration %s", iteration)
            return

        # Load candidates from the expected output file
        if not self.pending_path.exists():
            logger.warning("Proposer finished but no pending_eval.json found.")
            return

        with open(self.pending_path, encoding="utf-8") as f:
            data = json.load(f)
            candidates_raw = data.get("candidates", [])

        candidates = [Candidate(**c) for c in candidates_raw]
        logger.info("Proposed %s candidates.", len(candidates))

        # 2. Validate
        valid_candidates = []
        for c in candidates:
            if self.evaluator.validate_candidate(c.name):
                valid_candidates.append(c)
            else:
                logger.warning("Candidate %s failed validation.", c.name)

        # 3. Benchmark
        val_scores = {}
        for c in valid_candidates:
            logger.info("Benchmarking %s...", c.name)
            results = self.evaluator.run_benchmark(c.name)
            val_scores[c.name] = self.evaluator.get_frontier_score(results)

        # 4. Update Frontier
        self._update_frontier()
        self._update_summary(iteration, valid_candidates, val_scores)

    def _run_baselines(self):
        # Implementation depends on how baselines are defined in config
        pass

    def _run_test_eval(self):
        # Implementation for final test eval on frontier systems
        pass

    def _count_iterations(self) -> int:
        if not self.summary_path.exists():
            return 0
        max_iter = 0
        with open(self.summary_path, encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    max_iter = max(max_iter, data.get("iteration", 0))
                except json.JSONDecodeError:
                    continue
        return max_iter

    def _render_task_prompt(self, iteration: int) -> str:
        return f"Run iteration {iteration} of the evolution loop. Propose 3 new candidates."

    def _update_frontier(self):
        # Logic to call evaluator with --frontier and update local frontier file
        pass

    def _update_summary(
        self, iteration: int, candidates: List[Candidate], scores: Dict[str, float]
    ):
        with open(self.summary_path, "a", encoding="utf-8") as f:
            for c in candidates:
                row = {
                    "iteration": iteration,
                    "system": c.name,
                    "avg_val": scores.get(c.name, 0),
                    "axis": c.axis,
                    "hypothesis": c.hypothesis,
                }
                f.write(json.dumps(row) + "\n")
