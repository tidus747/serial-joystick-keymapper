from __future__ import annotations

import json
from pathlib import Path

from app.core.models import AppConfig
from .schema import config_from_dict, config_to_dict


class ProfileManager:
    def __init__(self, profiles_dir: Path) -> None:
        self._profiles_dir = profiles_dir
        self._profiles_dir.mkdir(parents=True, exist_ok=True)

    @property
    def profiles_dir(self) -> Path:
        return self._profiles_dir

    def list_profiles(self) -> list[str]:
        return sorted(path.stem for path in self._profiles_dir.glob("*.json"))

    def load(self, name: str) -> AppConfig:
        path = self._profiles_dir / f"{name}.json"
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return config_from_dict(data)

    def save(self, name: str, config: AppConfig) -> Path:
        safe_name = name.strip() or "default"
        path = self._profiles_dir / f"{safe_name}.json"
        data = config_to_dict(config)
        data["profile_name"] = safe_name
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        return path
