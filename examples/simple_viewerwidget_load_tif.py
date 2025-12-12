#!/usr/bin/env python3
"""
Minimal example: load a .tif raster and a vector file into TuiView ViewerWidget.

How to load raster and vector data:
-----------------------------------
- Raster (.tif): Uses GDAL to open the file, creates a ViewerStretch, and adds it to the ViewerWidget.
- Vector (e.g., .shp, .geojson): Uses OGR to open the file, gets the first layer, and adds it to the ViewerWidget.

Usage:
    python simple_viewerwidget_load_tif.py <raster.tif> [vector_file]

If a vector file is provided, it will be displayed on top of the raster.
"""

import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from tuiview import viewerwidget, viewerstretch
from osgeo import gdal, ogr

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_viewerwidget_load_tif.py <raster.tif> [vector_file]")
        sys.exit(1)

    raster_path = sys.argv[1]
    vector_path = sys.argv[2] if len(sys.argv) > 2 else None

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

    # Load vector (optional)
    if vector_path:
        vds = ogr.Open(vector_path)
        if vds is None:
            print(f"Could not open vector file {vector_path}")
            sys.exit(3)
        layer = vds.GetLayer(0)
        map_widget.addVectorLayer(vds, layer)

    app.exec()

if __name__ == "__main__":
    main()
