"""Claude API client with prompt caching support."""
from typing import Generator
import anthropic
from shared.config import config


class ClaudeClient:
    """Wrapper around Anthropic SDK with caching and streaming support."""

    def __init__(self):
        if not config.has_api_key():
            self._client = None
        else:
            self._client = anthropic.Anthropic(api_key=config.api_key)

    def _require_client(self):
        if self._client is None:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set.\n"
                "1. Copy .env.example to .env\n"
                "2. Add your API key from https://console.anthropic.com\n"
                "3. Restart the agent"
            )

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
    ) -> str:
        """Single-turn chat. Returns response text.
        history = [{"role": "user|assistant", "content": "..."}]
        """
        self._require_client()
        messages = list(history or [])
        messages.append({"role": "user", "content": user_message})

        response = self._client.messages.create(
            model=config.model,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=messages,
        )
        return response.content[0].text

    def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
    ) -> Generator[str, None, None]:
        """Streaming chat. Yields text chunks."""
        self._require_client()
        messages = list(history or [])
        messages.append({"role": "user", "content": user_message})

        with self._client.messages.stream(
            model=config.model,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def quick(self, prompt: str) -> str:
        """Simple one-off prompt with no system context. Returns string."""
        self._require_client()
        response = self._client.messages.create(
            model=config.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
