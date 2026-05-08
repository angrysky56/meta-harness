import json
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


def resolve_hermes_paths() -> tuple[Path, Path, Path]:
    """
    Resolves paths for Hermes components.
    Priority:
    1. Explicit environment variables (HERMES_AGENT_PATH, etc.)
    2. Local installation (.hermes/ in project root)
    3. User installation (~/.hermes/hermes-agent)
    """
    # Project root is 3 levels up from this file
    project_root = Path(__file__).parent.parent.parent
    user_default = Path.home() / ".hermes"

    # Check for local override in project root
    local_hermes = project_root / ".hermes"
    base_dir = local_hermes if local_hermes.exists() else user_default

    agent_path = Path(os.environ.get("HERMES_AGENT_PATH", base_dir / "hermes-agent"))
    config_path = Path(os.environ.get("HERMES_CONFIG_PATH", base_dir / "config.yaml"))
    env_path = Path(os.environ.get("HERMES_ENV_PATH", base_dir / ".env"))

    return agent_path, config_path, env_path


AGENT_PATH, CONFIG_PATH, ENV_PATH = resolve_hermes_paths()
HERMES_AGENT_PATH = str(AGENT_PATH)
HERMES_CONFIG_PATH = str(CONFIG_PATH)
HERMES_ENV_PATH = str(ENV_PATH)

# Add agent path to sys.path if it exists
if HERMES_AGENT_PATH not in sys.path and AGENT_PATH.exists():
    sys.path.append(HERMES_AGENT_PATH)
elif not AGENT_PATH.exists():
    logging.warning("Hermes agent path does not exist: %s", HERMES_AGENT_PATH)

try:
    from run_agent import AIAgent
    from tools.mcp_tool import discover_mcp_tools
    from tools.registry import registry
except ImportError as e:
    # We allow the import to fail here so the module can still be used for other purposes (like analysis)
    # but we log a strong warning. Functions that require AIAgent will fail later.
    logging.error(
        "Failed to import Hermes components from %s: %s", HERMES_AGENT_PATH, e
    )
    AIAgent = None
    discover_mcp_tools = None
    registry = None


def setup_logging(log_path: str = "logs/hermes_wrapper.log"):
    """Setup logging for Hermes wrapper."""
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    # We use a dedicated logger instead of basicConfig to avoid interfering with other modules
    wrapper_logger = logging.getLogger("hermes_wrapper")
    wrapper_logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates
    if wrapper_logger.hasHandlers():
        wrapper_logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # File handler
    fh = logging.FileHandler(log_path)
    fh.setFormatter(formatter)
    wrapper_logger.addHandler(fh)

    # Stream handler
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    wrapper_logger.addHandler(sh)

    return wrapper_logger


# Initialize logger
logger = setup_logging()


@dataclass
class ToolCall:
    name: str
    tool_id: str
    input: dict
    output: str = ""
    is_error: bool = False


@dataclass
class SessionResult:
    prompt: str
    text: str
    tool_calls: List[ToolCall]
    files_read: dict  # {path: {"reads": N, "lines": M}}
    files_written: dict  # {path: {"lines_written": M}}
    token_usage: dict
    duration_seconds: float
    model: str
    session_id: str
    exit_code: int
    cost_usd: float
    raw_events: list
    command: list = None
    cwd: str = None
    stderr: str = ""
    skill: dict = None
    name: str = None
    log_dir: str = None

    def to_dict(self):
        """Convert to a JSON-serializable dict."""
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

    @classmethod
    def from_dict(cls, d):
        """Create from a dict."""
        tc_dicts = d.pop("tool_calls", [])
        tool_calls = [ToolCall(**tc) for tc in tc_dicts]
        # raw_events is not usually stored in the summary dict
        return cls(tool_calls=tool_calls, raw_events=[], **d)

    def show(self):
        """Print compact one-line-per-event summary."""
        if self.exit_code != 0:
            print(f"  FAILED (exit={self.exit_code})")
            print(f"  {(self.stderr or 'No stderr.')[:300]}")
            return
        for tc in self.tool_calls:
            inp = tc.input
            arg = inp.get("file_path") or inp.get("pattern") or ""
            if not arg and "command" in inp:
                arg = inp["command"][:120]
            if not arg and "description" in inp:
                arg = inp["description"][:120]
            if not arg and "prompt" in inp:
                arg = inp["prompt"][:120]
            if not arg and "text" in inp:
                arg = inp["text"][:120]
            err = " ERR" if tc.is_error else ""
            print(f"  tool: {tc.name}({arg}){err}")
        text = self.text.strip().replace("\n", " ")
        if text:
            print(f"  text: {text[:200]}")
        if self.files_read:
            items = ", ".join(
                f"{Path(p).name} ({v['lines']}L)" for p, v in self.files_read.items()
            )
            print(f"  read: {items}")
        if self.files_written:
            items = ", ".join(
                f"{Path(p).name} (+{v['lines_written']}L)"
                for p, v in self.files_written.items()
            )
            print(f"  wrote: {items}")


class HermesWrapper:
    def __init__(
        self,
        log_dir="experience",
        model=None,
        provider=None,
        base_url=None,
        api_key=None,
        skip_mcp=False,
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Auto-detect from Hermes config for any unspecified params
        cfg_model, cfg_provider, cfg_base_url, cfg_api_key = self._detect_config()
        self.model = model or cfg_model
        self.provider = provider or cfg_provider
        self.base_url = base_url or cfg_base_url
        self.api_key = api_key or cfg_api_key
        self._mcp_discovered = skip_mcp  # skip discovery if requested
        self._skip_mcp = skip_mcp

    @staticmethod
    def _detect_config():
        """Read model, provider, base_url, api_key from Hermes configuration files.

        Prioritizes:
        1. Environment variables
        2. HERMES_CONFIG_PATH / HERMES_ENV_PATH
        3. Defaults

        Returns (model, provider, base_url, api_key) tuple.
        """
        import yaml

        # 1. Start with defaults
        model = os.environ.get("HERMES_MODEL", "claude-3-5-sonnet-20241022")
        provider = os.environ.get("HERMES_PROVIDER")
        base_url = os.environ.get("HERMES_BASE_URL")
        api_key = os.environ.get("HERMES_API_KEY")

        # 2. Load from config.yaml
        yaml_path = Path(HERMES_CONFIG_PATH)
        if yaml_path.exists():
            try:
                with open(yaml_path, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                mc = cfg.get("model", {})
                if not provider:
                    provider = mc.get("provider")
                if not base_url:
                    base_url = mc.get("base_url")

                default_model = mc.get("default")
                if default_model and not os.environ.get("HERMES_MODEL"):
                    # OpenRouter and others use "provider/model" format
                    if provider == "openrouter" and "/" not in default_model:
                        model = (
                            default_model  # OpenRouter default might already be full
                        )
                    elif provider and "/" not in default_model:
                        model = f"{provider}/{default_model}"
                    else:
                        model = default_model
            except Exception as e:
                logger.warning("Failed to load config from %s: %s", yaml_path, e)

        # 3. Load from .env for keys
        env_path = Path(HERMES_ENV_PATH)
        if env_path.exists():
            try:

                # We don't want to pollute the global env necessarily, so we'll parse manually
                # or just use load_dotenv if it's safe. Manual parsing is more robust for this specific file.
                env_text = env_path.read_text(encoding="utf-8")
                for line in env_text.split("\n"):
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    v = v.strip().strip('"').strip("'")
                    if k == "OPENROUTER_API_KEY" and not api_key:
                        api_key = v
                    elif k == "ANTHROPIC_API_KEY" and not api_key:
                        api_key = v
                    elif k == "OPENAI_API_KEY" and not api_key:
                        api_key = v
            except Exception as e:
                logger.warning("Failed to parse env from %s: %s", env_path, e)

        return model, provider, base_url, api_key

    def _ensure_mcp_tools(self):
        if not self._mcp_discovered:
            print("Discovering MCP tools...")
            discover_mcp_tools()
            self._mcp_discovered = True

    def _map_tools_to_toolsets(self, allowed_tools: List[str]) -> List[str]:
        toolsets = set()
        # Built-in mappings
        mapping = {
            "Read": "file",
            "Glob": "file",
            "Grep": "file",
            "Edit": "file",
            "Write": "file",
            "Bash": "terminal",
            "Agent": "delegation",
            "WebSearch": "web",
            "WebFetch": "web",
            "Reason": "advanced-reasoning",
            "Synapse": "project-synapse",
        }

        # Add all discovered MCP toolsets by default if they exist
        if not self._skip_mcp:
            for ts in registry.get_registered_toolset_names():
                if ts.startswith("mcp-"):
                    toolsets.add(ts)
                    # Also allow short names for MCP toolsets
                    server_name = ts.replace("mcp-", "")
                    toolsets.add(server_name)

        if allowed_tools:
            for tool in allowed_tools:
                if tool in mapping:
                    toolsets.add(mapping[tool])
                elif tool.lower() in toolsets:
                    pass  # already added
        else:
            # Default fallback if nothing specified
            toolsets.update(["file", "terminal", "delegation"])

        return list(toolsets)

    def verify_mcp_servers(self, servers: List[str] | None = None):
        """Check if specified MCP servers are registered and reachable."""
        if servers is None:
            servers = ["project-synapse", "advanced-reasoning"]
        self._ensure_mcp_tools()
        registered = registry.get_registered_toolset_names()
        missing = [
            s for s in servers if s not in registered and f"mcp-{s}" not in registered
        ]
        if missing:
            logger.warning("Missing MCP servers: %s", missing)
            return False
        return True

    def run(
        self,
        prompt: str,
        allowed_tools: List[str] = None,
        name: str = None,
        system_prompt: str = None,
        timeout: Optional[int] = None,
    ) -> SessionResult:
        self._ensure_mcp_tools()

        def _handler(_signum, _frame):
            raise TimeoutError(f"Session execution exceeded {timeout} seconds")

        if timeout:
            signal.signal(signal.SIGALRM, _handler)
            signal.alarm(timeout)

        try:
            start_time = time.time()
            session_id = f"hermes-{int(start_time)}-{os.getpid()}"

            toolsets = self._map_tools_to_toolsets(allowed_tools)

            # Build a robust system prompt based on SKILL.md
            base_system_prompt = (
                "You are an autonomous AI agent working inside a meta-harness evolution loop.\n"
                "Your goal is to evolve MemorySystems that improve text classification performance.\n\n"
                "CRITICAL CONSTRAINTS:\n"
                "1. Implement exactly 3 new memory systems per iteration.\n"
                "2. Fundamental mechanisms must change (retrieval, prompt arch, learning strategy, memory structure).\n"
                "3. Do NOT just tune parameters (numbers/constants).\n"
                "4. NEVER hardcode dataset names or specific domain knowledge.\n"
                "5. ALWAYS prototype your mechanism in /tmp/ before final implementation.\n"
                "6. Implementation checklist: Copied base -> Modified -> Ruff -> Mypy -> Runtime Validation.\n\n"
                "You have access to Synapse (knowledge graph) and Reason (advanced cognition). Use them proactively."
            )

            agent = AIAgent(
                model=self.model,
                provider=self.provider,
                base_url=self.base_url,
                api_key=self.api_key,
                enabled_toolsets=toolsets,
                session_id=session_id,
                max_iterations=50,
            )

            logger.info(
                "Starting Hermes session %s for %s", session_id, name or "unnamed task"
            )

            try:
                result_dict = agent.run_conversation(
                    user_message=prompt,
                    system_message=system_prompt or base_system_prompt,
                )
            except Exception as e:
                logger.error("Hermes agent crashed: %s", e)
                return SessionResult(
                    prompt=prompt,
                    text="",
                    tool_calls=[],
                    files_read={},
                    files_written={},
                    token_usage={},
                    duration_seconds=time.time() - start_time,
                    model=self.model,
                    session_id=session_id,
                    exit_code=1,
                    cost_usd=0.0,
                    raw_events=[],
                    stderr=str(e),
                )

            duration = time.time() - start_time

            # Process result
            messages = result_dict.get("messages", [])
            tool_calls = []
            files_read = {}
            files_written = {}

            # Extract last assistant message text
            final_text = ""
            for msg in reversed(messages):
                if msg["role"] == "assistant" and msg.get("content"):
                    final_text = msg["content"]
                    break

            # Map tool calls and track file operations
            call_map = {}  # tool_call_id -> ToolCall object

            for msg in messages:
                if msg["role"] == "assistant" and "tool_calls" in msg:
                    for tc in msg["tool_calls"]:
                        tc_id = tc["id"]
                        fn = tc["function"]
                        name_tc = fn["name"]
                        try:
                            args = json.loads(fn["arguments"])
                        except (json.JSONDecodeError, TypeError):
                            args = fn["arguments"]

                        t_call = ToolCall(name=name_tc, tool_id=tc_id, input=args)
                        call_map[tc_id] = t_call
                        tool_calls.append(t_call)

                if msg["role"] == "tool":
                    tc_id = msg["tool_call_id"]
                    if tc_id in call_map:
                        t_call = call_map[tc_id]
                        t_call.output = msg["content"]
                        # Simple heuristic for error
                        if (
                            "error" in msg["content"].lower()
                            or "failed" in msg["content"].lower()
                        ):
                            t_call.is_error = True

                        # Track file operations
                        if t_call.name == "read_file":
                            path = t_call.input.get("file_path")
                            if path:
                                lines = len(t_call.output.splitlines())
                                files_read[path] = files_read.get(
                                    path, {"reads": 0, "lines": 0}
                                )
                                files_read[path]["reads"] += 1
                                files_read[path]["lines"] = max(
                                    files_read[path]["lines"], lines
                                )
                        elif t_call.name == "write_file":
                            path = t_call.input.get("file_path")
                            content = t_call.input.get("content", "")
                            if path:
                                lines = len(content.splitlines())
                                files_written[path] = {"lines_written": lines}
                        elif t_call.name in ("edit_file", "multi_replace_file_content"):
                            path = t_call.input.get("file_path") or t_call.input.get(
                                "TargetFile"
                            )
                            if path:
                                files_written[path] = files_written.get(
                                    path, {"lines_written": 0}
                                )

            usage = result_dict.get("usage", {"input_tokens": 0, "output_tokens": 0})

            # Save logs to hermes_sessions
            log_dir = Path("logs/hermes_sessions")
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / f"{session_id}.json"
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(result_dict, f, indent=2)

            return SessionResult(
                prompt=prompt,
                text=final_text,
                tool_calls=tool_calls,
                files_read=files_read,
                files_written=files_written,
                token_usage=usage,
                duration_seconds=duration,
                model=self.model,
                session_id=session_id,
                exit_code=0,
                cost_usd=0.0,
                raw_events=messages,
                name=name,
                log_dir=str(log_dir),
            )
        finally:
            if timeout:
                signal.alarm(0)
