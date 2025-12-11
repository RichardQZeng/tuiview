"""
BERATools metadata loader and manager.

Handles loading and parsing of beratools.json.
"""

import json
from pathlib import Path


class BERAToolsManager:
    """Manages BERATools metadata and tool definitions."""

    def __init__(self):
        """Initialize manager and load tools metadata."""
        self.tools_metadata = None
        self.tools_list = []  # Flat list of tool names
        self.sorted_tools = []  # Tools organized by category
        self.toolbox_list = []  # Category names

        self._load_tools_metadata()

    def _load_tools_metadata(self):
        """
        Load beratools.json from BERATools installation.

        Returns:
            dict: Parsed beratools.json, or None if not found
        """
        # Try multiple possible locations for beratools.json
        possible_paths = [
            Path(__file__).parent.parent.parent / "beratools" / "beratools" / "gui" / "assets" / "beratools.json",
            Path.home() / ".beratools" / "beratools.json",
        ]

        for json_path in possible_paths:
            if json_path.exists():
                try:
                    with open(json_path, 'r') as f:
                        self.tools_metadata = json.load(f)
                    print(f"[BERATools] Loaded metadata from {json_path}")
                    self._parse_metadata()
                    return self.tools_metadata
                except Exception as e:
                    print(f"[BERATools] Error reading {json_path}: {e}")
                    continue

        print("[BERATools] WARNING: beratools.json not found in any location")
        self.tools_metadata = {"toolbox": []}
        return self.tools_metadata

    def _parse_metadata(self):
        """Parse metadata to extract tool list and organization."""
        if not self.tools_metadata or "toolbox" not in self.tools_metadata:
            return

        self.tools_list = []
        self.sorted_tools = []
        self.toolbox_list = []

        for toolbox in self.tools_metadata["toolbox"]:
            category = toolbox.get("category", "")
            self.toolbox_list.append(category)

            category_tools = []
            for tool in toolbox.get("tools", []):
                tool_name = tool.get("name", "")
                if tool_name:
                    self.tools_list.append(tool_name)
                    category_tools.append(tool_name)

            self.sorted_tools.append(category_tools)

    def get_tool(self, tool_name):
        """
        Get tool definition by name.

        Args:
            tool_name (str): Tool display name

        Returns:
            dict: Tool definition, or None if not found
        """
        if not self.tools_metadata:
            return None

        for toolbox in self.tools_metadata.get("toolbox", []):
            for tool in toolbox.get("tools", []):
                if tool.get("name") == tool_name:
                    return tool

        return None

    def get_tool_parameters(self, tool_name):
        """
        Get parameters for a tool.

        Args:
            tool_name (str): Tool display name

        Returns:
            list: Tool parameters, or empty list if not found
        """
        tool = self.get_tool(tool_name)
        if tool:
            return tool.get("parameters", [])
        return []

    def get_all_tools(self):
        """
        Get all tools organized by category.

        Returns:
            dict: {"category_name": ["tool1", "tool2", ...], ...}
        """
        result = {}
        for category, tools in zip(self.toolbox_list, self.sorted_tools):
            result[category] = tools
        return result

def name():
    return "BERATools Data"

def author():
    return "BERATools Team"

def description():
    return "BERATools metadata loader and manager."

def action(actioncode, param):
    # This plugin does not implement actions
    pass
