# Process.py
# by Robin Prillwitz
# 11.2.2020
#

import os
import sys
import copy
from pathlib import Path
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

import pandas as pd
import numpy as np
from scipy import integrate
from scipy.interpolate import interp1d
from scipy.ndimage.filters import gaussian_filter1d

import Config
import Cursor
import ListItem
import ListWidget

# Handles one data file and its processing
# inherits from QWidget to emit signals
class Process(ListItem.ListItem):

    def __init__(self, color, config=None, parent=None):
        super().__init__(color, config=config, parent=parent)

        self.config["operation"] = "Addition"

        self.__initSettings()
        self.__showListItem()

        self.data = None
        self.recalculate()
        self.updatePlot()

        self.__toggleSettings()
        self.updateUI()

    def __copy__(self):
        newPc = Process(self.config["color"], self.config, self.parent)
        for item in self.fileList.list:
            newPc.fileList.addItem(copy.copy(item))
        return newPc

    # displays the list item in the file list
    def __showListItem(self):
        Font = QtGui.QFont()
        Font.setItalic(True)

        self.box = QtWidgets.QFrame()
        self.Hlayout = QtWidgets.QHBoxLayout()
        self.Vlayout = QtWidgets.QVBoxLayout()

        self.enable = QtWidgets.QCheckBox()
        self.enable.setChecked(self.config["enabled"])
        self.enable.stateChanged.connect(self.setEnabled)
        self.enable.setObjectName("enable_checkbox")
        self.enable.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.enable.setStyleSheet(
            "background-color: hsv({:d},{:d}%,{:d}%); color: black;".format(
                self.config["color"][0], self.config["color"][1], self.config["color"][2]))

        self.Hlayout.addWidget(self.enable)

        self.label = QtWidgets.QLabel("Prozess")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setFont(Font)
        self.Hlayout.addWidget(self.label)
        self.Hlayout.addStretch(1)

        self.operationBox = QtWidgets.QComboBox()
        self.operationBox.addItems(["Addition", "Subtraktion", "Multiplikation", "Division"])
        self.operationBox.setCurrentText(self.config["operation"])
        self.operationBox.textHighlighted.connect(lambda x, who="operation": self.applyChange(x, who))
        self.Hlayout.addWidget(self.operationBox)

        self.settingsBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/left.png")), "")
        self.settingsBtn.clicked.connect(self.__toggleSettings)
        self.settingsBtn.setFlat(True)
        self.settingsBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.settingsBtn.setIconSize(QtCore.QSize(16, 16))
        self.settingsBtn.setFixedSize(30, 30)
        self.Hlayout.addWidget(self.settingsBtn)

        self.Hlayout.addStrut(40)
        self.Hlayout.setAlignment(QtCore.Qt.AlignCenter)
        self.Hlayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.Hlayout.setContentsMargins(10,0,10,0)
        self.Vlayout.setContentsMargins(0,0,0,0)

        self.box.setLayout(self.Hlayout)
        self.Vlayout.addWidget(self.box)
        self.Vlayout.addWidget(self.settings)

        self.fileList = ListWidget.DeselectableListWidget(self)
        self.fileList.setObjectName("process-list")
        self.fileList.setMinimumHeight(self.Hlayout.sizeHint().height() * 1.5)
        self.fileList.setMaximumHeight(self.Hlayout.sizeHint().height() * 2)
        self.fileList.setMinimumWidth(200)

        self.fileList.sigUpdateUI.connect(self.updateUI)
        self.fileList.sigCalc.connect(self.update)
        self.Vlayout.addWidget(self.fileList)

        self.frame.setLayout(self.Vlayout)

    # applies all calculations and interpolation
    def recalculate(self):

        if len(self.fileList.list) == 0:
            self.ignore = True
            self.config["cursorEnabled"] = False
            self.modData = pd.DataFrame({'x': [0], 'y': [0]})
            self.interpData = pd.DataFrame({'x': [0], 'y': [0]})
            return
        self.ignore = False
        self.config["cursorEnabled"] = True

        # find entire range of all items
        start = np.Inf
        end =  -np.Inf

        for index, item in enumerate(self.fileList.list):
            if item.ignore:
                break

            imin = item.interpData["x"].min()
            imax = item.interpData["x"].max()

            if imin < start:
                start = imin
            if imax > end:
                end = imax

        if start == np.Inf or end == -np.Inf:
            return

        # generate x points in range
        x = np.linspace(
            start,
            end,
            int(np.ceil(
                (abs(end - start) / Config.DIVISION) * Config.PPD))
            )
        y = np.full(len(x), np.nan)

        for item in self.fileList.list:
            if item.ignore:
                break

            if isinstance(item, Cursor.Cursor):
                 values = np.full(len(x), item.config["yOffset"])
            else:
                if item.config["interpolation"] == "keine":
                    interpolation = "linear"
                else:
                    interpolation = item.config["interpolation"]

                # create spline, ignoreing all out-of-range values
                spl = interp1d(item.modData["x"], item.modData["y"],
                        kind=interpolation, copy=False, assume_sorted=True,
                        bounds_error = False, fill_value=0)
                values = spl(x)

            # apply Operation otherwise just add
            for i in range(len(x)):
                if np.isnan(y[i]):
                    y[i] = values[i]
                else:
                    y[i] = self.__doOperation(y[i], values[i])

        # remove all remaining NANs
        y[np.isnan(y)] = 0

        # apply gaussian filter
        if self.config["filter"] > 0:
            y = gaussian_filter1d(y, sigma=self.config["filter"])

        # calculate numeric integration / differential
        if self.config["integrate"] > 0:
            for i in range(self.config["integrate"]):
                for j, val in enumerate(x):
                    y[j] = integrate.quad(lambda _: y[j], 0, val)[0]
        elif self.config["integrate"] < 0:
            for i in range(abs(self.config["integrate"])):
                y = np.gradient(y, x[1] - x[0])

        # Add Offsets
        x = x + self.config["xOffset"]
        y = y + self.config["yOffset"]

        # save data
        self.interpData = pd.DataFrame({'x': x, 'y': y})
        if self.sigCalc:
            self.sigCalc.emit()

    # from user Aguy at
    # https://stackoverflow.com/questions/48900977/find-all-indexes-of-a-numpy-array-closest-to-a-value
    def __findValueIndex(self, seq, val):
        r = np.where(np.diff(np.sign(seq - val)) != 0)
        idx = r + (val - seq[r]) / (seq[r + np.ones_like(r)] - seq[r])
        idx = np.append(idx, np.where(seq == val))
        idx = np.sort(idx)
        return idx

    def __doOperation(self, a, b):
        if self.config["operation"] == "Addition":
            return a + b
        elif self.config["operation"] == "Subtraktion":
            return a - b
        elif self.config["operation"] == "Multiplikation":
            return a * b
        elif self.config["operation"] == "Division":
            return a / b
        else:
            return -1

    # reflects updated values in the UI
    def updateUI(self):
        self.x_offset.setValue(self.config["xOffset"])
        self.y_offset.setValue(self.config["yOffset"])

        height = 50
        for item in self.fileList.list:
            height += item.item.sizeHint().height()

        self.fileList.setFixedHeight( height )

        self.__setSizeHint()

    def deselect(self):
        super().deselect()
        self.fileList.deselectAll()

    def getSelected(self):
        return self.fileList.getSelected()

    def getCount(self, i):
        i = self.fileList.getCount(i)
        return i + 1

    def deleteSelected(self, plot, selected):
        # deletes itself and all its children
        if self.item == selected:
            plot.plt.removeItem(self.plot)
            plot.plt.removeItem(self.cursor)

            self.fileList.deleteChildren(plot)

            del self
            return False # may be unreachable
        else:
            self.fileList.deleteSelected(plot)
            return True # = item stays alive

    def updateCursor(self, mousePoint):
        infoText = super().updateCursor(mousePoint)
        for index, item in enumerate(self.fileList.list):
            infoText += item.updateCursor(mousePoint)

        return infoText

    def autoscale(self):
        considerations = super().autoscale()
        for item in self.fileList.list:
            considerations = considerations + item.autoscale()
        return considerations

    def setZIndex(self, zIndex):
        self.config["zIndex"] = zIndex

        zIndex = self.fileList.setZIndex(zIndex - 1)

        self.updatePlot()
        return zIndex

    def __toggleSettings(self):
        if self.settings.isHidden():
            self.settings.show()
            self.settingsBtn.setIcon(QtGui.QIcon(Config.getResource("assets/down.png")))
            self.__setSizeHint()
        else:
            self.settings.hide()
            self.settingsBtn.setIcon(QtGui.QIcon(Config.getResource("assets/left.png")))
            sizeHint = self.Vlayout.sizeHint()
            # sizeHint.setHeight(40+7)    # strut height + padding (don't ask)
            self.__setSizeHint()

        self.sigUpdateUI.emit()

    def __setSizeHint(self):
        sizeHint = self.Vlayout.sizeHint()
        sizeHint.setHeight(sizeHint.height() + 7)
        self.item.setSizeHint(sizeHint)

    def __initSettings(self):
        self.settings = QtWidgets.QFrame()
        self.settings.setObjectName("settings")
        self.settings.setContentsMargins(20, 0, 20, 0)
        self.settings.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)

        self.GLayout = QtWidgets.QGridLayout()

        # Offsets
        self.x_offset = ListItem.SuperSpinner(None)
        self.x_offset.setRange(-9999, 9999)
        self.x_offset.setValue(self.config["xOffset"])
        self.x_offset.setFixedWidth(75)
        self.x_offset.valueChanged.connect(lambda x, who="xOffset": self.applyChange(x, who))
        self.x_offset_label = QtWidgets.QLabel("x-Offset:")
        self.x_offset_label.setBuddy(self.x_offset)
        self.x_offset_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.y_offset = ListItem.SuperSpinner(None)
        self.y_offset.setRange(-9999, 9999)
        self.y_offset.setValue(self.config["yOffset"])
        self.y_offset.setFixedWidth(75)
        self.y_offset.valueChanged.connect(lambda y, who="yOffset": self.applyChange(y, who))
        self.y_offset_label = QtWidgets.QLabel("y-Offset:")
        self.y_offset_label.setBuddy(self.y_offset)
        self.y_offset_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        # Color Picker
        self.colorPickerBtn = QtWidgets.QPushButton("  ")
        self.colorPickerBtn.setObjectName("color_select_button")
        self.colorPickerBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.colorPickerBtn.setStyleSheet("background-color: hsv({:d},{:d}%,{:d}%); color: black;".format(
            self.config["color"][0], self.config["color"][1], self.config["color"][2]))
        self.colorPickerBtn.clicked.connect(lambda x, who="color": self.applyChange(x, who))
        self.colorPickerLabel = QtWidgets.QLabel("Farbe:")
        self.colorPickerLabel.setBuddy(self.colorPickerBtn)
        self.colorPickerLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        # Width Spinner
        self.widthSpinner = QtWidgets.QSpinBox()
        self.widthSpinner.setRange(1, 20)
        self.widthSpinner.setValue(self.config["width"])
        self.widthSpinner.valueChanged.connect(lambda x, who="width": self.applyChange(x, who))
        self.widthLabel = QtWidgets.QLabel("Breite:")
        self.widthLabel.setBuddy(self.widthSpinner)
        self.widthLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        # Integration
        self.integrationBox = QtWidgets.QSpinBox()
        self.integrationBox.setRange(-10, 10)
        self.integrationBox.setValue(self.config["integrate"])
        self.integrationBox.valueChanged.connect(lambda x, who="integrate": self.applyChange(x, who))
        self.integrationLabel = QtWidgets.QLabel("Integration:")
        self.integrationLabel.setBuddy(self.integrationBox)
        self.integrationLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        # Filter
        self.filterBox = QtWidgets.QDoubleSpinBox()
        self.filterBox.setValue(self.config["filter"])
        self.filterBox.valueChanged.connect(lambda x, who="filter": self.applyChange(x, who))
        self.filterLabel = QtWidgets.QLabel("Filter:")
        self.filterLabel.setBuddy(self.integrationBox)
        self.filterLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.GLayout.addWidget(self.x_offset_label,              0, 0)
        self.GLayout.addWidget(self.x_offset,                    0, 1)
        self.GLayout.addWidget(self.y_offset_label,              1, 0)
        self.GLayout.addWidget(self.y_offset,                    1, 1)

        self.GLayout.addWidget(self.colorPickerLabel,            2, 0)
        self.GLayout.addWidget(self.colorPickerBtn,              2, 1)

        self.GLayout.addWidget(self.widthLabel,                  3, 0)
        self.GLayout.addWidget(self.widthSpinner,                3, 1)

        self.GLayout.addWidget(self.filterLabel,                 4, 0)
        self.GLayout.addWidget(self.filterBox,                   4, 1)

        self.GLayout.addWidget(self.integrationLabel,            5, 0)
        self.GLayout.addWidget(self.integrationBox,              5, 1)

        self.settings.setLayout(self.GLayout)
