# Cursor.py
# by Robin Prillwitz
# 31.3.2020
#

import os
import sys
from pathlib import Path
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

import pandas as pd
import numpy as np
from scipy import integrate
from scipy.interpolate import interp1d
from scipy.ndimage.filters import gaussian_filter1d

import Config
import ListItem

class Cursor(ListItem.ListItem):

    def __init__(self, color, config=None, parent=None):
        super().__init__(color, config=config, parent=parent)

        self.__showListItem()

        del self.plot
        self.plot = pg.InfiniteLine(angle=0, movable=True)

        self.recalculate()
        self.updatePlot()

    def __copy__(self):
        return Cursor(self.config["color"], config=self.config, parent=self.parent)

    # displays the list item in the file list
    def __showListItem(self):
        Font = QtGui.QFont()
        Font.setItalic(True)

        self.box = QtWidgets.QFrame()
        self.Hlayout = QtWidgets.QHBoxLayout()
        self.Vlayout = QtWidgets.QVBoxLayout()

        self.enable = QtWidgets.QCheckBox()
        self.enable.setChecked(self.config["cursorEnabled"])
        self.enable.stateChanged.connect(self.setEnabled)
        self.enable.setObjectName("enable_checkbox")
        self.enable.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.enable.setStyleSheet(
            "background-color: hsv({:d},{:d}%,{:d}%); color: black;".format(
                self.config["color"][0], self.config["color"][1], self.config["color"][2]))

        self.Hlayout.addWidget(self.enable)

        self.label = QtWidgets.QLabel("Cursor")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setFont(Font)
        self.Hlayout.addWidget(self.label)
        self.Hlayout.addStretch(1)

        self.y_offset = ListItem.SuperSpinner(None)
        self.y_offset.setRange(-9999, 9999)
        self.y_offset.setValue(self.config["yOffset"])
        self.y_offset.setFixedWidth(75)
        self.y_offset.setFixedHeight(30)
        self.y_offset.valueChanged.connect(lambda y, who="yOffset": self.applyChange(y, who))
        self.y_offset_label = QtWidgets.QLabel("y-Offset:")
        self.y_offset_label.setBuddy(self.y_offset)
        self.y_offset_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.Hlayout.addWidget(self.y_offset_label)
        self.Hlayout.addWidget(self.y_offset)

        self.Hlayout.addStrut(40)
        self.Hlayout.setAlignment(QtCore.Qt.AlignCenter)
        self.Hlayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.Hlayout.setContentsMargins(10,0,10,0)
        self.Vlayout.setContentsMargins(0,0,0,0)

        self.box.setLayout(self.Hlayout)
        self.Vlayout.addWidget(self.box)
        self.frame.setLayout(self.Vlayout)

        sizeHint = self.Vlayout.sizeHint()
        sizeHint.setHeight(sizeHint.height() + 7)
        self.item.setSizeHint(sizeHint)

    # applies all calculations and interpolation
    def recalculate(self):
        self.modData = pd.DataFrame({"x": [0,0.0001], "y": [self.config["yOffset"],self.config["yOffset"]]})
        self.interpData = pd.DataFrame({"x": [0,0.0001], "y": [self.config["yOffset"],self.config["yOffset"]]})
        if self.sigCalc:
            self.sigCalc.emit()

    def updatePlot(self):
        # Calculate all colors
        color = QtGui.QColor()
        color.setHsvF(  self.config["color"][0] / 360,
                        self.config["color"][1] / 100,
                        self.config["color"][2] / 100)
        pen = pg.mkPen(color=color, width=self.config["width"])

        highlightColor = QtGui.QColor()
        highlightColor.setHsvF( self.config["color"][0] / 360,
                                self.config["color"][1] / 100,
                                self.config["color"][2] / 100, 0.2)
        highlightPen = pg.mkPen(color=highlightColor, width=self.config["width"] * 4 + 10)

        self.cursor.setPen(pg.mkPen(color=(0, 0, 0, 0), width=0))

        if not self.config["enabled"]:
                self.plot.setPen(None)
        else:
            if self.config["highlight"]:
                self.plot.setPen(highlightPen)
                # self.plot.setData(pen=None, symbolPen=pen, symbolBrush=highlightColor, shadowPen=None)
            else:
                self.plot.setPen(pen)

            # set respective z indecies
            if self.config["highlight"]:
                # self.cursor.setZValue(Config.Z_IDX_TOP)
                self.plot.setZValue(Config.Z_IDX_TOP)
            else:
                # self.cursor.setZValue(self.config["zIndex"])
                self.plot.setZValue(self.config["zIndex"])

        self.plot.setValue(self.config["yOffset"])

    def updateUI(self):
        self.y_offset.setValue(self.config["yOffset"])

    def getSelected(self):
        return None

    def deleteSelected(self, plot, selected):
        if self.item == selected:
            plot.plt.removeItem(self.plot)
            # plot.plt.removeItem(self.cursor)
            del self
            return False # may be unreachable
        else:
            return True # = item stays alive

    def setZIndex(self, zIndex):
        self.config["zIndex"] = zIndex
        self.updatePlot()
        return zIndex - 1

    def toDict(self):
        return {
            "type": "cursor",
            "containing": {
                "config": self.config
            }
        }
