#!/usr/bin/env python3
"""
Minimal example: load a .tif raster into TuiView ViewerWidget.
"""

import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from tuiview import viewerwidget, viewerstretch
from osgeo import gdal

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_viewerwidget_load_tif.py <raster.tif>")
        sys.exit(1)

    raster_path = sys.argv[1]

    app = QApplication(sys.argv)
    w = QWidget()
    layout = QVBoxLayout()
    map_widget = viewerwidget.ViewerWidget(w)
    layout.addWidget(map_widget)
    w.setLayout(layout)
    w.resize(800, 600)
    w.setWindowTitle('Simple TuiView ViewerWidget')
    w.show()

    # Load raster
    ds = gdal.Open(raster_path)
    if ds is None:
        print(f"Could not open {raster_path}")
        sys.exit(2)
    stretch = viewerstretch.ViewerStretch()
    stretch.setGreyScale()
    stretch.setBands((1,))
    stretch.setStdDevStretch()
    map_widget.addRasterLayer(ds, stretch)

    app.exec()

if __name__ == "__main__":
    main()
