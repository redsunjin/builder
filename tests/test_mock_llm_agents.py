import os
import tempfile
import unittest

from worktrees.composition_agent.agent import CompositionAgent
from worktrees.customer_agent.agent import CustomerAgent
from worktrees.generation_agent.agent import GenerationAgent


class MockLLMAgentTest(unittest.TestCase):
    ENV_KEYS = [
        "AI_PROVIDER",
        "AI_MODEL",
        "CUSTOMER_LLM_PROVIDER",
        "CUSTOMER_LLM_MODEL",
        "GENERATION_LLM_PROVIDER",
        "GENERATION_LLM_MODEL",
        "COMPOSITION_LLM_PROVIDER",
        "COMPOSITION_LLM_MODEL",
        "COMPONENT_LIBRARY_PATH",
    ]

    def setUp(self):
        self.original_env = {key: os.environ.get(key) for key in self.ENV_KEYS}
        os.environ["AI_MODEL"] = "mock-model"
        os.environ["CUSTOMER_LLM_PROVIDER"] = "mock-provider"
        os.environ["GENERATION_LLM_PROVIDER"] = "mock-provider"
        os.environ["COMPOSITION_LLM_PROVIDER"] = "mock-provider"

    def tearDown(self):
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_customer_agent_uses_mock_chain_output(self):
        agent = CustomerAgent()

        result = agent.process_request("session-123", "헤더와 버튼, 입력창이 있는 로그인 UI")

        self.assertEqual(result["session_id"], "session-123")
        self.assertIn("header", result["required_components"])
        self.assertIn("button", result["required_components"])
        self.assertIn("text_input", result["required_components"])
        self.assertIn("로그인 UI", result["user_intent"])

    def test_generation_agent_creates_mock_component_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["COMPONENT_LIBRARY_PATH"] = temp_dir
            agent = GenerationAgent()

            result = agent.load_component_metadata("search_bar")

            self.assertEqual(result["type"], "component")
            self.assertEqual(result["name"], "search_bar")
            self.assertIn("search_bar", result["html_template"])
            self.assertEqual(result["description"], "Mock-generated component for search_bar.")
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "search_bar.json")))

    def test_composition_agent_returns_full_html_without_fallback_marker(self):
        agent = CompositionAgent()

        html = agent.compose(
            {"user_intent": "Mock dashboard"},
            [
                {"name": "header", "html_template": "<header>{title}</header>"},
                {"name": "button", "html_template": "<button>{text}</button>"},
            ],
        )

        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn("Mock dashboard", html)
        self.assertIn("data-component=\"header\"", html)
        self.assertIn("data-component=\"button\"", html)
        self.assertNotIn("Generated Output (Fallback)", html)


if __name__ == "__main__":
    unittest.main()
