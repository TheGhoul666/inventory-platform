"""Configuration module for life-agents system."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve base directory (life-agents/)
BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = BASE_DIR / "data"

# Load .env from base directory
load_dotenv(BASE_DIR / ".env")

# Create data directory if needed
DATA_DIR.mkdir(exist_ok=True)


class _Config:
    """Singleton configuration object."""

    @property
    def api_key(self) -> str:
        return os.getenv("ANTHROPIC_API_KEY", "")

    @property
    def base_dir(self) -> Path:
        return BASE_DIR

    @property
    def data_dir(self) -> Path:
        return DATA_DIR

    @property
    def model(self) -> str:
        return "claude-sonnet-4-6"

    def has_api_key(self) -> bool:
        key = self.api_key
        return bool(key and not key.startswith("sk-ant-api03-your"))


config = _Config()
