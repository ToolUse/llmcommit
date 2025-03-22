"""AI Service module for interacting with different LLM providers."""

from typing import Optional

import requests

JAN_BASE_URL = "http://localhost:1337/v1/chat/completions"
OLLAMA_BASE_URL = "http://localhost:11434/api/generate"


class AIService:
    """Service for interacting with different AI providers."""

    def __init__(self, service_type: str, model: Optional[str] = None):
        """Initialize AI service.

        Args:
            service_type: Type of AI service ('ollama' or 'jan')
            model: Model name to use
        """
        self.service_type = service_type
        self.model = model

        # Set up base URLs for services
        self.base_urls = {
            "ollama": OLLAMA_BASE_URL,
            "jan": JAN_BASE_URL,
        }

        if service_type not in self.base_urls:
            raise ValueError(f"Unsupported service type: {service_type}")

    def query(self, prompt: str) -> str:
        """Query the AI service with the given prompt.

        Args:
            prompt: The prompt to send to the AI service

        Returns:
            The response from the AI service

        Raises:
            Exception: If there's an error communicating with the AI service
        """
        if self.service_type == "ollama":
            return self._query_ollama(prompt)
        elif self.service_type == "jan":
            return self._query_jan(prompt)
        else:
            raise ValueError(f"Unsupported service type: {self.service_type}")

    def _query_ollama(self, prompt: str) -> str:
        """Send query to Ollama API.

        Args:
            prompt: The prompt text

        Returns:
            Generated text response
        """
        url = self.base_urls["ollama"]
        data = {"model": self.model, "prompt": prompt, "stream": False}

        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            raise Exception(f"Error querying Ollama API: {e}")

    def _query_jan(self, prompt: str) -> str:
        """Send query to Jan AI API.

        Args:
            prompt: The prompt text

        Returns:
            Generated text response
        """
        url = self.base_urls["jan"]
        headers = {
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"Error querying Jan AI API: {e}")
