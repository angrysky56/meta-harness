import logging
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from text_classification.hermes_wrapper import resolve_hermes_paths, setup_logging


class TestHermesWrapper(unittest.TestCase):

    @patch("pathlib.Path.home")
    @patch("pathlib.Path.exists")
    @patch.dict(os.environ, {}, clear=True)
    def test_resolve_hermes_paths_home_default(self, mock_exists, mock_home):
        """Verify fallback to home directory when no local override exists."""
        mock_home.return_value = Path("/home/user")

        # Mock exists to say .hermes in root doesn't exist, but in home it might
        def exists_side_effect(*args, **kwargs):
            if args and "/home/user/.hermes" in str(args[0]):
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        agent, config, env = resolve_hermes_paths()

        self.assertTrue(str(agent).startswith("/home/user/.hermes"))
        self.assertTrue(str(config).startswith("/home/user/.hermes"))

    @patch("pathlib.Path.exists")
    def test_resolve_hermes_paths_local_priority(self, mock_exists):
        """Verify prioritization of local .hermes directory if it exists."""
        mock_exists.return_value = True

        agent, config, env = resolve_hermes_paths()

        self.assertIn(".hermes", str(config))
        self.assertTrue(str(config).endswith(".hermes/config.yaml"))

    def test_setup_logging_isolation(self):
        """Verify that setup_logging configures the dedicated logger."""
        # setup_logging uses hardcoded name "hermes_wrapper"
        setup_logging("test_logs/hermes_wrapper.log")

        wrapper_logger = logging.getLogger("hermes_wrapper")
        self.assertEqual(wrapper_logger.level, logging.INFO)
        self.assertTrue(len(wrapper_logger.handlers) > 0)

        # Clean up handlers
        wrapper_logger.handlers.clear()


if __name__ == "__main__":
    unittest.main()
