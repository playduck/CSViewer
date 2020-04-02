# DataFile.py
# by Robin Prillwitz
# 11.2.2020
#

import sys
from pathlib import Path

# Highest possible Z-Index
Z_IDX_TOP = 201

# Colors in HSV for Graphs
COLORS = [
    [151, 90, 90],
    [185, 95, 90],
    [52, 95, 90],
    [25, 95, 90],
    [325, 95, 90],
    [355, 75, 91],
]

# size of one division [x units]
DIVISION = 1
# Points Per Division
# amount of points to interpolate to for each division
PPD = 100
# rounding values after comma
PRECISION = 8

def getResource(path):
    root = Path()
    if getattr(sys, 'frozen', False):
        root = Path(sys._MEIPASS) # sys has attribute if it's frozen

    return str(root / path)
