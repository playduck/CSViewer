# Plot.py
# by Robin Prillwitz
# 11.2.2020
#

import sys
from pathlib import Path

import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import pyqtgraph.graphicsItems.GridItem

import Config

# handles all graphing
class PlotViewer:
    def __init__(self, parent):
        self.parent = parent

        pg.setConfigOptions(antialias=False, background=None, useWeave=True, leftButtonPan=False)

        self.win = pg.GraphicsWindow()
        self.win.setObjectName("plotWindow")
        self.plt = self.win.addPlot(enableMenu=False)

        self.plt.hideButtons()
        self.plt.autoRange(padding=0.2)
        # self.plt.showAxis("top")
        # self.plt.showAxis("right")
        # self.plt.setDownsampling(auto=True, mode="mean") # "peak" "mean" "subsample" # can cause crashes
        self.plt.showGrid(True, True, 0.6)
        self.plt.vb.setLimits(minXRange=0.001, minYRange=0.001)
        # self.plt.vb.setAspectLocked(ratio=1)

        # vLine for vertical x-Axis cursor
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.vLine.setPen((255,255,255,200))
        self.vLine.setZValue(Config.Z_IDX_TOP + 1)
        self.plt.addItem(self.vLine, ignoreBounds=True)

        # Info Region below Plot
        self.info = QtWidgets.QLabel()
        self.info.setAlignment(QtCore.Qt.AlignCenter)
        self.info.setObjectName("infoWindow")

        # Add to Layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.win)
        self.layout.addWidget(self.info)

    def addPlot(self, item):
        self.plt.addItem(item.plot)
        self.plt.addItem(item.cursor, ignoreBounds=True)

        try:
            item.plot.setData(clipToView=True)
            item.plot.setData(autoDownsample=True, downsampleMethod="peak")
            item.updatePlot()
        except:
            pass

    def setInfoText(self, info):
        self.info.setText(info)
