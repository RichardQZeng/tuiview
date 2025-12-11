"""
Parameter widget classes for BERATools plugin.

Provides reusable widgets for different parameter types:
- Text input (QLineEdit)
- Numeric input (QSpinBox, QDoubleSpinBox)
- File selection (QLineEdit + QPushButton)
- Directory selection (QLineEdit + QPushButton)
- Options/List selection (QComboBox)

All widgets implement:
- get_value(): Returns {variable_name: value}
- set_value(value): Sets widget value
"""

from abc import abstractmethod
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QSpinBox,
    QDoubleSpinBox, QPushButton, QComboBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

# Try to import pyogrio for GeoPackage support
try:
    import pyogrio
    HAS_PYOGRIO = True
except ImportError:
    HAS_PYOGRIO = False


class ParameterWidget(QWidget):
    """
    Base class for all parameter widgets.
    
    Subclasses must implement get_value() and set_value().
    """
    
    # Minimum width for labels
    LABEL_MIN_WIDTH = 130
    
    def __init__(self, param_def, parent=None):
        """
        Initialize parameter widget.
        
        Args:
            param_def (dict): Parameter definition from beratools.json
                - variable: Parameter variable name
                - label: Display label
                - description: Parameter description
                - type: Parameter type (file, number, text, etc.)
                - default: Default value
                - optional: Whether parameter is optional
            parent: Parent widget
        """
        super().__init__(parent)
        self.param_def = param_def
        self.variable = param_def.get("variable", "")
        self.label_text = param_def.get("label", "")
        self.description = param_def.get("description", "")
        self.default_value = param_def.get("default", "")
        self.optional = param_def.get("optional", False)
        self.value = self.default_value
    
    @abstractmethod
    def get_value(self):
        """
        Get current widget value.
        
        Returns:
            dict: {variable_name: value}
        """
        pass
    
    @abstractmethod
    def set_value(self, value):
        """
        Set widget value.
        
        Args:
            value: Value to set
        """
        pass
    
    def set_default_value(self):
        """Reset widget to default value."""
        self.set_value(self.default_value)


def create_parameter_widget(param_def, parent=None):
    """
    Factory function to create appropriate widget for a parameter.
    
    Args:
        param_def (dict): Parameter definition from beratools.json
        parent: Parent widget
        
    Returns:
        ParameterWidget: Appropriate widget instance, or None if type unsupported
    """
    param_type = param_def.get("type", "")
    
    if param_type == "text":
        return TextParameterWidget(param_def, parent)
    elif param_type == "number":
        return NumberParameterWidget(param_def, parent)
    elif param_type == "file":
        return FileParameterWidget(param_def, parent)
    elif param_type == "directory":
        return DirectoryParameterWidget(param_def, parent)
    elif param_type == "list":
        return OptionsParameterWidget(param_def, parent)
    else:
        print(f"[BERATools] WARNING: Unsupported parameter type '{param_type}'")
        return None


# ============================================
# Concrete Widget Implementations
# ============================================

class TextParameterWidget(ParameterWidget):
    """Widget for text input parameters."""
    
    def __init__(self, param_def, parent=None):
        super().__init__(param_def, parent)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label = QLabel(self.label_text)
        label.setMinimumWidth(self.LABEL_MIN_WIDTH)
        layout.addWidget(label)
        
        # Text input
        self.text_input = QLineEdit()
        self.text_input.setToolTip(self.description)
        self.text_input.setText(str(self.default_value))
        self.text_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_input)
        
        self.setLayout(layout)
    
    def _on_text_changed(self):
        self.value = self.text_input.text()
    
    def get_value(self):
        return {self.variable: self.value}
    
    def set_value(self, value):
        self.value = str(value) if value else ""
        self.text_input.setText(self.value)


class NumberParameterWidget(ParameterWidget):
    """Widget for numeric (int/float) input parameters."""
    
    def __init__(self, param_def, parent=None):
        super().__init__(param_def, parent)
        
        # Determine if int or float
        subtypes = param_def.get("subtype", [])
        if isinstance(subtypes, str):
            subtypes = [subtypes]
        
        self.is_float = "float" in subtypes
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label = QLabel(self.label_text)
        label.setMinimumWidth(self.LABEL_MIN_WIDTH)
        layout.addWidget(label)
        
        # Numeric input
        if self.is_float:
            self.number_input = QDoubleSpinBox()
            self.number_input.setMinimum(-999999.0)
            self.number_input.setMaximum(999999.0)
            self.number_input.setSingleStep(0.1)
            try:
                self.number_input.setValue(float(self.default_value))
            except (ValueError, TypeError):
                self.number_input.setValue(0.0)
        else:
            self.number_input = QSpinBox()
            self.number_input.setMinimum(-999999)
            self.number_input.setMaximum(999999)
            self.number_input.setSingleStep(1)
            try:
                self.number_input.setValue(int(self.default_value))
            except (ValueError, TypeError):
                self.number_input.setValue(0)
        
        self.number_input.setToolTip(self.description)
        self.number_input.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.number_input)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def _on_value_changed(self):
        self.value = self.number_input.value()
    
    def get_value(self):
        return {self.variable: self.value}
    
    def set_value(self, value):
        try:
            if self.is_float:
                self.value = float(value)
                self.number_input.setValue(float(value))
            else:
                self.value = int(value)
                self.number_input.setValue(int(value))
        except (ValueError, TypeError):
            if self.is_float:
                self.number_input.setValue(0.0)
            else:
                self.number_input.setValue(0)


class OptionsParameterWidget(ParameterWidget):
    """Widget for list/options selection parameters."""
    
    def __init__(self, param_def, parent=None):
        super().__init__(param_def, parent)
        
        # Get options from parameter definition
        self.options = param_def.get("data", [])
        self.options = [str(opt) for opt in self.options]
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label = QLabel(self.label_text)
        label.setMinimumWidth(self.LABEL_MIN_WIDTH)
        layout.addWidget(label)
        
        # Combo box
        self.combo_box = QComboBox()
        self.combo_box.addItems(self.options)
        self.combo_box.setToolTip(self.description)
        self.combo_box.currentTextChanged.connect(self._on_selection_changed)
        
        # Set to default value if in options
        default_str = str(self.default_value)
        if default_str in self.options:
            self.combo_box.setCurrentText(default_str)
        
        layout.addWidget(self.combo_box)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def _on_selection_changed(self):
        self.value = self.combo_box.currentText()
    
    def get_value(self):
        return {self.variable: self.value}
    
    def set_value(self, value):
        self.value = str(value)
        if self.value in self.options:
            self.combo_box.setCurrentText(self.value)


class FileParameterWidget(ParameterWidget):
    """Widget for file selection (input/output)."""
    
    def __init__(self, param_def, parent=None):
        super().__init__(param_def, parent)
        
        self.output = param_def.get("output", False)
        self.subtypes = param_def.get("subtype", [])
        if isinstance(self.subtypes, str):
            self.subtypes = [self.subtypes]
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label = QLabel(self.label_text)
        label.setMinimumWidth(self.LABEL_MIN_WIDTH)
        layout.addWidget(label)
        
        # File path input (read-only)
        self.file_input = QLineEdit()
        self.file_input.setReadOnly(False)
        self.file_input.setText(str(self.default_value))
        self.file_input.setToolTip(self.description)
        self.file_input.textChanged.connect(self._on_path_changed)
        layout.addWidget(self.file_input)
        
        # Auto-fill button (only for input, non-output parameters)
        if not self.output:
            self.autofill_btn = QPushButton("Auto")
            self.autofill_btn.setMaximumWidth(40)
            self.autofill_btn.clicked.connect(self._on_autofill_clicked)
            self.autofill_btn.setToolTip("Fill from active TuiView layer")
            layout.addWidget(self.autofill_btn)
        
        # Browse button
        self.browse_btn = QPushButton("...")
        self.browse_btn.setMaximumWidth(40)
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        layout.addWidget(self.browse_btn)
        
        # Layer combo (for GeoPackage files)
        self.layer_combo = QComboBox()
        self.layer_combo.setVisible(False)
        self.layer_combo.setMaximumWidth(150)
        layout.addWidget(self.layer_combo)
        
        self.setLayout(layout)
    
    def _on_path_changed(self):
        self.value = self.file_input.text()
        
        # Check if path is a GeoPackage and update layer combo
        if self.value.lower().endswith('.gpkg'):
            self._load_gpkg_layers(self.value)
    
    def _on_autofill_clicked(self):
        """Auto-fill path from TuiView's active layer."""
        try:
            from PySide6.QtGui import QGuiApplication
            app = QGuiApplication.instance()
            
            # Try to find viewer window and get active layer
            if hasattr(app, 'viewerwindow'):
                viewer = app.viewerwindow
                if hasattr(viewer, 'viewwidget') and hasattr(viewer.viewwidget, 'layers'):
                    current_layer = viewer.viewwidget.layers.getCurrentLayer()
                    if current_layer and hasattr(current_layer, 'filename'):
                        self.set_value(current_layer.filename)
                        return
            
            print("[BERATools] Could not find active layer in TuiView")
        except Exception as e:
            print(f"[BERATools] Auto-fill error: {e}")
    
    def _on_browse_clicked(self):
        """Open file dialog."""
        if self.output:
            # For output, allow saving new files
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                f"Select output {self.subtypes[0] if self.subtypes else 'file'}",
                "",
                self._get_file_filter()
            )
        else:
            # For input, select existing files
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                f"Select input {self.subtypes[0] if self.subtypes else 'file'}",
                "",
                self._get_file_filter()
            )
        
        if file_path:
            self.set_value(file_path)
    
    def _get_file_filter(self):
        """Get file dialog filter based on subtypes."""
        if not self.subtypes:
            return "All files (*.*)"
        
        subtype = self.subtypes[0]
        
        filters = {
            "vector": "Vector Files (*.gpkg *.shp)",
            "raster": "Raster Files (*.tif *.tiff *.jp2)",
            "lidar": "LiDAR Files (*.las *.laz)",
            "text": "Text Files (*.txt)",
            "csv": "CSV Files (*.csv)",
            "json": "JSON Files (*.json)",
        }
        
        return filters.get(subtype, "All files (*.*)")
    
    def get_value(self):
        return {self.variable: self.value}
    
    def _load_gpkg_layers(self, gpkg_path):
        """
        Load layers from a GeoPackage file and populate combo box.
        
        Args:
            gpkg_path (str): Path to GeoPackage file
        """
        if not HAS_PYOGRIO:
            print("[BERATools] pyogrio not available, cannot load GeoPackage layers")
            return
        
        try:
            path = Path(gpkg_path)
            if not path.exists():
                self.layer_combo.setVisible(False)
                return
            
            # Get layers from GeoPackage
            layers_info = pyogrio.list_layers(str(path))
            
            self.layer_combo.clear()
            layer_names = []
            
            # layers_info is an array of [name, geometry_type] pairs
            for layer_item in layers_info:
                if hasattr(layer_item, '__len__') and len(layer_item) >= 2:
                    layer_name = str(layer_item[0])
                    geom_type = str(layer_item[1])
                    display_name = f"{layer_name} ({geom_type})"
                    self.layer_combo.addItem(display_name, userData=layer_name)
                    layer_names.append(layer_name)
            
            if layer_names:
                self.layer_combo.setVisible(True)
                print(f"[BERATools] Loaded {len(layer_names)} layers from {path.name}")
            else:
                self.layer_combo.setVisible(False)
        
        except Exception as e:
            print(f"[BERATools] Error loading GeoPackage layers: {e}")
            self.layer_combo.setVisible(False)
    
    def set_value(self, value):
        self.value = str(value) if value else ""
        self.file_input.setText(self.value)
        
        # If it's a GeoPackage, load and show layers
        if self.value.lower().endswith('.gpkg'):
            self._load_gpkg_layers(self.value)


class DirectoryParameterWidget(ParameterWidget):
    """Widget for directory selection."""
    
    def __init__(self, param_def, parent=None):
        super().__init__(param_def, parent)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label = QLabel(self.label_text)
        label.setMinimumWidth(self.LABEL_MIN_WIDTH)
        layout.addWidget(label)
        
        # Directory path input
        self.dir_input = QLineEdit()
        self.dir_input.setReadOnly(False)
        self.dir_input.setText(str(self.default_value))
        self.dir_input.setToolTip(self.description)
        self.dir_input.textChanged.connect(self._on_path_changed)
        layout.addWidget(self.dir_input)
        
        # Browse button
        self.browse_btn = QPushButton("...")
        self.browse_btn.setMaximumWidth(40)
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        layout.addWidget(self.browse_btn)
        
        self.setLayout(layout)
    
    def _on_path_changed(self):
        self.value = self.dir_input.text()
    
    def _on_browse_clicked(self):
        """Open directory dialog."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select directory",
            str(self.default_value)
        )
        
        if dir_path:
            self.set_value(dir_path)
    
    def get_value(self):
        return {self.variable: self.value}
    
    def set_value(self, value):
        self.value = str(value) if value else ""
        self.dir_input.setText(self.value)
