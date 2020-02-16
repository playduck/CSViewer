# DataFile.py
# by Robin Prillwitz
# 11.2.2020
#

import os
import platform
from PyQt5 import QtGui, QtCore, QtWidgets

import pandas as pd
import numpy as np
from scipy import integrate
from scipy.interpolate import make_interp_spline
from scipy.ndimage.filters import gaussian_filter1d


# modified class from user Spencer at
# https://stackoverflow.com/questions/20922836/increases-decreases-qspinbox-value-when-click-drag-mouse-python-pyside
class SuperSpinner(QtWidgets.QDoubleSpinBox):
    def __init__(self, parent=None):
        super(SuperSpinner, self).__init__(parent)
        self.mouseStartPosY = 0
        self.startValue = 0

    def mousePressEvent(self, e):
        super(SuperSpinner, self).mousePressEvent(e)
        self.mouseStartPosY = e.pos().y()
        self.startValue = self.value()

    def mouseMoveEvent(self, e):
        self.setCursor(QtCore.Qt.SizeVerCursor)
        multiplier = 0.5
        valueOffset = int((self.mouseStartPosY - e.pos().y()) * multiplier)
        self.setValue(self.startValue + valueOffset)

    def mouseReleaseEvent(self, e):
        super(SuperSpinner, self).mouseReleaseEvent(e)
        self.unsetCursor()


# Handles one data file and its processing
class DataFile:
    def __init__(self, filename, handler, color):
        self.filename = filename
        self.handler = handler

        self.frame = QtWidgets.QWidget()
        self.item = QtWidgets.QListWidgetItem()
        self.settings = QtWidgets.QDialog()
        self.plot = None
        self.cursor = None
        self.highlight = False

        self.enabled = True
        self.data = self.readData()
        self.modData = None

        self.color = color
        self.width = 3
        self.xOffset = 0
        self.yOffset = 0
        self.interpolation = "Linear"
        self.interpolationAmount = 2000
        self.integrate = 0
        self.filter = 0

        self.initSettings()
        self.calculateData()

    def readData(self):
        return pd.read_csv(self.filename, sep=",", header=0, skipinitialspace=True)

    # applies all calculations and interpolation
    def calculateData(self):
        x = self.data["Zeit"].copy()  # TODO: automate if possible or wait for spec
        y = self.data["Messung"].copy()

        # Add Offsets
        x = x + self.xOffset
        y = y + self.yOffset

        # apply gaussian filter
        if self.filter > 0:
            y = gaussian_filter1d(y, sigma=self.filter)

        # calculate numeric integration / differential
        if self.integrate > 0:
            for i in range(self.integrate):
                for j, val in enumerate(x):
                    y[j] = integrate.quad(lambda x: y[j], 0, val)[0]
        elif self.integrate < 0:
            for i in range(abs(self.integrate)):
                y = np.gradient(y, x[1] - x[0])

        # interpolate data
        if self.interpolation == "Bezier" or self.interpolation == "Linear":

            xnew = np.linspace(x.min(), x.max(), self.interpolationAmount)
            if self.interpolation == "Bezier":
                spl = make_interp_spline(x, y, k=3)
            else:
                spl = make_interp_spline(x, y, k=1)
            y = spl(xnew)
            x = xnew

        # save data
        self.modData = pd.DataFrame({'x': x, 'y': y})

    # displays the list item in the file list
    def showListItem(self):
        boldFont = QtGui.QFont()
        boldFont.setBold(True)

        self.layout = QtWidgets.QHBoxLayout()

        self.enable = QtWidgets.QCheckBox()
        self.enable.setChecked(self.enabled)
        self.enable.stateChanged.connect(self.enableHandle)
        self.enable.setObjectName("enable_checkbox")
        self.enable.setStyleSheet("background-color: hsv({:d},{:d}%,{:d}%); color: black;".format(self.color[0], self.color[1], self.color[2]))

        self.layout.addWidget(self.enable)

        self.label = QtWidgets.QLabel(os.path.basename(self.filename))
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setFont(boldFont)
        self.layout.addWidget(self.label)
        self.layout.addStretch(1)

        self.offset = SuperSpinner(None)
        self.offset.setRange(-9999, 9999)
        self.offset.setFixedWidth(75)
        self.offset.valueChanged.connect(lambda x,who="xOffset": self.applyChange(x, who))
        self.offset_label = QtWidgets.QLabel("Offset:")
        self.offset_label.setBuddy(self.offset)
        self.layout.addWidget(self.offset_label)
        self.layout.addWidget(self.offset)

        self.settingsBtn = QtWidgets.QPushButton(QtGui.QIcon("./assets/settings.png"), "")
        self.settingsBtn.clicked.connect(self.showSettings)
        self.settingsBtn.setFlat(True)
        self.layout.addWidget(self.settingsBtn)

        self.layout.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)

        self.frame.setLayout(self.layout)
        self.item.setSizeHint(self.itemSizeHint(self.frame))

        return self.item, self.frame

    def itemSizeHint(self, w):
        a = w.sizeHint()
        a.setHeight(a.height() - 8)
        return a

    def enableHandle(self, value):
        self.enabled = value
        self.handler.updatePlot()

    def showSettings(self):
        framePos = self.frame.geometry()
        if platform.system() != "Windows":
            windowPos = self.handler.window.pos()
        else:
            windowPos = self.handler.pos()

        x = windowPos.x() + 150
        y = windowPos.y() + 1 * framePos.y() + 108  # offsets only work for fusion style

        self.settings.move(x, y)
        self.settings.exec_()

    def initSettings(self):
        self.settings.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
        )

        self.layout = QtWidgets.QGridLayout()

        # Color Picker
        self.colorPickerBtn = QtWidgets.QPushButton("  ")
        self.colorPickerBtn.setObjectName("color_select_button")
        self.colorPickerBtn.setStyleSheet("background-color: hsv({:d},{:d}%,{:d}%); color: black;".format(
            self.color[0], self.color[1], self.color[2]))

        self.colorPickerBtn.clicked.connect(lambda x,who="color": self.applyChange(x, who))
        self.colorPickerLabel = QtWidgets.QLabel("Farbe:")
        self.colorPickerLabel.setBuddy(self.colorPickerBtn)

        # Width Spinner
        self.widthSpinner = SuperSpinner()
        self.widthSpinner.setRange(1, 20)
        #width.setFixedWidth(100)
        self.widthSpinner.setValue(self.width)
        self.widthSpinner.valueChanged.connect(lambda x,who="width": self.applyChange(x, who))
        self.widthLabel = QtWidgets.QLabel("Breite:")
        self.widthLabel.setBuddy(self.widthSpinner)

        # Interpolation
        self.interpolationBox = QtWidgets.QComboBox()
        self.interpolationBox.addItems(["Keine", "Linear", "Bezier"])
        self.interpolationBox.setCurrentText(self.interpolation)
        self.interpolationBox.currentTextChanged.connect(lambda x,who="interpolation": self.applyChange(x, who))
        self.interpolationLabel = QtWidgets.QLabel("Interpolation:")
        self.interpolationLabel.setBuddy(self.interpolationBox)

        # Interpolation Amount
        self.interpolationAmountBox = QtWidgets.QSpinBox()
        self.interpolationAmountBox.setRange(len(self.data["Zeit"]), len(self.data["Zeit"]) * 1000)  # Automate maybe?
        self.interpolationAmountBox.setValue(self.interpolationAmount)
        self.interpolationAmountBox.valueChanged.connect(lambda x,who="interpolationAmount": self.applyChange(x, who))
        self.interpolationAmountLabel = QtWidgets.QLabel("Interpolationen:")
        self.interpolationAmountLabel.setBuddy(self.interpolationAmountBox)

        # Integration
        self.integrationBox = QtWidgets.QSpinBox()
        self.integrationBox.setRange(-10, 10)
        self.integrationBox.valueChanged.connect(lambda x,who="integration": self.applyChange(x, who))
        self.integrationLabel = QtWidgets.QLabel("Integration:")
        self.integrationLabel.setBuddy(self.integrationBox)

        # Filter
        self.filterBox = QtWidgets.QDoubleSpinBox()
        self.filterBox.valueChanged.connect(lambda x,who="filter": self.applyChange(x, who))
        self.filterLabel = QtWidgets.QLabel("Filter:")
        self.filterLabel.setBuddy(self.integrationBox)

        # Exit Buttons
        self.OKButton = QtWidgets.QPushButton("&Fertig")
        self.OKButton.clicked.connect(self.settings.close)
        self.OKButton.setDefault(True)

        self.layout.addWidget(self.colorPickerLabel,     0, 0)
        self.layout.addWidget(self.colorPickerBtn,       0, 1)
        self.layout.addWidget(self.widthLabel,           1, 0)
        self.layout.addWidget(self.widthSpinner,         1, 1)
        self.layout.addWidget(self.interpolationLabel,   2, 0)
        self.layout.addWidget(self.interpolationBox,     2, 1)
        self.layout.addWidget(self.interpolationAmountLabel, 3, 0)
        self.layout.addWidget(self.interpolationAmountBox,   3, 1)
        self.layout.addWidget(self.filterLabel,          4, 0)
        self.layout.addWidget(self.filterBox,            4, 1)
        self.layout.addWidget(self.integrationLabel,     5, 0)
        self.layout.addWidget(self.integrationBox,       5, 1)
        self.layout.addWidget(self.OKButton,             6, 1)

        self.settings.setLayout(self.layout)

    def applyChange(self, evt, who):
        if who == "color":
            color = QtGui.QColor()
            color.setHsvF(self.color[0] / 360, self.color[1] / 100, self.color[2] / 100)

            colorPicker = QtWidgets.QColorDialog()

            newColor = colorPicker.getColor(color).getHsvF()
            colorPicker.close()

            self.color[0] = int(newColor[0] * 360)
            self.color[1] = int(newColor[1] * 100)
            self.color[2] = int(newColor[2] * 100)

            self.settings.findChild(QtWidgets.QPushButton, "color_select_button").setStyleSheet(
                "background-color: hsv({:d},{:d}%,{:d}%); color: black;".format(
                    self.color[0], self.color[1], self.color[2]))
            self.frame.findChild(QtWidgets.QCheckBox, "enable_checkbox").setStyleSheet(
                "background-color: hsv({:d},{:d}%,{:d}%); color: black;".format(
                    self.color[0], self.color[1], self.color[2]))

        elif who == "width":
            self.width = evt
        elif who == "interpolation":
            self.interpolation = evt
        elif who == "interpolationAmount":
            self.interpolationAmount = evt
        elif who == "integration":
            self.integrate = evt
        elif who == "xOffset":
            self.xOffset = evt
        elif who == "yOffset":
            self.xOffset = evt
        elif who == "filter":
            self.filter = evt

        self.calculateData()
        self.handler.updatePlot()


