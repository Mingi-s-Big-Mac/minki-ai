import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from fastapi.testclient import TestClient

from api.main import app


class HealthTest(unittest.TestCase):
    client = TestClient(app)

    def test_health(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("api.main.urlopen")
    @patch("api.main.get_settings")
    def test_ready_with_ollama(self, get_settings, urlopen):
        get_settings.return_value = SimpleNamespace(
            llm_provider="ollama",
            chat_model="llama3.2",
            roadmap_model="llama3.2",
            embedding_provider="ollama",
            embedding_model="nomic-embed-text",
            ollama_base_url="http://ollama:11434",
        )

        response = self.client.get("/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")
        self.assertEqual(urlopen.call_count, 2)

    @patch("api.main.urlopen", side_effect=URLError("offline"))
    @patch("api.main.get_settings")
    def test_ready_when_ollama_is_unavailable(self, get_settings, _urlopen):
        get_settings.return_value = SimpleNamespace(
            llm_provider="ollama",
            chat_model="llama3.2",
            roadmap_model="llama3.2",
            embedding_provider="ollama",
            embedding_model="nomic-embed-text",
            ollama_base_url="http://ollama:11434",
        )

        response = self.client.get("/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["checks"]["ollama"], "unavailable")

    @patch(
        "api.main.urlopen",
        side_effect=HTTPError("http://ollama/api/show", 404, "missing", {}, None),
    )
    @patch("api.main.get_settings")
    def test_ready_when_ollama_model_is_missing(self, get_settings, _urlopen):
        get_settings.return_value = SimpleNamespace(
            llm_provider="ollama",
            chat_model="missing",
            roadmap_model="missing",
            embedding_provider="ollama",
            embedding_model="missing",
            ollama_base_url="http://ollama:11434",
        )

        response = self.client.get("/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["checks"]["ollama"], "missing")

    @patch("api.main.get_settings")
    def test_ready_with_anthropic_and_huggingface(self, get_settings):
        get_settings.return_value = SimpleNamespace(
            llm_provider="anthropic",
            anthropic_api_key="secret",
            embedding_provider="huggingface",
            embedding_model="jhgan/ko-sroberta-multitask",
        )
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "chroma.sqlite3").touch()
            with patch("api.main.DB_PATH", directory):
                response = self.client.get("/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")

    @patch("api.main.get_settings")
    def test_ready_when_anthropic_and_vector_db_are_missing(self, get_settings):
        get_settings.return_value = SimpleNamespace(
            llm_provider="anthropic",
            anthropic_api_key="",
            embedding_provider="huggingface",
            embedding_model="jhgan/ko-sroberta-multitask",
        )
        with tempfile.TemporaryDirectory() as directory:
            with patch("api.main.DB_PATH", directory):
                response = self.client.get("/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["checks"]["anthropic_key"], "missing")
        self.assertEqual(response.json()["checks"]["vector_db"], "missing")


if __name__ == "__main__":
    unittest.main()
