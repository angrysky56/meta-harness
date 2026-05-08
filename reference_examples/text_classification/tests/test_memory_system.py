import unittest

from text_classification.agents.fewshot_memory import FewShotMemory
from text_classification.agents.no_memory import NoMemory


class MockLLM:
    def __call__(self, prompt: str) -> str:
        return '{"final_answer": "test"}'


class TestMemorySystem(unittest.TestCase):
    def test_predict_signature(self):
        """Verify that predict uses 'text' as the parameter name."""
        llm = MockLLM()
        agents = [NoMemory(llm), FewShotMemory(llm)]

        for agent in agents:
            with self.subTest(agent=type(agent).__name__):
                # Inspect the predict method signature
                import inspect

                sig = inspect.signature(agent.predict)
                self.assertIn(
                    "text",
                    sig.parameters,
                    f"{type(agent).__name__}.predict must have 'text' parameter",
                )
                self.assertNotIn(
                    "input",
                    sig.parameters,
                    f"{type(agent).__name__}.predict should not have 'input' parameter",
                )

    def test_learn_from_batch_keys(self):
        """Verify that learn_from_batch correctly handles 'input' keys in the batch results."""
        llm = MockLLM()
        agent = FewShotMemory(llm)

        batch = [
            {
                "input": "This is a test input",
                "prediction": "positive",
                "ground_truth": "positive",
                "was_correct": True,
                "metadata": {},
            }
        ]

        # This should not raise an error
        try:
            agent.learn_from_batch(batch)
        except KeyError as e:
            self.fail(
                f"learn_from_batch raised KeyError: {e}. It likely expects 'text' instead of 'input' in the dict keys."
            )


if __name__ == "__main__":
    unittest.main()
