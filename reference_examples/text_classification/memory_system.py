"""Abstract interface for memory systems."""

import hashlib
import json
import re
import threading
from abc import ABC, abstractmethod
from typing import Any

from .llm import LLMCallable


def extract_json_field(text: str, field: str, default: Any = "") -> str:
    """Helper function to extract a field from JSON in LLM response as a string.

    If the field is a complex object (dict, list), it is serialized to JSON string.
    """

    def _val_to_str(v):
        if isinstance(v, (dict, list)):
            return json.dumps(v)
        return str(v)

    # Try direct parse
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return _val_to_str(data.get(field, default))
    except json.JSONDecodeError:
        pass

    # Try code blocks: ```json ... ``` or ``` ... ```
    for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", text):
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict):
                return _val_to_str(data.get(field, default))
        except json.JSONDecodeError:
            pass

    # Find balanced braces and try parsing
    for start, char in enumerate(text):
        if char != "{":
            continue
        depth, pos, in_str = 1, start + 1, False
        while pos < len(text) and depth > 0:
            c = text[pos]
            if c == '"' and (pos == 0 or text[pos - 1] != "\\"):
                in_str = not in_str
            elif not in_str:
                depth += 1 if c == "{" else (-1 if c == "}" else 0)
            pos += 1
        if depth == 0:
            candidate = text[start:pos]
            candidate = re.sub(
                r",\s*([\]}])", r"\1", candidate
            )  # Remove trailing commas
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return _val_to_str(data.get(field, default))
            except json.JSONDecodeError:
                pass

    # Regex fallback (only works for simple string values)
    match = re.findall(rf'"{field}"\s*:\s*"([^"]*)"', text)
    return match[-1] if match else str(default)


class MemorySystem(ABC):
    """Memory system interface for online and offline learning.

    Args:
        llm: Callable that takes a prompt string and returns a response string.
    """

    def __init__(self, llm: LLMCallable):
        self._llm = llm
        self._prompt_local = threading.local()

    def call_llm(self, prompt: str) -> str:
        """Call the LLM with a prompt. Tracks last prompt length/hash per thread."""
        self._prompt_local.last_prompt_len = len(prompt)
        # trunk-ignore(bandit/B324)
        self._prompt_local.last_prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[
            :8
        ]
        self._prompt_local.last_prompt_text = prompt
        return self._llm(prompt)

    def get_last_prompt_info(self) -> dict[str, Any]:
        """Return length, hash, and full text of the last prompt sent via call_llm (thread-local)."""
        return {
            "prompt_len": getattr(self._prompt_local, "last_prompt_len", None),
            "prompt_hash": getattr(self._prompt_local, "last_prompt_hash", None),
            "prompt_text": getattr(self._prompt_local, "last_prompt_text", None),
        }

    @abstractmethod
    def predict(self, text: str) -> tuple[str, dict[str, Any]]:
        """Generate prediction BEFORE seeing ground truth. Returns (answer, metadata)."""

    @abstractmethod
    def learn_from_batch(self, batch_results: list[dict[str, Any]]) -> None:
        """Learn from a batch of evaluation results.

        Args:
            batch_results: List of dicts, each containing:
                - input: str
                - prediction: str
                - ground_truth: str
                - was_correct: bool
                - metadata: dict (optional)

        This is called AFTER all predictions in the batch are complete.
        The memory system can analyze patterns across the batch.
        """

    def get_context_length(self) -> int:
        """Return the character length of context actually injected per query.

        Override in subclasses where the injected context differs from stored state
        (e.g., fewshot memories that store all examples but only inject N).
        """
        return len(self.get_state())

    @abstractmethod
    def get_state(self) -> str:
        """Return serializable state for checkpointing."""

    @abstractmethod
    def set_state(self, state: str) -> None:
        """Restore state from serialized representation."""
