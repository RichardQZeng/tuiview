"""
Dock widget classes for BERATools plugin.

Contains two main panels:
- BERAToolsPanel: Tool selection, parameter input, execution controls
- LogPanel: Tool execution output and progress display
"""

import re
import shlex

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QScrollArea, QPushButton, QPlainTextEdit, QProgressBar, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QProcess, Slot, QTimer

# Import data manager, widgets, and executor
try:
    # When imported as part of package
    from .beratools_data import BERAToolsManager
    from .beratools_widgets import create_parameter_widget
    from .beratools_executor import BERAToolExecutor
except ImportError:
    # When imported directly or from tests
    from beratools_data import BERAToolsManager
    from beratools_widgets import create_parameter_widget
    from beratools_executor import BERAToolExecutor


class BERAToolsPanel(QDockWidget):
    """
    Main BERATools dock panel.
    
    Contains:
    - Tool selection tree
    - Parameter input widgets
    - Run/Stop buttons
    """
    
    # Signals
    output_received = Signal(str)  # Emitted when tool produces output
    progress_updated = Signal(int)  # Emitted when progress updates
    tool_selected = Signal(str)  # Emitted when user selects a tool
    status_message = Signal(str)  # Emitted for UI status updates
    
    def __init__(self, parent=None):
        """Initialize BERATools panel."""
        super().__init__("BERATools", parent)
        
        # Load tools metadata
        self.manager = BERAToolsManager()
        self.executor = BERAToolExecutor()
        self.selected_tool = None
        self.selected_tool_api = None
        self.param_widgets = {}  # Store references to parameter widgets
        self.current_process = None  # Current running QProcess
        self.all_tool_names = []  # For search filtering
        
        # Create main widget and layout
        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title
        layout.addWidget(QLabel("Select Tool:"))
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search tools...")
        self.search_box.setMaximumHeight(25)
        self.search_box.textChanged.connect(self._on_search_text_changed)
        layout.addWidget(self.search_box)
        
        # Tree widget for tools
        self.tool_tree = QTreeWidget()
        self.tool_tree.setHeaderHidden(True)
        self.tool_tree.setColumnCount(1)
        self.tool_tree.setMaximumHeight(150)
        layout.addWidget(self.tool_tree)
        
        # Populate tree
        self._populate_tool_tree()
        
        # Connect tree selection signal
        self.tool_tree.itemClicked.connect(self._on_tool_selected)
        
        # Parameters section
        layout.addWidget(QLabel("Parameters:"))
        
        # Scroll area for parameters
        self.params_scroll = QScrollArea()
        self.params_scroll.setWidgetResizable(True)
        self.params_scroll.setStyleSheet("QScrollArea { border: none; }")
        
        # Container for parameter widgets
        self.params_container = QWidget()
        self.params_layout = QVBoxLayout()
        self.params_layout.setContentsMargins(0, 0, 0, 0)
        self.params_layout.setSpacing(2)
        self.params_container.setLayout(self.params_layout)
        self.params_scroll.setWidget(self.params_container)
        
        layout.addWidget(self.params_scroll)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.status_label)
        
        # Control buttons (top row)
        button_layout1 = QHBoxLayout()
        
        self.load_defaults_btn = QPushButton("Load Defaults")
        self.load_defaults_btn.clicked.connect(self._on_load_defaults_clicked)
        self.load_defaults_btn.setMaximumWidth(100)
        button_layout1.addWidget(self.load_defaults_btn)
        
        button_layout1.addStretch()
        layout.addLayout(button_layout1)
        
        # Control buttons (bottom row)
        button_layout2 = QHBoxLayout()
        
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._on_run_clicked)
        button_layout2.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setEnabled(False)
        button_layout2.addWidget(self.stop_btn)
        
        button_layout2.addStretch()
        layout.addLayout(button_layout2)
        
        main_widget.setLayout(layout)
        self.setWidget(main_widget)
        
        # Panel properties
        self.setObjectName("BERAToolsPanel")
        self.setMinimumWidth(300)
        self.setMinimumHeight(400)
        
        # Status update signal
        self.status_message.connect(self._on_status_message)
    
    def _populate_tool_tree(self):
        """Populate tree widget from metadata."""
        self.tool_tree.clear()
        self.all_tool_names.clear()
        
        # Get organized tools
        tools_by_category = self.manager.get_all_tools()
        
        if not tools_by_category:
            # Handle missing beratools.json
            error_item = QTreeWidgetItem()
            error_item.setText(0, "ERROR: beratools.json not found")
            self.tool_tree.addTopLevelItem(error_item)
            self.status_message.emit("ERROR: Could not load tools metadata")
            print("[BERATools] ERROR: No tools loaded from metadata")
            return
        
        for category in self.manager.toolbox_list:
            # Create category node
            category_item = QTreeWidgetItem()
            category_item.setText(0, category)
            category_item.setExpanded(True)
            self.tool_tree.addTopLevelItem(category_item)
            
            # Add tools under category
            tools = tools_by_category.get(category, [])
            for tool_name in tools:
                self.all_tool_names.append(tool_name)  # Track for search
                tool_item = QTreeWidgetItem()
                tool_item.setText(0, tool_name)
                tool_item.setData(0, Qt.UserRole, tool_name)  # Store tool name for later
                category_item.addChild(tool_item)
        
        # Expand all categories by default
        self.tool_tree.expandAll()
        
        if self.all_tool_names:
            self.status_message.emit(f"Loaded {len(self.all_tool_names)} tools")
            print(f"[BERATools] Loaded {len(self.all_tool_names)} tools from metadata")
    
    def _on_search_text_changed(self, search_text):
        """Filter tool tree based on search text (Task 9.1)."""
        search_text = search_text.lower().strip()
        
        # Iterate through all top-level categories
        for i in range(self.tool_tree.topLevelItemCount()):
            category_item = self.tool_tree.topLevelItem(i)
            category_visible = False
            
            # Check each tool in the category
            for j in range(category_item.childCount()):
                tool_item = category_item.child(j)
                tool_name = tool_item.text(0).lower()
                
                # Show item if search text matches
                matches = search_text in tool_name if search_text else True
                tool_item.setHidden(not matches)
                
                if matches:
                    category_visible = True
            
            # Show category if any tool matches
            category_item.setHidden(not category_visible)
    
    def _on_status_message(self, message):
        """Update status label with message (Task 9.1)."""
        self.status_label.setText(message)
        print(f"[Status] {message}")
    
    def _on_tool_selected(self, item, column):
        """
        Handle tool selection in the tree.
        
        Args:
            item: QTreeWidgetItem that was clicked
            column: Column index (always 0)
        """
        # Get parent item to check if this is a tool (not a category)
        parent = item.parent()
        
        # Only process if this is a child item (tool), not a category
        if parent is None:
            return  # Clicked on a category, ignore
        
        # Get tool name from the item's data
        tool_name = item.data(0, Qt.UserRole)
        
        if tool_name:
            self.selected_tool = tool_name
            
            # Get tool_api from metadata
            tool = self.manager.get_tool(tool_name)
            if tool:
                self.selected_tool_api = tool.get("tool_api", "")
            
            print(f"[BERATools] Selected tool: {tool_name} (api: {self.selected_tool_api})")
            
            # Load and display parameters
            self._load_tool_parameters(tool_name)
            
            # Emit signal
            self.tool_selected.emit(tool_name)
    
    def _load_tool_parameters(self, tool_name):
        """
        Load and display parameters for the selected tool.
        
        Args:
            tool_name (str): Selected tool name
        """
        # Clear previous parameters
        while self.params_layout.count():
            widget = self.params_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        self.param_widgets.clear()
        
        # Get tool parameters from metadata
        parameters = self.manager.get_tool_parameters(tool_name)
        
        if not parameters:
            print(f"[BERATools] No parameters for tool: {tool_name}")
            return
        
        # Create widgets for each parameter
        for param_def in parameters:
            try:
                widget = create_parameter_widget(param_def, self)
                if widget:
                    # Store reference using variable name
                    variable = param_def.get("variable", "")
                    if variable:
                        self.param_widgets[variable] = widget
                    
                    self.params_layout.addWidget(widget)
                    print(f"[BERATools] Added parameter widget: {param_def.get('label', 'unknown')}")
            except Exception as e:
                print(f"[BERATools] Error creating widget for parameter: {e}")
        
        # Add stretch at the end
        self.params_layout.addStretch()
        
        print(f"[BERATools] Loaded {len(self.param_widgets)} parameter widgets for {tool_name}")
    
    def get_tool_parameters(self):
        """
        Get current parameter values from all widgets.
        
        Returns:
            dict: {variable: value, ...} or None if required params missing
        """
        params = {}
        for variable, widget in self.param_widgets.items():
            try:
                value_dict = widget.get_value()
                params.update(value_dict)
            except Exception as e:
                print(f"[BERATools] Error getting value from {variable}: {e}")
        
        return params if params else None
    
    def _on_load_defaults_clicked(self):
        """Load default values for all parameters (Task 9.1)."""
        if not self.selected_tool:
            self.status_message.emit("No tool selected")
            return
        
        try:
            for widget in self.param_widgets.values():
                widget.set_default_value()
            
            self.status_message.emit(f"Defaults loaded for {self.selected_tool}")
            print(f"[BERATools] Loaded default values for {self.selected_tool}")
        except Exception as e:
            error_msg = f"Error loading defaults: {e}"
            self.status_message.emit(error_msg)
            print(f"[BERATools] {error_msg}")
            QMessageBox.warning(self, "Error", error_msg)
    
    def _on_run_clicked(self):
        """Handle Run button click (Task 9.2: Validation)."""
        if not self.selected_tool:
            self.status_message.emit("ERROR: No tool selected")
            return
        
        # Get parameter values
        params = self.get_tool_parameters()
        if not params:
            self.status_message.emit("ERROR: No parameters available")
            return
        
        # Validate parameters before execution
        validation_errors = self._validate_parameters()
        if validation_errors:
            error_msg = "Parameter validation failed:\n" + "\n".join(validation_errors)
            self.status_message.emit("ERROR: Validation failed")
            QMessageBox.warning(self, "Validation Error", error_msg)
            print(f"[BERATools] Validation errors:\n{error_msg}")
            return
        
        self.status_message.emit(f"Running {self.selected_tool}...")
        print(f"[BERATools] Running tool: {self.selected_tool}")
        print(f"[BERATools] Parameters: {params}")
        
        # Start subprocess
        self._start_process()
        
        # Disable Run button, enable Stop button (Task 9.1)
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
    
    def _validate_parameters(self):
        """
        Validate all parameter values before execution (Task 9.2).
        
        Returns:
            list: List of error messages (empty if all valid)
        """
        errors = []
        tool = self.manager.get_tool(self.selected_tool)
        if not tool:
            return ["Tool definition not found"]
        
        tool_params = tool.get("parameters", [])
        
        for param_def in tool_params:
            variable = param_def.get("variable", "")
            optional = param_def.get("optional", False)
            label = param_def.get("label", variable)
            
            if variable not in self.param_widgets:
                if not optional:
                    errors.append(f"Required parameter missing: {label}")
                continue
            
            try:
                widget = self.param_widgets[variable]
                value_dict = widget.get_value()
                value = value_dict.get(variable, "")
                
                # Check required parameters
                if not optional and not value:
                    errors.append(f"Required parameter empty: {label}")
                
                # Type-specific validation
                param_type = param_def.get("type", "")
                if param_type == "file" and value:
                    # Check if file exists for input files
                    if not param_def.get("output", False):
                        from pathlib import Path
                        if not Path(value).exists():
                            errors.append(f"Input file does not exist: {label} ({value})")
                
                elif param_type == "number" and value:
                    # Validate number format
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"Invalid number format: {label} ({value})")
            
            except Exception as e:
                errors.append(f"Error validating {label}: {e}")
        
        return errors
    
    def _start_process(self):
        """Start BERATool subprocess (Task 9.2: Error handling)."""
        if self.current_process:
            self.status_message.emit("ERROR: A process is already running")
            print("[BERATools] A process is already running")
            return
        
        if not self.selected_tool_api:
            self.status_message.emit("ERROR: No tool API available")
            print("[BERATools] No tool API available")
            return
        
        # Get current parameters
        params = self.get_tool_parameters()
        if not params:
            self.status_message.emit("ERROR: No parameters to execute")
            print("[BERATools] No parameters to execute")
            return
        
        # Build command using executor
        try:
            program, args = self.executor.build_command(self.selected_tool_api, params)
            
            if not program or not args:
                self.status_message.emit("ERROR: Failed to build tool command")
                print("[BERATools] Failed to build tool command")
                return
        except Exception as e:
            error_msg = f"Error building command: {e}"
            self.status_message.emit(f"ERROR: {error_msg}")
            print(f"[BERATools] {error_msg}")
            QMessageBox.critical(self, "Execution Error", error_msg)
            return
        
        # Create and start process
        self.current_process = QProcess()
        self.current_process.readyReadStandardOutput.connect(self._handle_stdout)
        self.current_process.readyReadStandardError.connect(self._handle_stderr)
        self.current_process.finished.connect(self._handle_process_finished)
        
        print(f"[BERATools] Starting process: {program} {' '.join(args[:3])}...")
        self.current_process.start(program, args)
        
        if not self.current_process.waitForStarted(3000):
            error_msg = "Failed to start process"
            self.status_message.emit(f"ERROR: {error_msg}")
            print(f"[BERATools] {error_msg}")
            self.current_process = None
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            QMessageBox.critical(self, "Execution Error", error_msg)
    
    def _handle_stdout(self):
        """Handle stdout from subprocess."""
        data = self.current_process.readAllStandardOutput()
        text = bytes(data).decode('utf8', errors='ignore')
        if text:
            # Parse for progress indicators
            self._parse_progress(text)
            # Emit the output
            self.output_received.emit(text)
    
    def _handle_stderr(self):
        """Handle stderr from subprocess (Task 9.2: Error handling)."""
        data = self.current_process.readAllStandardError()
        text = bytes(data).decode('utf8', errors='ignore')
        if text:
            print(f"[STDERR] {text.strip()}")
            self.output_received.emit(f"[ERROR] {text}")  # Prefix errors in log
    
    def _parse_progress(self, output_text):
        """
        Parse tool output for progress indicators.
        
        Looks for:
        1. Percentage: "50%" or "Processing... 50%" → extract 50
        2. PROGRESS_LABEL: "PROGRESS_LABEL 'Processing data'" → emit label
        
        Based on BERATools' custom_callback from bt_gui_main.py.
        
        Args:
            output_text (str): Output line from tool
        """
        output_text = str(output_text).strip()
        
        if not output_text:
            return
        
        # Remove ANSI escape sequences
        output_text = re.sub(r'\x1b\[0m', '', output_text)
        
        # Check for percentage progress
        if "%" in output_text:
            try:
                # Extract all numbers followed by % sign
                matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', output_text)
                if matches:
                    # Take the last percentage found (most recent)
                    progress = int(float(matches[-1]))
                    if 0 <= progress <= 100:
                        print(f"[Progress] {progress}%")
                        self.progress_updated.emit(progress)
            except (ValueError, IndexError):
                pass
        
        # Check for PROGRESS_LABEL
        if "PROGRESS_LABEL" in output_text:
            try:
                # Extract quoted string after PROGRESS_LABEL
                # Pattern: PROGRESS_LABEL "message" or PROGRESS_LABEL 'message'
                match = re.search(r'PROGRESS_LABEL\s+["\']([^"\']*)["\']', output_text)
                if match:
                    label_text = match.group(1)
                    print(f"[Progress Label] {label_text}")
                    # Could emit a separate signal for label, but for now just log
            except Exception:
                pass
    
    def _handle_process_finished(self):
        """Handle process completion (Task 9.2: Error handling)."""
        exit_code = self.current_process.exitCode()
        print(f"[BERATools] Process finished with exit code: {exit_code}")
        
        if exit_code == 0:
            print("[BERATools] Tool completed successfully")
            self.status_message.emit(f"✓ {self.selected_tool} completed successfully")
            self.output_received.emit("\n[SUCCESS] Tool completed successfully\n")
            self._handle_tool_success()
        else:
            error_msg = f"Tool failed with exit code {exit_code}"
            print(f"[BERATools] {error_msg}")
            self.status_message.emit(f"✗ {error_msg}")
            self.output_received.emit(f"\n[FAILURE] {error_msg}\n")
        
        self.current_process = None
        
        # Re-enable Run button
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def _handle_tool_success(self):
        """Handle successful tool completion."""
        # Find output file parameters
        output_files = {}
        for variable, widget in self.param_widgets.items():
            param_def = self.manager.get_tool(self.selected_tool)
            if not param_def:
                continue
            
            # Look through tool parameters for output files
            params = param_def.get("parameters", [])
            for param in params:
                if param.get("variable") == variable and param.get("output", False):
                    # This is an output parameter
                    try:
                        value_dict = widget.get_value()
                        if variable in value_dict:
                            output_files[variable] = value_dict[variable]
                    except Exception:
                        pass
        
        if output_files:
            print(f"[BERATools] Output files available: {output_files}")
            # Log message about importing outputs
            msg = "Tool completed. Output files ready for import:"
            for var, path in output_files.items():
                msg += f"\n  - {path}"
            print(f"[BERATools] {msg}")
    
    def _on_stop_clicked(self):
        """Handle Stop button click."""
        if self.current_process:
            print("[BERATools] Stopping process...")
            self.current_process.terminate()
        
        # Re-enable Run button
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)


class LogPanel(QDockWidget):
    """
    Log and progress dock panel.
    
    Contains:
    - Execution log (text output)
    - Progress bar
    """
    
    def __init__(self, parent=None):
        """Initialize log panel."""
        super().__init__("Execution Log", parent)
        
        # Create main widget and layout
        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Progress bar with label
        progress_layout = QHBoxLayout()
        progress_label = QLabel("Progress:")
        progress_label.setMaximumWidth(60)
        progress_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addLayout(progress_layout)
        
        # Log text area
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        # Set monospace font for better output formatting
        font = self.log_text.font()
        font.setFamily("Consolas" if font.family() == "Consolas" else "Courier New")
        self.log_text.setFont(font)
        layout.addWidget(self.log_text)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setMaximumWidth(80)
        clear_btn.clicked.connect(self.clear_log)
        layout.addWidget(clear_btn)
        
        main_widget.setLayout(layout)
        self.setWidget(main_widget)
        
        # Panel properties
        self.setObjectName("LogPanel")
        self.setMinimumWidth(300)
        self.setMinimumHeight(200)
    
    @Slot(str)
    def append_log(self, text):
        """
        Append text to the log display with formatting (Task 9.1).
        
        Args:
            text (str): Text to append
        """
        if text:
            # Add timestamp for cleaner output
            text = text.rstrip()
            self.log_text.appendPlainText(text)
    
    @Slot(int)
    def set_progress(self, value):
        """
        Set progress bar value.
        
        Args:
            value (int): Progress percentage (0-100)
        """
        self.progress_bar.setValue(value)
    
    def clear_log(self):
        """Clear all log text."""
        self.log_text.clear()
        self.progress_bar.setValue(0)
