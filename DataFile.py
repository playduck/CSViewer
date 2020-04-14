# DataFile.py
# by Robin Prillwitz
# 11.2.2020
#

import os
import sys
from pathlib import Path
from PyQt5 import QtGui, QtCore, QtWidgets, uic
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
        self.interpolationBox.addItems(["keine", "linear", "slinear", "quadratic", "cubic", "nearest", "zero", "previous", "next"])
        self.interpolationBox.setCurrentText(self.config["interpolation"])
        self.interpolationBox.currentTextChanged.connect(lambda x, who="interpolation": self.applyChange(x, who))
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

    def __reparseData(self, dialog):
        sep = dialog.findChild(QtWidgets.QLineEdit, "sepLineEdit").text()
        dec = dialog.findChild(QtWidgets.QLineEdit, "decimalLineEdit").text()
        if not sep or not dec:
            return

        self.config["seperator"] = sep
        self.config["decimal"] = dec

        dialog.close()
        del dialog

        self.__readData(sep=self.config["seperator"], decimal=self.config["decimal"])
        self.__selectData()

    def __selectData(self):
        dialog = uic.loadUi(Config.getResource("./ui/file_open_dialog.ui"))
        dialog.setWindowTitle(os.path.basename(self.filename))

        # dialog cannot be cancelled on first assignment
        if self.config["xColumn"] == -1 or self.config["yColumn"] == -1:
            buttonBox = dialog.findChild(QtWidgets.QDialogButtonBox, "buttonBox")
            for button in buttonBox.buttons():
                if buttonBox.buttonRole(button) == QtWidgets.QDialogButtonBox.RejectRole:
                    button.setCursor(QtGui.QCursor(QtCore.Qt.ForbiddenCursor))
                    button.setDisabled(True)

        itemList = self.data.columns.values.tolist()

        xComboBox = dialog.findChild(QtWidgets.QComboBox, "xComboBox")
        yComboBox = dialog.findChild(QtWidgets.QComboBox, "yComboBox")
        xComboBox.addItems(itemList)
        yComboBox.addItems(itemList)

        if self.config["xColumn"] != -1:
            xComboBox.setCurrentText(self.config["xColumn"])
        else:
            xComboBox.setCurrentIndex(0)

        if self.config["yColumn"] != -1:
            yComboBox.setCurrentText(self.config["yColumn"])
        else:
            yComboBox.setCurrentIndex(1 if len(itemList) > 0 else 0)

        dialog.findChild(QtWidgets.QLineEdit, "sepLineEdit").setText(str(self.config["seperator"]))
        dialog.findChild(QtWidgets.QLineEdit, "decimalLineEdit").setText(str(self.config["decimal"]))

        reparseBtn = dialog.findChild(QtWidgets.QPushButton, "reparseBtn")
        reparseBtn.clicked.connect(lambda: self.__reparseData(dialog))

        ret = dialog.exec_()
        dialog.close()

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
                self.modData =  self.interpData = pd.DataFrame([0, 0.001], [0, 0])

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

    def __readData(self, sep=Config.SEPERATOR, decimal=Config.DECIMAL):
        if not os.path.isfile(self.filename):
            self.data = pd.DataFrame([0, 0.001], [0, 0])
            return

        self.data = pd.read_csv(self.filename, sep=sep, decimal=decimal, header=0, skipinitialspace=True)

    # applies all calculations and interpolation
    def recalculate(self):
        dlg = pg.ProgressDialog("Berechnung", cancelText=None, busyCursor=False, disable=False, wait=250)
        dlg.setValue(0)

        if self.config["xColumn"] == -1 or self.config["yColumn"] == -1:
            return

        dlg += 10

        self.calculateCommon(dlg)

        x = self.modData["x"].values
        y = self.modData["y"].values

        dlg += 10

        # interpolate data
        if self.config["interpolation"] != "keine" and self.config["interpolation"] != "linear":

            # generate common x samples
            xnew = np.linspace(
                x.min(), # from
                x.max(), # to
                int(min([max([
                    np.ceil(((x.max() - x.min()) / Config.DIVISION) * Config.PPD),
                    Config.PPD,
                    len(x)
                ]), Config.MAX]))
            )

            dlg += 10
            spl = interp1d(x, y, kind=self.config["interpolation"], copy=False,
                    assume_sorted=True, bounds_error=False, fill_value=0)
            dlg += 10
            y = spl(xnew)
            x = xnew
            dlg += 10

        dlg += 10

        self.dataUpdated = True

        # save data
        self.interpData = {'x': x, 'y': y}

        dlg.setValue(100)

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

    def toDict(self):
        return {
            "type": "datafile",
            "containing": {
                "filename": self.filename,
                "data": self.data.to_dict(),
                "config": self.config
            }
        }
