"""Shared BERATools history persistence for plugin UI.

This module intentionally mirrors the JSON file/schema used by BERATools GUI:
~/.beratools/.data/saved_tool_parameters.json
"""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path


class BERAToolsHistoryStore:
    """Read/write tool history in BERATools-compatible JSON format."""

    def __init__(self, settings_path: Path | None = None):
        if settings_path is None:
            settings_path = (
                Path.home() / ".beratools" / ".data" / "saved_tool_parameters.json"
            )
        self.settings_path = Path(settings_path)

    def _ensure_parent_dir(self):
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_settings(self):
        if not self.settings_path.exists():
            return {}

        try:
            with self.settings_path.open("r", encoding="utf-8") as f:
                data = json.load(f, object_pairs_hook=OrderedDict)
        except (OSError, json.JSONDecodeError):
            return {}

        return data if isinstance(data, dict) else {}

    def _write_settings(self, data):
        self._ensure_parent_dir()
        with self.settings_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def _sanitize_history(raw_history):
        if not isinstance(raw_history, dict):
            return OrderedDict()

        cleaned = OrderedDict()
        for key, value in raw_history.items():
            if key is None or key == "null":
                continue
            cleaned[str(key)] = value if isinstance(value, dict) else {}
        return cleaned

    def get_tool_history(self):
        data = self._load_settings()
        return self._sanitize_history(data.get("tool_history"))

    def get_recent_tool(self):
        data = self._load_settings()
        gui_params = data.get("gui_parameters")
        if not isinstance(gui_params, dict):
            return None
        recent_tool = gui_params.get("recent_tool")
        return str(recent_tool) if recent_tool else None

    def add_tool_history(self, tool_api, params):
        if not tool_api:
            return

        data = self._load_settings()
        history = self._sanitize_history(data.get("tool_history"))

        history[str(tool_api)] = params if isinstance(params, dict) else {}
        history.move_to_end(str(tool_api), last=False)
        data["tool_history"] = history

        self._write_settings(data)

    def remove_tool_history_item(self, index):
        data = self._load_settings()
        history = self._sanitize_history(data.get("tool_history"))

        keys = list(history.keys())
        if index < 0 or index >= len(keys):
            return

        history.pop(keys[index], None)
        data["tool_history"] = history
        self._write_settings(data)

    def remove_tool_history_all(self):
        data = self._load_settings()
        data.pop("tool_history", None)
        self._write_settings(data)

    def save_recent_tool(self, recent_tool):
        if not recent_tool:
            return

        data = self._load_settings()
        gui_params = data.get("gui_parameters")
        if not isinstance(gui_params, dict):
            gui_params = {}

        gui_params["recent_tool"] = str(recent_tool)
        data["gui_parameters"] = gui_params
        self._write_settings(data)
