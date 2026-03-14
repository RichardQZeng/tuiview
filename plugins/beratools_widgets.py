"""Parameter widget classes for BERATools plugin."""

from abc import abstractmethod
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

try:
    from .beratools_geometry_types import (
        format_expected_families,
        get_allowed_geometry_families,
        is_geometry_compatible,
        parse_subtype_tokens,
    )
except ImportError:
    from beratools_geometry_types import (
        format_expected_families,
        get_allowed_geometry_families,
        is_geometry_compatible,
        parse_subtype_tokens,
    )

# Try to import pyogrio for GeoPackage support
try:
    import pyogrio

    HAS_PYOGRIO = True
except ImportError:
    HAS_PYOGRIO = False
    pyogrio = None


def name():
    return "BERATools Widgets"


def author():
    return "BERATools Team"


def description():
    return "Reusable parameter widgets for BERATools plugin."


def action(actioncode, param):
    # This plugin does not implement actions
    pass


def _normalize_parameter_definition(param_def):
    """Normalize alternate parameter type names to plugin widget types."""
    normalized = dict(param_def)
    param_type = str(normalized.get("type", "")).strip().lower()

    # Support vector subtype names used by some BERATools metadata variants.
    vector_type_map = {
        "existing_vector": (False, "vector"),
        "new_vector": (True, "vector"),
        "existing_line_vector": (False, "vector|line"),
        "existing_polygon_vector": (False, "vector|polygon"),
        "existing_point_vector": (False, "vector|point"),
        "new_line_vector": (True, "vector|line"),
        "new_polygon_vector": (True, "vector|polygon"),
        "new_point_vector": (True, "vector|point"),
    }
    if param_type in vector_type_map:
        output, subtype = vector_type_map[param_type]
        normalized["type"] = "file"
        normalized["output"] = output
        normalized.setdefault("subtype", subtype)
        return normalized

    # Support numeric aliases.
    numeric_type_map = {
        "positive_float": "float",
        "positive_int": "int",
        "float": "float",
        "int": "int",
    }
    if param_type in numeric_type_map:
        normalized["type"] = "number"
        normalized.setdefault("subtype", numeric_type_map[param_type])
        return normalized

    return normalized


class ParameterWidget(QWidget):
    """Base class for all parameter widgets."""

    value_changed = Signal(str, object)

    # Minimum width for labels
    LABEL_MIN_WIDTH = 130

    def __init__(self, param_def, parent=None):
        super().__init__(parent)
        self.param_def = param_def
        self.variable = param_def.get("variable", "")
        self.label_text = param_def.get("label", "")
        self.description = param_def.get("description", "")
        self.default_value = param_def.get("default", "")
        self.optional = param_def.get("optional", False)
        self.depends_on = param_def.get("depends_on")
        self.value = self.default_value
        self.validation_error = ""

    @abstractmethod
    def get_value(self) -> dict[str, Any]:
        return {}

    @abstractmethod
    def set_value(self, value: Any):
        raise NotImplementedError

    def set_default_value(self):
        self.set_value(self.default_value)

    def emit_value_changed(self):
        self.value_changed.emit(self.variable, self.get_dependency_value())

    def get_dependency_value(self) -> Any:
        return self.value

    def get_validation_error(self) -> str:
        return self.validation_error

    def set_validation_error(self, message: str):
        self.validation_error = str(message) if message else ""

    def clear_validation_error(self):
        self.validation_error = ""


def create_parameter_widget(param_def, parent=None):
    """Factory function to create appropriate widget for a parameter."""
    normalized_param_def = _normalize_parameter_definition(param_def)
    param_type = str(normalized_param_def.get("type", "")).strip().lower()

    if param_type == "text":
        return TextParameterWidget(normalized_param_def, parent)
    if param_type == "number":
        return NumberParameterWidget(normalized_param_def, parent)
    if param_type == "file":
        return FileParameterWidget(normalized_param_def, parent)
    if param_type == "directory":
        return DirectoryParameterWidget(normalized_param_def, parent)
    if param_type == "list":
        return OptionsParameterWidget(normalized_param_def, parent)

    print(f"[BERATools] WARNING: Unsupported parameter type '{param_type}'")
    return None


class TextParameterWidget(ParameterWidget):
    """Widget for text input parameters."""

    def __init__(self, param_def, parent=None):
        super().__init__(param_def, parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self.label_text)
        label.setMinimumWidth(self.LABEL_MIN_WIDTH)
        layout.addWidget(label)

        self.text_input = QLineEdit()
        self.text_input.setToolTip(self.description)
        self.text_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_input)

        self.setLayout(layout)
        self.set_value(self.default_value)

    def _on_text_changed(self):
        self.value = self.text_input.text()
        self.emit_value_changed()

    def get_value(self):
        return {self.variable: self.value}

    def set_value(self, value):
        self.value = str(value) if value is not None else ""
        self.text_input.setText(self.value)


class NumberParameterWidget(ParameterWidget):
    """Widget for numeric (int/float) input parameters."""

    def __init__(self, param_def, parent=None):
        super().__init__(param_def, parent)

        subtype_tokens = parse_subtype_tokens(param_def.get("subtype", []))
        self.is_float = "float" in subtype_tokens
        self.unit = str(param_def.get("unit", "") or "")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self.label_text)
        label.setMinimumWidth(self.LABEL_MIN_WIDTH)
        layout.addWidget(label)

        if self.is_float:
            self.number_input = QDoubleSpinBox()
            self.number_input.setMinimum(-999999.0)
            self.number_input.setMaximum(999999.0)
            self.number_input.setSingleStep(0.1)
        else:
            self.number_input = QSpinBox()
            self.number_input.setMinimum(-999999)
            self.number_input.setMaximum(999999)
            self.number_input.setSingleStep(1)

        self.number_input.setToolTip(self.description)
        self.number_input.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.number_input)

        self.unit_label = QLabel(self.unit)
        self.unit_label.setVisible(bool(self.unit))
        self.unit_label.setToolTip(self.description)
        layout.addWidget(self.unit_label)
        layout.addStretch()

        self.setLayout(layout)
        self.set_value(self.default_value)

    def _on_value_changed(self):
        self.value = self.number_input.value()
        self.emit_value_changed()

    def get_value(self):
        return {self.variable: self.value}

    def set_value(self, value):
        try:
            if self.is_float:
                self.value = float(value)
                if isinstance(self.number_input, QDoubleSpinBox):
                    self.number_input.setProperty("value", self.value)
            else:
                self.value = int(value)
                if isinstance(self.number_input, QSpinBox):
                    self.number_input.setValue(self.value)
        except (ValueError, TypeError):
            fallback = 0.0 if self.is_float else 0
            self.value = fallback
            if self.is_float and isinstance(self.number_input, QDoubleSpinBox):
                self.number_input.setProperty("value", float(fallback))
            elif not self.is_float and isinstance(self.number_input, QSpinBox):
                self.number_input.setValue(int(fallback))


class OptionsParameterWidget(ParameterWidget):
    """Widget for list/options selection parameters."""

    def __init__(self, param_def, parent=None):
        super().__init__(param_def, parent)

        self.options = list(param_def.get("data", []))
        self.option_labels = [str(opt) for opt in self.options]

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self.label_text)
        label.setMinimumWidth(self.LABEL_MIN_WIDTH)
        layout.addWidget(label)

        self.combo_box = QComboBox()
        self.combo_box.addItems(self.option_labels)
        self.combo_box.setToolTip(self.description)
        self.combo_box.currentIndexChanged.connect(self._on_selection_changed)

        layout.addWidget(self.combo_box)
        layout.addStretch()

        self.setLayout(layout)
        self.set_value(self.default_value)

    def _on_selection_changed(self, index):
        if 0 <= index < len(self.options):
            self.value = self.options[index]
        elif self.options:
            self.value = self.options[0]
        else:
            self.value = ""
        self.emit_value_changed()

    def get_value(self):
        return {self.variable: self.value}

    def set_value(self, value):
        if not self.options:
            self.value = ""
            return

        target_index = -1
        for idx, opt in enumerate(self.options):
            if value == opt or str(value) == str(opt):
                target_index = idx
                break

        if target_index < 0:
            target_index = 0

        self.combo_box.setCurrentIndex(target_index)
        self.value = self.options[target_index]

    def get_dependency_value(self):
        return self.value


class FileParameterWidget(ParameterWidget):
    """Widget for file selection (input/output)."""

    NO_COMPATIBLE_LAYER_TEXT = "(No compatible layers)"

    def __init__(self, param_def, parent=None):
        super().__init__(param_def, parent)

        self.output = param_def.get("output", False)
        self.subtype_tokens = parse_subtype_tokens(param_def.get("subtype", []))
        self.allowed_geometry_families = get_allowed_geometry_families(
            self.subtype_tokens
        )
        self.is_vector = "vector" in self.subtype_tokens
        self.selected_layer = ""

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self.label_text)
        label.setMinimumWidth(self.LABEL_MIN_WIDTH)
        layout.addWidget(label)

        self.file_input = QLineEdit()
        self.file_input.setReadOnly(False)
        self.file_input.setToolTip(self.description)
        self.file_input.textChanged.connect(self._on_path_changed)
        layout.addWidget(self.file_input)

        self.browse_btn = QPushButton("...")
        self.browse_btn.setMaximumWidth(40)
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        layout.addWidget(self.browse_btn)

        self.layer_combo = QComboBox()
        self.layer_combo.setVisible(False)
        self.layer_combo.setMaximumWidth(180)
        self.layer_combo.currentIndexChanged.connect(self._on_layer_changed)
        layout.addWidget(self.layer_combo)

        self.setLayout(layout)
        self.set_value(self.default_value)

    def _split_path_and_layer(self, value):
        if isinstance(value, str) and "|" in value:
            path, layer = value.rsplit("|", 1)
            return path.strip(), layer.strip()
        return (str(value).strip() if value else "", "")

    def _on_path_changed(self):
        self.value = self.file_input.text().strip()
        self._refresh_vector_state()
        self.emit_value_changed()

    def _on_layer_changed(self, _index):
        self.selected_layer = self._current_layer_name()
        self.emit_value_changed()

    def _on_browse_clicked(self):
        """Open file dialog."""
        if self.output:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                f"Select output {self.subtype_tokens[0] if self.subtype_tokens else 'file'}",
                "",
                self._get_file_filter(),
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                f"Select input {self.subtype_tokens[0] if self.subtype_tokens else 'file'}",
                "",
                self._get_file_filter(),
            )

        if file_path:
            self.set_value(file_path)

    def _get_file_filter(self):
        """Get file dialog filter based on subtypes."""
        if not self.subtype_tokens:
            return "All files (*.*)"

        if "vector" in self.subtype_tokens:
            return "Vector Files (*.gpkg *.shp)"
        if "raster" in self.subtype_tokens:
            return "Raster Files (*.tif *.tiff *.jp2)"
        if "lidar" in self.subtype_tokens:
            return "LiDAR Files (*.las *.laz)"
        if "text" in self.subtype_tokens:
            return "Text Files (*.txt)"
        if "csv" in self.subtype_tokens:
            return "CSV Files (*.csv)"
        if "json" in self.subtype_tokens:
            return "JSON Files (*.json)"

        return "All files (*.*)"

    def _set_input_geometry_warning(self, message):
        self.set_validation_error(message)
        self.file_input.setToolTip(message)
        self.file_input.setStyleSheet("QLineEdit { background-color: #f8d7da; }")

    def _clear_input_geometry_warning(self):
        self.clear_validation_error()
        self.file_input.setToolTip(self.description)
        self.file_input.setStyleSheet("")

    def _set_no_compatible_layer_placeholder(self):
        self.layer_combo.clear()
        self.layer_combo.setEditable(False)
        self.layer_combo.addItem(self.NO_COMPATIBLE_LAYER_TEXT)
        self.layer_combo.setVisible(True)

    @staticmethod
    def _layer_name_from_display(display_text):
        if (
            not display_text
            or display_text == FileParameterWidget.NO_COMPATIBLE_LAYER_TEXT
        ):
            return ""
        if " (" in display_text:
            return display_text.split(" (", 1)[0]
        return display_text

    def _current_layer_name(self):
        if not self.layer_combo.isVisible():
            return self.selected_layer
        if self.layer_combo.isEditable():
            return self._layer_name_from_display(self.layer_combo.currentText())

        data = self.layer_combo.currentData(Qt.ItemDataRole.UserRole)
        if data:
            return str(data)
        return self._layer_name_from_display(self.layer_combo.currentText())

    def _validate_shp_input_geometry(self, path):
        if self.output or not self.allowed_geometry_families:
            self._clear_input_geometry_warning()
            return

        file_path = Path(path)
        if not file_path.exists():
            self._clear_input_geometry_warning()
            return

        if not HAS_PYOGRIO:
            self._clear_input_geometry_warning()
            return

        pyogrio_mod = pyogrio
        if pyogrio_mod is None:
            self._clear_input_geometry_warning()
            return

        try:
            info = pyogrio_mod.read_info(str(file_path))
            geometry_type = info.get("geometry_type")
        except Exception as exc:
            self._set_input_geometry_warning(
                f"Could not read shapefile geometry type: {exc}"
            )
            return

        if is_geometry_compatible(geometry_type, self.allowed_geometry_families):
            self._clear_input_geometry_warning()
            return

        expected = format_expected_families(self.allowed_geometry_families)
        detected = geometry_type if geometry_type else "Unknown"
        self._set_input_geometry_warning(
            f"Geometry mismatch: expected {expected}, found {detected}"
        )

    def _refresh_vector_state(self):
        path_text = self.file_input.text().strip()
        self.value = path_text

        if not self.is_vector:
            self.layer_combo.setVisible(False)
            self._clear_input_geometry_warning()
            return

        is_gpkg = path_text.lower().endswith(".gpkg")
        is_shp = path_text.lower().endswith(".shp")

        if is_gpkg:
            self._load_gpkg_layers(path_text)
            return

        self.layer_combo.clear()
        self.layer_combo.setVisible(False)
        self.selected_layer = ""
        if is_shp and not self.output:
            self._validate_shp_input_geometry(path_text)
        else:
            self._clear_input_geometry_warning()

    def _load_gpkg_layers(self, gpkg_path):
        if not self.is_vector:
            self.layer_combo.setVisible(False)
            return

        path = Path(gpkg_path)
        self.layer_combo.blockSignals(True)
        self.layer_combo.clear()
        self.layer_combo.setEditable(bool(self.output))

        if not path.exists():
            if self.output:
                self.layer_combo.addItem(self.selected_layer or "Result_layer")
                self.layer_combo.setVisible(True)
                if self.selected_layer:
                    self.layer_combo.setCurrentText(self.selected_layer)
                self._clear_input_geometry_warning()
            else:
                self.layer_combo.setVisible(False)
                self.selected_layer = ""
                self._clear_input_geometry_warning()
            self.layer_combo.blockSignals(False)
            return

        if not HAS_PYOGRIO:
            if not self.output:
                self._clear_input_geometry_warning()
            self.layer_combo.setVisible(False)
            self.layer_combo.blockSignals(False)
            return

        pyogrio_mod = pyogrio
        if pyogrio_mod is None:
            self.layer_combo.setVisible(False)
            self.layer_combo.blockSignals(False)
            return

        try:
            layers_info = pyogrio_mod.list_layers(str(path))
            parsed_layers = []
            for layer_item in layers_info:
                if hasattr(layer_item, "__len__") and len(layer_item) >= 2:
                    layer_name = str(layer_item[0])
                    geometry_type = str(layer_item[1])
                    parsed_layers.append((layer_name, geometry_type))

            if not self.output and self.allowed_geometry_families:
                parsed_layers = [
                    (layer_name, geom)
                    for layer_name, geom in parsed_layers
                    if is_geometry_compatible(geom, self.allowed_geometry_families)
                ]

            if not parsed_layers and not self.output and self.allowed_geometry_families:
                expected = format_expected_families(self.allowed_geometry_families)
                self._set_input_geometry_warning(
                    f"No compatible layers found in GeoPackage (expected {expected})"
                )
                self._set_no_compatible_layer_placeholder()
                self.selected_layer = ""
                self.layer_combo.blockSignals(False)
                return

            for layer_name, geom_type in parsed_layers:
                self.layer_combo.addItem(
                    f"{layer_name} ({geom_type})", userData=layer_name
                )

            if self.output:
                if self.layer_combo.count() == 0:
                    self.layer_combo.addItem(self.selected_layer or "Result_layer")
                if self.selected_layer:
                    self.layer_combo.setCurrentText(self.selected_layer)
            else:
                if self.selected_layer:
                    for idx in range(self.layer_combo.count()):
                        if (
                            str(
                                self.layer_combo.itemData(idx, Qt.ItemDataRole.UserRole)
                            )
                            == self.selected_layer
                        ):
                            self.layer_combo.setCurrentIndex(idx)
                            break
                if not self.selected_layer and self.layer_combo.count() > 0:
                    self.selected_layer = str(
                        self.layer_combo.itemData(0, Qt.ItemDataRole.UserRole)
                    )
                    self.layer_combo.setCurrentIndex(0)

            self.layer_combo.setVisible(True)
            self._clear_input_geometry_warning()

        except Exception as e:
            print(f"[BERATools] Error loading GeoPackage layers: {e}")
            self.layer_combo.setVisible(False)
            self.selected_layer = ""
            if not self.output:
                self._set_input_geometry_warning(
                    f"Could not read GeoPackage layers: {e}"
                )
        finally:
            self.layer_combo.blockSignals(False)

    def _get_encoded_value(self):
        path_text = self.file_input.text().strip()
        if not path_text:
            return ""

        if not self.is_vector:
            return path_text

        if self.get_validation_error() and not self.output:
            return ""

        if path_text.lower().endswith(".gpkg"):
            layer_name = self._current_layer_name() or self.selected_layer
            if layer_name:
                return f"{path_text}|{layer_name}"

        return path_text

    def get_value(self):
        return {self.variable: self._get_encoded_value()}

    def get_dependency_value(self):
        return self._get_encoded_value()

    def set_value(self, value):
        path_text, layer_name = self._split_path_and_layer(value)
        self.value = path_text
        self.selected_layer = layer_name
        self.file_input.setText(path_text)
        self._refresh_vector_state()
        self.emit_value_changed()


class DirectoryParameterWidget(ParameterWidget):
    """Widget for directory selection."""

    def __init__(self, param_def, parent=None):
        super().__init__(param_def, parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self.label_text)
        label.setMinimumWidth(self.LABEL_MIN_WIDTH)
        layout.addWidget(label)

        self.dir_input = QLineEdit()
        self.dir_input.setReadOnly(False)
        self.dir_input.setToolTip(self.description)
        self.dir_input.textChanged.connect(self._on_path_changed)
        layout.addWidget(self.dir_input)

        self.browse_btn = QPushButton("...")
        self.browse_btn.setMaximumWidth(40)
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        layout.addWidget(self.browse_btn)

        self.setLayout(layout)
        self.set_value(self.default_value)

    def _on_path_changed(self):
        self.value = self.dir_input.text()
        self.emit_value_changed()

    def _on_browse_clicked(self):
        """Open directory dialog."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select directory", str(self.default_value)
        )

        if dir_path:
            self.set_value(dir_path)

    def get_value(self):
        return {self.variable: self.value}

    def set_value(self, value):
        self.value = str(value) if value else ""
        self.dir_input.setText(self.value)
