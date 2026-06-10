# TuiView Raster & Vector Loader

## Tool Summary

A minimal Python script to display a raster (.tif) and optional vector file (e.g., .shp, .geojson) in a TuiView ViewerWidget using PySide6 and GDAL/OGR.

## Tool Usage

```sh
python simple_viewerwidget_load_tif.py <raster.tif> [vector_file]
```

- `<raster.tif>`: Path to the raster file to display (required)
- `[vector_file]`: Path to a vector file to overlay (optional)

If a vector file is provided, it will be displayed on top of the raster.

## Tool API

- **Raster Loading**:  
  Uses `gdal.Open()` to open the raster, creates a `ViewerStretch`, and adds it to the widget with `addRasterLayer()`.

- **Vector Loading**:  
  Uses `ogr.Open()` to open the vector file, gets the first layer, and adds it to the widget with `addVectorLayer()`.

### Example Code

```python
from tuiview import viewerwidget, viewerstretch
from osgeo import gdal, ogr

# ... PySide6 setup omitted for brevity ...

# Load raster
ds = gdal.Open(raster_path)
stretch = viewerstretch.ViewerStretch()
stretch.setGreyScale()
stretch.setBands((1,))
stretch.setStdDevStretch()
map_widget.addRasterLayer(ds, stretch)

# Load vector (optional)
if vector_path:
    vds = ogr.Open(vector_path)
    layer = vds.GetLayer(0)
    map_widget.addVectorLayer(vds, layer)
```

## Recommendations for Online Tool Doc Format

- Use clear sections: Summary, Usage, API, Example, and optionally FAQ or Troubleshooting.
- For larger projects, consider [MkDocs](https://www.mkdocs.org/) or [Sphinx with MyST](https://myst-parser.readthedocs.io/) for Markdown-based documentation.
- Include links to dependencies (PySide6, GDAL, tuiview).
- Add screenshots or animated GIFs for visual tools.
