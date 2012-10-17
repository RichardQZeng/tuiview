
"""
Module that deals with color ramps

This product includes color specifications and designs developed by 
Cynthia Brewer (http://colorbrewer.org/).
"""
# This file is part of 'Viewer' - a simple Raster viewer
# Copyright (C) 2012  Sam Gillingham
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import numpy
import json
# Import minify function, available from
# https://github.com/getify/JSON.minify
from minify_json import json_minify 

# init our dictionary of data
# longest list of colors for each name
# from http://colorbrewer.org/
# generated by colorbrewer2py.py

RAMP = {}
RAMP['Blues'] = {'author' : 'Cynthia Brewer', 'comments' : 'Colours from www.colorbrewer.org by Cynthia A. Brewer, Geography, Pennsylvania State University.', 'type' : 'Sequential'}
RAMP['Blues']['description'] = {}
RAMP['Blues']['description']['red'] = '247 222 198 158 107 66 33 8 8'
RAMP['Blues']['description']['green'] = '251 235 219 202 174 146 113 81 48'
RAMP['Blues']['description']['blue'] = '255 247 239 225 214 198 181 156 107'
RAMP['Greys'] = {'author' : 'Cynthia Brewer', 'comments' : 'Colours from www.colorbrewer.org by Cynthia A. Brewer, Geography, Pennsylvania State University.', 'type' : 'Sequential'}
RAMP['Greys']['description'] = {}
RAMP['Greys']['description']['red'] = '255 240 217 189 150 115 82 37 0'
RAMP['Greys']['description']['green'] = '255 240 217 189 150 115 82 37 0'
RAMP['Greys']['description']['blue'] = '255 240 217 189 150 115 82 37 0'
RAMP['RdBu'] = {'author' : 'Cynthia Brewer', 'comments' : 'Colours from www.colorbrewer.org by Cynthia A. Brewer, Geography, Pennsylvania State University.', 'type' : 'Diverging'}
RAMP['RdBu']['description'] = {}
RAMP['RdBu']['description']['red'] = '103 178 214 244 253 247 209 146 67 33 5'
RAMP['RdBu']['description']['green'] = '0 24 96 165 219 247 229 197 147 102 48'
RAMP['RdBu']['description']['blue'] = '31 43 77 130 199 247 240 222 195 172 97'
RAMP['RdYlBu'] = {'author' : 'Cynthia Brewer', 'comments' : 'Colours from www.colorbrewer.org by Cynthia A. Brewer, Geography, Pennsylvania State University.', 'type' : 'Diverging'}
RAMP['RdYlBu']['description'] = {}
RAMP['RdYlBu']['description']['red'] = '165 215 244 253 254 255 224 171 116 69 49'
RAMP['RdYlBu']['description']['green'] = '0 48 109 174 224 255 243 217 173 117 54'
RAMP['RdYlBu']['description']['blue'] = '38 39 67 97 144 191 248 233 209 180 149'
RAMP['RdYlGn'] = {'author' : 'Cynthia Brewer', 'comments' : 'Colours from www.colorbrewer.org by Cynthia A. Brewer, Geography, Pennsylvania State University.', 'type' : 'Diverging'}
RAMP['RdYlGn']['description'] = {}
RAMP['RdYlGn']['description']['red'] = '165 215 244 253 254 255 217 166 102 26 0'
RAMP['RdYlGn']['description']['green'] = '0 48 109 174 224 255 239 217 189 152 104'
RAMP['RdYlGn']['description']['blue'] = '38 39 67 97 139 191 139 106 99 80 55'
RAMP['Reds'] = {'author' : 'Cynthia Brewer', 'comments' : 'Colours from www.colorbrewer.org by Cynthia A. Brewer, Geography, Pennsylvania State University.', 'type' : 'Sequential'}
RAMP['Reds']['description'] = {}
RAMP['Reds']['description']['red'] = '255 254 252 252 251 239 203 165 103'
RAMP['Reds']['description']['green'] = '245 224 187 146 106 59 24 15 0'
RAMP['Reds']['description']['blue'] = '240 210 161 114 74 44 29 21 13'
RAMP['Spectral'] = {'author' : 'Cynthia Brewer', 'comments' : 'Colours from www.colorbrewer.org by Cynthia A. Brewer, Geography, Pennsylvania State University.', 'type' : 'Diverging'}
RAMP['Spectral']['description'] = {}
RAMP['Spectral']['description']['red'] = '158 213 244 253 254 255 230 171 102 50 94'
RAMP['Spectral']['description']['green'] = '1 62 109 174 224 255 245 221 194 136 79'
RAMP['Spectral']['description']['blue'] = '66 79 67 97 139 191 152 164 165 189 162'
RAMP['YlGnBu'] = {'author' : 'Cynthia Brewer', 'comments' : 'Colours from www.colorbrewer.org by Cynthia A. Brewer, Geography, Pennsylvania State University.', 'type' : 'Sequential'}
RAMP['YlGnBu']['description'] = {}
RAMP['YlGnBu']['description']['red'] = '255 237 199 127 65 29 34 37 8'
RAMP['YlGnBu']['description']['green'] = '255 248 233 205 182 145 94 52 29'
RAMP['YlGnBu']['description']['blue'] = '217 177 180 187 196 192 168 148 88'
RAMP['YlOrRd'] = {'author' : 'Cynthia Brewer', 'comments' : 'Colours from www.colorbrewer.org by Cynthia A. Brewer, Geography, Pennsylvania State University.', 'type' : 'Sequential'}
RAMP['YlOrRd']['description'] = {}
RAMP['YlOrRd']['description']['red'] = '255 255 254 254 253 252 227 189 128'
RAMP['YlOrRd']['description']['green'] = '255 237 217 178 141 78 26 0 0'
RAMP['YlOrRd']['description']['blue'] = '204 160 118 76 60 42 28 38 38'

def getRampsFromFile(fname):
    # Read and minify file contents
    palsMinified = json_minify(open(fname, "r").read())
    # Loads palettes in a dict
    pals = json.loads(palsMinified)
    
    # For each palette that's been detected
    for pal in pals:
      # Check name is present and unique
      if "name" in pal:
          cur_name = pal["name"]
      else:
          # Quit - invalid colour scheme structure
      if cur_name in RAMP.keys():
          # Quit - invalid colour scheme name
      
      # Check red, green and blue fields are present
      if "description" in pal:
          if pal[cur_name]["description"].keys() != ['red', 'green', 'blue']:
              # Quit - invalid colour scheme
      else:
          # Quit - invalid colour scheme
      
      # Other fields optional
      if "author" in pal:
          cur_author = pal["author"]
      else:
          cur_author = ''
      if "comments" in pal:
          cur_comments = pal["comments"]
      else:
          cur_comments = ''
      if "type" in pal:
          cur_type = pal["type"]
      else:
          cur_type = ''
      
      # Assembling dictionary entry
      RAMP[cur_name] = {'author' : cur_author, 'comments' : cur_comments, 'type' : cur_type, 'description' = {}}
      # Add decsription fields
      RAMP[cur_name]["description"]["red"] = pal["description"]["red"]
      RAMP[cur_name]["description"]["green"] = pal["description"]["green"]
      RAMP[cur_name]["description"]["blue"] = pal["description"]["blue"]
  
def getRampsForDisplay():
    """
    Returns a list of (name, displayname) tuples for
    populating Combo boxes. Sorted by type
    """
    # sort by stype
    rampDict = {}
    for key in RAMP:
        rampType = RAMP[key]['type']
        if rampType in rampDict:
            rampDict[rampType].append(key)
        else:
            rampDict[rampType] = [key]

    display = []
    for rampType in rampDict:
        for name in rampDict[rampType]:
            title = "%s (%s)" % (name, rampType)
            display.append((name, title))
    return display

def getLUTForRamp(code, name, lutsize):
    """
    Returns an LUT for the specified color and name
    """
    # get the data as string
    colstr = RAMP[name][code]
    # turn it into a list of floats
    # numpy.interp() needs floats
    colList = [float(x) for x in colstr.split()]
    # the x-values of the observations
    # evenly spaced 0-255 with len(colList) obs
    xobs = numpy.linspace(0, 255, len(colList))
    # create an array from our list
    yobs = numpy.array(colList)
    # values to interpolate at 0-255
    # same size as the lut
    xinterp = numpy.linspace(0, 255, lutsize)
    # do the interp
    yinterp = numpy.interp(xinterp, xobs, yobs)
    # return as 8 bit int
    return yinterp.astype(numpy.uint8)
