"""AI Service module for interacting with different LLM providers."""

from typing import Optional
import logging
import requests

JAN_BASE_URL = "http://localhost:1337/v1/chat/completions"
OLLAMA_BASE_URL = "http://localhost:11434/api/generate"


class AIService:
    """Service for interacting with different AI providers."""

    def __init__(
        self, service_type: str, model: Optional[str] = None, debug: bool = False
    ):
        """Initialize AI service.

        Args:
            service_type: Type of AI service ('ollama' or 'jan')
            model: Model name to use
            debug: Whether to enable debug logging
        """
        self.service_type = service_type
        self.model = model
        self.debug = debug
        self.logger = logging.getLogger(__name__)

        # Set up base URLs for services
        self.base_urls = {
            "ollama": OLLAMA_BASE_URL,
            "jan": JAN_BASE_URL,
        }

        if service_type not in self.base_urls:
            self.logger.error(f"Unsupported service type: {service_type}")
            raise ValueError(f"Unsupported service type: {service_type}")

        self.logger.debug(
            f"Initialized AIService with {service_type} and model {model}"
        )

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
            self.logger.error(f"Unsupported service type: {self.service_type}")
            raise ValueError(f"Unsupported service type: {self.service_type}")

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
            "messages": [
                {
                    "role": "system",
                    "content": "You are a commit message generator. You only summarize code in git diffs.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        self.logger.debug(f"Sending request to Jan AI API at {url}")
        if self.debug:
            self.logger.debug(f"Request data: {data}")

        try:
            self.logger.debug("Making POST request to Jan AI API")
            # Add timeout parameter to prevent hanging
            response = requests.post(url, headers=headers, json=data, timeout=60)
            self.logger.debug(
                f"Received response with status code: {response.status_code}"
            )

            if self.debug:
                self.logger.debug(f"Response headers: {response.headers}")

            response.raise_for_status()
            result = response.json()

            if not result.get("choices") or not result["choices"][0].get("message"):
                self.logger.error(f"Unexpected response format from Jan AI: {result}")
                if self.debug:
                    self.logger.debug(f"Full response: {result}")
                return ""

            content = result["choices"][0]["message"]["content"]
            return content
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Error connecting to Jan AI API: {e}")
            raise Exception(
                "Error connecting to Jan AI: Is Jan AI running on localhost:1337?"
            )
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Jan AI API request timed out: {e}")
            raise Exception("Jan AI request timed out. Service may be overloaded.")
        except Exception as e:
            self.logger.error(f"Error querying Jan AI API: {e}")
            raise Exception(f"Error with Jan AI: {str(e)[:100]}")

    def _query_ollama(self, prompt: str) -> str:
        """Send query to Ollama API.

        Args:
            prompt: The prompt text

        Returns:
            Generated text response
        """
        url = self.base_urls["ollama"]
        data = {"model": self.model, "prompt": prompt, "stream": False}

        self.logger.debug(f"Sending request to Ollama API at {url}")
        if self.debug:
            self.logger.debug(f"Request data: {data}")

        try:
            self.logger.debug("Making POST request to Ollama API")
            # Add timeout parameter to prevent hanging
            response = requests.post(url, json=data, timeout=60)
            self.logger.debug(
                f"Received response with status code: {response.status_code}"
            )

            if self.debug:
                self.logger.debug(f"Response headers: {response.headers}")

            response.raise_for_status()
            result = response.json()

            if not result.get("response"):
                self.logger.error(f"Unexpected response format from Ollama: {result}")
                if self.debug:
                    self.logger.debug(f"Full response: {result}")

            return result.get("response", "")
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Error connecting to Ollama API: {e}")
            raise Exception(
                "Error connecting to Ollama: Is Ollama running on localhost:11434?"
            )
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Ollama API request timed out: {e}")
            raise Exception(
                "Ollama request timed out. Service may be overloaded or model is too large."
            )
        except Exception as e:
            self.logger.error(f"Error querying Ollama API: {e}")
            raise Exception(f"Error with Ollama: {str(e)[:100]}")
