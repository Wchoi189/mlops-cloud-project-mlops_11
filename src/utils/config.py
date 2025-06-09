import os
from pathlib import Path
from typing import Any, Dict

import yaml


class Config:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()

    def _get_default_config_path(self) -> str:
        return os.path.join(
            os.path.dirname(__file__), "..", "..", "configs", "model_config.yaml"
        )

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)


# Environment variables
class EnvConfig:
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    MODEL_NAME = os.getenv("MODEL_NAME", "imdb_sentiment_model")
    MODEL_STAGE = os.getenv("MODEL_STAGE", "Production")
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
