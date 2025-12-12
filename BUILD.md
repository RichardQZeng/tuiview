
# Set env variable before installing

pip install -e .

$env:GDAL_HOME = 'C:\miniconda3\envs\data\Library'
This will provide path to gdal.lib

tuiview chm.tif --vector centerline.gpkg