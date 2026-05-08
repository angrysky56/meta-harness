"""
Hermes agent wrapper for autonomous research sessions.
"""

import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger("meta_harness.wrapper")


def resolve_hermes_paths():
    """
    Resolves paths for Hermes components based on environment variables or defaults.

    Returns:
        tuple: (agent_path, config_path, env_path)
    """
    base_dir = Path.home() / ".hermes"

    agent_path = os.environ.get("HERMES_AGENT_PATH", str(base_dir / "hermes-agent"))
    config_path = os.environ.get("HERMES_CONFIG_PATH", str(base_dir / "config.yaml"))
    env_path = os.environ.get("HERMES_ENV_PATH", str(base_dir / ".env"))

    return agent_path, config_path, env_path


HERMES_AGENT_PATH, HERMES_CONFIG_PATH, HERMES_ENV_PATH = resolve_hermes_paths()

# Inject Hermes agent into sys.path
if HERMES_AGENT_PATH not in sys.path and os.path.exists(HERMES_AGENT_PATH):
    sys.path.append(HERMES_AGENT_PATH)

try:
    from run_agent import AIAgent
    from tools.mcp_tool import discover_mcp_tools
except ImportError as e:
    logger.error("Failed to import Hermes components: %s", e)
    AIAgent = None
    discover_mcp_tools = None


@dataclass
class ToolCall:
    """Represents a single tool execution within a session."""

    name: str
    tool_id: str
    input: dict
    output: str = ""
    is_error: bool = False


@dataclass
class SessionResult:
    """Captured results from an autonomous agent session."""

    prompt: str
    text: str
    tool_calls: List[ToolCall]
    files_read: dict
    files_written: dict
    token_usage: dict
    duration_seconds: float
    model: str
    session_id: str
    exit_code: int
    cost_usd: float
    raw_events: list
    stderr: str = ""
    name: str = None
    log_dir: str = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts result to a JSON-serializable dictionary."""
        return {
            "prompt": self.prompt,
            "text": self.text,
            "tool_calls": [
                {
                    "name": tc.name,
                    "tool_id": tc.tool_id,
                    "input": tc.input,
                    "output": tc.output,
                    "is_error": tc.is_error,
                }
                for tc in self.tool_calls
            ],
            "files_read": self.files_read,
            "files_written": self.files_written,
            "token_usage": self.token_usage,
            "duration_seconds": self.duration_seconds,
            "model": self.model,
            "session_id": self.session_id,
            "exit_code": self.exit_code,
            "cost_usd": self.cost_usd,
            "stderr": self.stderr,
            "name": self.name,
            "log_dir": self.log_dir,
        }

    def show(self):
        """Prints a human-readable summary of the session."""
        if self.exit_code != 0:
            print(f"  FAILED (exit={self.exit_code})")
            print(f"  {(self.stderr or 'No stderr.')[:300]}")
            return

        for tc in self.tool_calls:
            inp = tc.input
            arg = inp.get("file_path") or inp.get("pattern") or ""
            if not arg and "command" in inp:
                arg = inp["command"][:120]
            err = " [ERR]" if tc.is_error else ""
            print(f"  tool: {tc.name}({arg}){err}")

        if self.files_written:
            print(f"  wrote: {', '.join(Path(p).name for p in self.files_written)}")


class HermesWrapper:
    """Wrapper for the Hermes-Agent framework."""

    def __init__(
        self,
        log_dir: str = "logs/hermes_sessions",
        model: Optional[str] = None,
        provider: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        skip_mcp: bool = False,
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        cfg_model, cfg_provider, cfg_base_url, cfg_api_key = self._detect_config()
        self.model = model or cfg_model
        self.provider = provider or cfg_provider
        self.base_url = base_url or cfg_base_url
        self.api_key = api_key or cfg_api_key
        self._mcp_discovered = skip_mcp
        self._skip_mcp = skip_mcp

    @staticmethod
    def _detect_config():
        """Reads configuration from Hermes config and environment."""

        model = os.environ.get("HERMES_MODEL", "claude-3-5-sonnet-20241022")
        provider = os.environ.get("HERMES_PROVIDER")
        base_url = os.environ.get("HERMES_BASE_URL")
        api_key = os.environ.get("HERMES_API_KEY")

        if Path(HERMES_CONFIG_PATH).exists():
            try:
                with open(HERMES_CONFIG_PATH, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                mc = cfg.get("model", {})
                provider = provider or mc.get("provider")
                base_url = base_url or mc.get("base_url")
                if mc.get("default") and not os.environ.get("HERMES_MODEL"):
                    model = mc["default"]
            except (yaml.YAMLError, OSError) as e:
                logger.warning("Failed to load config: %s", e)

        if Path(HERMES_ENV_PATH).exists():
            try:

                env_text = Path(HERMES_ENV_PATH).read_text(encoding="utf-8")
                for line in env_text.splitlines():
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        if "API_KEY" in k and not api_key:
                            api_key = v.strip().strip('"').strip("'")
            except OSError as e:
                logger.warning("Failed to parse env: %s", e)

        return model, provider, base_url, api_key

    def run(
        self,
        prompt: str,
        _allowed_tools: Optional[List[str]] = None,
        name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        _timeout: Optional[int] = None,
    ) -> SessionResult:
        """Executes an autonomous session."""
        if not AIAgent:
            raise RuntimeError("Hermes AIAgent not available. Check HERMES_AGENT_PATH.")

        if not self._mcp_discovered and not self._skip_mcp:
            discover_mcp_tools()
            self._mcp_discovered = True

        start_time = time.time()
        session_id = f"hermes-{int(start_time)}-{os.getpid()}"

        agent = AIAgent(
            model=self.model,
            provider=self.provider,
            base_url=self.base_url,
            api_key=self.api_key,
            session_id=session_id,
        )

        try:
            result_dict = agent.run_conversation(
                user_message=prompt,
                system_message=system_prompt or "You are an autonomous research agent.",
            )
        except Exception as e:
            logger.error("Session failed: %s", e)
            return SessionResult(
                prompt,
                "",
                [],
                {},
                {},
                {},
                time.time() - start_time,
                self.model,
                session_id,
                1,
                0.0,
                [],
                stderr=str(e),
            )

        # (Simplified result extraction for the shared package)
        messages = result_dict.get("messages", [])
        final_text = ""
        for msg in reversed(messages):
            if msg["role"] == "assistant" and msg.get("content"):
                final_text = msg["content"]
                break

        return SessionResult(
            prompt=prompt,
            text=final_text,
            tool_calls=[],  # Parsing logic omitted for brevity in the core package
            files_read={},
            files_written={},
            token_usage=result_dict.get("usage", {}),
            duration_seconds=time.time() - start_time,
            model=self.model,
            session_id=session_id,
            exit_code=0,
            cost_usd=0.0,
            raw_events=messages,
            name=name,
            log_dir=str(self.log_dir),
        )
