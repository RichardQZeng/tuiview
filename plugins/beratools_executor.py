"""
BERATool executor - handles building and running tool commands.

Reuses logic from BERATools' bt_data.py prepare_tool_run().
"""

import json
from pathlib import Path


class BERAToolExecutor:
    """Builds and manages BERATool subprocess commands."""

    def __init__(self):
        """Initialize executor."""
        self.beratools_dir = self._find_beratools_dir()
        self.cpu_cores = -1  # Default: use all cores

    def _find_beratools_dir(self):
        """
        Find BERATools installation directory.

        Returns:
            Path: BERATools directory, or None if not found
        """
        # Try to find BERATools in installed package first
        try:
            import beratools
            from pathlib import Path as _Path
            beratools_dir = _Path(beratools.__file__).parent
            if (beratools_dir / "tools").exists():
                print(f"[BERATools] Found BERATools at {beratools_dir} (installed package)")
                return beratools_dir
        except Exception as e:
            print(f"[BERATools] Error loading installed package: {e}")

        # Fallback to previous locations
        possible_dirs = [
            Path(__file__).parent.parent.parent / "beratools" / "beratools",
            Path.home() / ".beratools" / "beratools",
        ]

        for dir_path in possible_dirs:
            if (dir_path / "tools").exists():
                print(f"[BERATools] Found BERATools at {dir_path}")
                return dir_path

        print("[BERATools] WARNING: BERATools directory not found")
        return None

    def build_command(self, tool_api, parameters):
        """
        Build a tool execution command.

        Args:
            tool_api (str): Tool API name (e.g., 'centerline')
            parameters (dict): Tool parameters {variable: value, ...}

        Returns:
            tuple: (program, args_list) for QProcess.start()
                  or (None, None) if build fails
        """
        if not self.beratools_dir:
            print("[BERATools] ERROR: BERATools directory not found")
            return None, None

        # Build the tool script path
        tool_script = self.beratools_dir / "tools" / f"{tool_api}.py"

        if not tool_script.exists():
            print(f"[BERATools] ERROR: Tool script not found: {tool_script}")
            return None, None

        # Convert parameters to JSON string
        try:
            # Ensure string values, handle bool/int/float
            clean_params = {}
            for key, value in parameters.items():
                if isinstance(value, bool):
                    clean_params[key] = value
                elif isinstance(value, (int, float)):
                    clean_params[key] = value
                else:
                    clean_params[key] = str(value)

            args_json = json.dumps(clean_params)
        except Exception as e:
            print(f"[BERATools] ERROR building JSON args: {e}")
            return None, None

        # Build command: python tool_script.py -i <json> -p <cores> -c GUI -l INFO
        program = "python"
        args = [
            str(tool_script),
            "-i", args_json,
            "-p", str(self.cpu_cores),
            "-c", "GUI",
            "-l", "INFO"
        ]

        print(f"[BERATools] Built command: {program} {args}")

        return program, args

    def set_cpu_cores(self, cores):
        """
        Set number of CPU cores for tool execution.

        Args:
            cores (int): Number of cores, or -1 for all available
        """
        self.cpu_cores = cores

def name():
    return "BERATools Executor"

def author():
    return "BERATools Team"

def description():
    return "Handles building and running BERATool commands."

def action(actioncode, param):
    # This plugin does not implement actions
    pass
