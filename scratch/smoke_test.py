import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from meta_harness.wrapper import HermesWrapper


def test_wrapper_init():
    try:
        wrapper = HermesWrapper(skip_mcp=True)
        print("Wrapper initialized successfully.")
        print(f"Model: {wrapper.model}")
        print(f"Provider: {wrapper.provider}")
    except Exception as e:
        print(f"Initialization failed: {e}")


if __name__ == "__main__":
    test_wrapper_init()
