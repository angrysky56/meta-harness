from typing import Any, Dict, Protocol


class Evaluator(Protocol):
    """
    Protocol defining the interface for domain-specific evaluators.
    """

    def run_benchmark(self, system_name: str, test: bool = False) -> Dict[str, Any]:
        """
        Runs the benchmark for a given system.

        Args:
            system_name: Name of the memory system/agent to evaluate.
            test: Whether to run on the held-out test set.

        Returns:
            Dict containing accuracy, latency, and other metrics.
        """
        ...

    def validate_candidate(self, name: str) -> bool:
        """
        Checks if a proposed candidate system is well-formed and runnable.
        """
        ...

    def get_frontier_score(self, results: Dict[str, Any]) -> float:
        """
        Extracts the primary metric for frontier comparison from benchmark results.
        """
        ...
