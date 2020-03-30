# DataFile.py
# by Robin Prillwitz
# 11.2.2020
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


# Handles one data file and its processing
# inherits from QWidget to emit signals
class DataFile(ListItem.ListItem):

    def __init__(self, filename, color, config=None, parent=None):
        super().__init__(color, config=config, parent=parent)
        self.filename = filename

        self.__initSettings()
        self.__showListItem()

        self.__readData()

        if self.config["xColumn"] == -1 or self.config["yColumn"] == -1:
            self.__selectData()

        self.recalculate()
        self.updatePlot()

        self.__toggleSettings()

    def __copy__(self):
        return DataFile(self.filename, self.config["color"], config=self.config, parent=self.parent)

    # displays the list item in the file list
    def __showListItem(self):
        boldFont = QtGui.QFont()
        boldFont.setBold(True)

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

        self.label = QtWidgets.QLabel(os.path.basename(self.filename))
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setFont(boldFont)
        self.Hlayout.addWidget(self.label)
        self.Hlayout.addStretch(1)

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

        self.frame.setLayout(self.Vlayout)

    def __initSettings(self):
        self.settings = QtWidgets.QFrame()
        self.settings.setObjectName("settings")
        self.settings.setContentsMargins(0, 0, 20, 0)
        self.settings.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        self.GLayout = QtWidgets.QGridLayout()

        # Offsets
        self.x_offset = ListItem.SuperSpinner(None)
        self.x_offset.setRange(-9999, 9999)
        self.x_offset.setValue(self.config["xOffset"])
        # self.x_offset.setFixedWidth(75)
        self.x_offset.valueChanged.connect(lambda x, who="xOffset": self.applyChange(x, who))
        self.x_offset_label = QtWidgets.QLabel("x-Offset:")
        self.x_offset_label.setBuddy(self.x_offset)
        self.x_offset_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.y_offset = ListItem.SuperSpinner(None)
        self.y_offset.setRange(-9999, 9999)
        self.y_offset.setValue(self.config["yOffset"])
        # self.y_offset.setFixedWidth(75)
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

        # Interpolation
        self.interpolationBox = QtWidgets.QComboBox()
        self.interpolationBox.addItems(["Keine", "Linear", "Bezier"])
        self.interpolationBox.setCurrentText(self.config["interpolation"])
        self.interpolationBox.textHighlighted.connect(lambda x, who="interpolation": self.applyChange(x, who))
        self.interpolationLabel = QtWidgets.QLabel("Interpolation:")
        self.interpolationLabel.setBuddy(self.interpolationBox)
        self.interpolationLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

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

        self.reassignBtn = QtWidgets.QPushButton("Umbesetzen")
        self.reassignBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.reassignBtn.clicked.connect(lambda _: [
            self.__readData(),
            self.__selectData(),
            self.update()
        ])

        self.GLayout.addWidget(self.x_offset_label,              0, 0)
        self.GLayout.addWidget(self.x_offset,                    0, 1)
        self.GLayout.addWidget(self.y_offset_label,              1, 0)
        self.GLayout.addWidget(self.y_offset,                    1, 1)

        self.GLayout.addWidget(self.colorPickerLabel,            2, 0)
        self.GLayout.addWidget(self.colorPickerBtn,              2, 1)

        self.GLayout.addWidget(self.widthLabel,                  3, 0)
        self.GLayout.addWidget(self.widthSpinner,                3, 1)

        self.GLayout.addWidget(self.interpolationLabel,          4, 0)
        self.GLayout.addWidget(self.interpolationBox,            4, 1)

        self.GLayout.addWidget(self.filterLabel,                 5, 0)
        self.GLayout.addWidget(self.filterBox,                   5, 1)

        self.GLayout.addWidget(self.integrationLabel,            6, 0)
        self.GLayout.addWidget(self.integrationBox,              6, 1)

        self.GLayout.addWidget(self.reassignBtn,                 7, 1)

        self.settings.setLayout(self.GLayout)

    def __selectData(self):
        selectDialog = QtWidgets.QDialog()
        selectDialog.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint
        )
        selectDialog.setWindowTitle(os.path.basename(self.filename))
        with open(Config.getResource("assets/style.qss"), "r") as fh:
            selectDialog.setStyleSheet(fh.read())

        layout = QtWidgets.QGridLayout()

        itemList = self.data.columns.values.tolist()

        xComboBox = QtWidgets.QComboBox()
        xComboBox.addItems(itemList)

        yComboBox = QtWidgets.QComboBox()
        yComboBox.addItems(itemList)

        if self.config["xColumn"] != -1:
            xComboBox.setCurrentText(self.config["xColumn"])
        else:
            xComboBox.setCurrentIndex(0)

        if self.config["yColumn"] != -1:
            yComboBox.setCurrentText(self.config["yColumn"])
        else:
            yComboBox.setCurrentIndex(1 if len(itemList) > 0 else 0)


        xLabel = QtWidgets.QLabel("x Achse:")
        xLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        xLabel.setBuddy(xComboBox)
        yLabel = QtWidgets.QLabel("y Achse:")
        yLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        yLabel.setBuddy(yComboBox)

        OKButton = QtWidgets.QPushButton("Ok")
        OKButton.clicked.connect(selectDialog.accept)
        OKButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        CancelButton = QtWidgets.QPushButton("Abbrechen")
        CancelButton.clicked.connect(selectDialog.reject)
        CancelButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        CancelButton.setFlat(True)

        layout.addWidget(xLabel,    1,0)
        layout.addWidget(xComboBox, 1,1)
        layout.addWidget(yLabel,    2,0)
        layout.addWidget(yComboBox, 2,1)

        layout.addWidget(OKButton,      4,0)
        layout.addWidget(CancelButton,  4,1)

        selectDialog.setLayout(layout)
        selectDialog.setMinimumSize(200, 100)
        selectDialog.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        ret = selectDialog.exec_()
        selectDialog.close()

        if ret:
            l = self.data[xComboBox.currentText()].copy()
            if np.all(l.to_numpy() == np.sort(l)):
                self.config["xColumn"] = xComboBox.currentText()
                self.config["yColumn"] = yComboBox.currentText()
            else:
                self.showError("Unsortierte x-Achse",
                    """<p>Die angegebene x-Achse ist nicht chronologisch sortiert!
                    Die korrekte Darstellung kann nicht garantiert werden.</p>""")
        else:
            if self.config["xColumn"] == -1 or self.config["yColumn"] == -1:
                self.modData = pd.DataFrame({'x': [0], 'y': [0]})
                self.interpData = pd.DataFrame({'x': [0], 'y': [0]})

    def __toggleSettings(self):
        if self.settings.isHidden():
            self.settings.show()
            self.settingsBtn.setIcon(QtGui.QIcon(Config.getResource("assets/down.png")))
            self.item.setSizeHint(self.Vlayout.sizeHint())
        else:
            self.settings.hide()
            self.settingsBtn.setIcon(QtGui.QIcon(Config.getResource("assets/left.png")))
            sizeHint = self.Hlayout.sizeHint()
            sizeHint.setHeight(40+7)    # strut height + padding (don't ask)
            self.item.setSizeHint(sizeHint)

        self.sigUpdateUI.emit()

    def __readData(self):
        if not os.path.isfile(self.filename):
            self.data = pd.DataFrame([0], [0])
            return

        self.data = pd.read_csv(self.filename, sep=",", header=0, skipinitialspace=True)

    # applies all calculations and interpolation
    def recalculate(self):
        if self.config["xColumn"] == -1 or self.config["yColumn"] == -1:
            return

        self.calculateCommon()

        x = self.modData["x"]
        y = self.modData["y"]

        # interpolate data
        if self.config["interpolation"] != "Keine":

            # generate common x samples
            xnew = np.linspace(
                x.min(), # from
                x.max(), # to
                int(np.ceil(
                    ((x.max() - x.min()) / Config.DIVISION) * Config.PPD))
                )

            if self.config["interpolation"] == "Bezier":
                k = 3   # cubic
            else:
                k = 1   # linear

            spl = interp1d(x, y, kind=k, copy=False,
                    assume_sorted=True, bounds_error=False, fill_value=0)
            y = spl(xnew)
            x = xnew

        # save data
        self.interpData = pd.DataFrame({'x': x, 'y': y})

        if self.sigCalc:
            self.sigCalc.emit()

    # reflects updated values in the UI
    def updateUI(self):
        self.x_offset.setValue(self.config["xOffset"])
        self.y_offset.setValue(self.config["yOffset"])

    def getSelected(self):
        return None

    def deleteSelected(self, plot, selected):
        if self.item == selected:
            plot.plt.removeItem(self.plot)
            plot.plt.removeItem(self.cursor)
            del self
            return False # may be unreachable
        else:
            return True # = item stays alive

    def setZIndex(self, zIndex):
        self.config["zIndex"] = zIndex
        self.updatePlot()
        return zIndex - 1
