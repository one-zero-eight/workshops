import os
from pathlib import Path

from src.config_schema import Settings
from dotenv import load_dotenv

load_dotenv()

settings_path = os.getenv("SETTINGS_PATH", "setting.yaml")
settings: Settings = Settings.from_yaml(Path(settings_path))
