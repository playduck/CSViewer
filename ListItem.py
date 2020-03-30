# ListItem.py
# by Robin Prillwitz
# 16.3.2020
#

from PyQt5 import QtGui, QtCore, QtWidgets
from scipy import integrate
from scipy.interpolate import make_interp_spline
from scipy.ndimage.filters import gaussian_filter1d
import pyqtgraph as pg
import numpy as np
import pandas as pd
import Config
import Graph

class ListItem(QtCore.QObject):
    sigUpdateUI = QtCore.pyqtSignal()
    sigCalc = QtCore.pyqtSignal()

    sigDeleteMe = QtCore.pyqtSignal(["QObject"])

    def __init__(self, color, config=None, parent=None):
        super().__init__()

        self.parent = parent

        if config:
            self.config = config
        else:
            self.config = {
                "highlight": False,
                "enabled": True,
                "zIndex": 0,
                "xOffset": 0,
                "yOffset": 0,
                "xColumn": -1,
                "yColumn": -1,
                "color": color,
                "width": 3,
                "interpolation": "Linear",
                "interpolationAmount":  100,
                "integrate": 0,
                "filter": 0
            }

        self.cursor = None
        self.plot = None
        self.modData = None
        self.interpData = None
        self.ignore = False

        self.plot = Graph.Graph(symbol='o', symbolSize=5)
        self.plot.sigPositionDelta.connect(self.__applyDelta)
        self.cursor = pg.InfiniteLine(angle=0, movable=False)

        self.item = QtWidgets.QListWidgetItem()
        self.frame = QtWidgets.QWidget()

        self.frame.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.frame.customContextMenuRequested.connect(self.__contextMenuEvent)


    def __copy__(self):
        raise NotImplementedError

# ---------------------------------- private --------------------------------- #

    def __applyDelta(self, dx, dy):
        self.config["xOffset"] += dx
        self.config["yOffset"] += dy

        self.recalculate()
        self.updateUI()
        self.updatePlot()

    def __showListItem(self):
        raise NotImplementedError

    def __contextMenuEvent(self, event):
        menu = QtGui.QMenu(self.frame)
        menu.addAction(QtGui.QAction('Exportieren', self))
        menu.addSeparator()
        menu.addAction(QtGui.QAction('Löschen', self))

        action = menu.exec_(self.frame.mapToGlobal(event))

        if action:
            if action.text() == "Exportieren":
                self.__export()
            elif action.text() == "Löschen":
                self.sigDeleteMe.emit(self)

    def __export(self):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Exportieren", "",
                                                  "CSV Datei (*.csv);;Alle Dateinen (*)", options=options)
        if filename:
            self.interpData.to_csv(filename, encoding='utf-8', index=False)

# ----------------------------------- local ---------------------------------- #

    def showError(self, title, message):
        error_dialog = QtWidgets.QMessageBox()

        with open(Config.getResource("assets/style.qss"), "r") as fh:
            error_dialog.setStyleSheet(fh.read())

        error_dialog.setIcon(QtWidgets.QMessageBox.Warning)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(title)
        error_dialog.setInformativeText(message)
        error_dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)

        for button in error_dialog.buttons():
            button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        error_dialog.exec_()

    def calculateCommon(self):
        x = self.data[self.config["xColumn"]]
        y = self.data[self.config["yColumn"]]

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

        self.modData = pd.DataFrame({'x': x, 'y': y})

    def recalculate(self):
        raise NotImplementedError

    def updateUI(self):
        raise NotImplementedError

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

        # hide if not enabled
        if not self.config["enabled"]:
            self.cursor.setPen(pg.mkPen(color=(0, 0, 0, 0), width=0))
            self.plot.setData(pen=None, symbolPen=None, symbolBrush=None, shadowPen=None)

        else:
            # set cursors
            self.cursor.setPen(pg.mkPen(color=color, width=max(1, self.config["width"] / 2)))
            self.cursor.setZValue(self.config["zIndex"])

            # set to appropritae interpolation with respect to highlighting
            if self.config["interpolation"] == "Keine":
                if self.config["highlight"]:
                    self.plot.setData(pen=None, symbolPen=pen, symbolBrush=highlightColor, shadowPen=None)
                else:
                    self.plot.setData(pen=None, symbolPen=pen, symbolBrush=color, shadowPen=None)

            else:
                self.plot.setData(pen=pen, symbolPen=None, symbolBrush=None, shadowPen=None)

                if self.config["highlight"]:
                    self.plot.setData(shadowPen=highlightPen)

            # set respective z indecies
            if self.config["highlight"]:
                self.cursor.setZValue(Config.Z_IDX_TOP)
                self.plot.setZValue(Config.Z_IDX_TOP)
            else:
                self.cursor.setZValue(self.config["zIndex"])
                self.plot.setZValue(self.config["zIndex"])

        self.plot.setData(np.array(self.interpData["x"]), np.array(self.interpData["y"]))

    def update(self):
        self.recalculate()
        self.updatePlot()
        self.updateUI()

    def applyChange(self, evt, who):
        if who == "color":
            color = QtGui.QColor()
            color.setHsvF(self.config["color"][0] / 360, self.config["color"][1] / 100, self.config["color"][2] / 100)

            colorPicker = QtWidgets.QColorDialog()

            newColor = colorPicker.getColor(color).getHsvF()
            colorPicker.close()

            self.config["color"][0] = int(newColor[0] * 360)
            self.config["color"][1] = int(newColor[1] * 100)
            self.config["color"][2] = int(newColor[2] * 100)

            self.settings.findChild(QtWidgets.QPushButton, "color_select_button").setStyleSheet(
                "background-color: hsv({:d},{:d}%,{:d}%); color: black;".format(
                    self.config["color"][0], self.config["color"][1], self.config["color"][2]))
            self.frame.findChild(QtWidgets.QCheckBox, "enable_checkbox").setStyleSheet(
                "background-color: hsv({:d},{:d}%,{:d}%); color: black;".format(
                    self.config["color"][0], self.config["color"][1], self.config["color"][2]))
        else:
            self.config[who] = evt

        self.update()

# -------------------------------- recoursive -------------------------------- #

    def deselect(self):
        if self.config["highlight"] == True:
            self.setHighlight(False)
            self.updatePlot()

    def getSelected(self):
        raise NotImplementedError

    def getCount(self, i):
        return i+1

    def deleteSelected(self, plot, selected):
        raise NotImplementedError

    def updateCursor(self, mousePoint):
        infoText = ""
        if self.config.get("enabled"):
            # find nearest x-sample to mouse-x pos
            index = np.clip(
                np.searchsorted(self.interpData["x"],
                [mousePoint.x()])[0],
                0, len(self.interpData["y"]) - 1
            )

            self.cursor.setPos(self.interpData["y"][index])

            infoText = "\t  <span style='color: hsv({:d},{:d}%,{:d}%);'>y={:5.3f}</span>".format(
                self.config["color"][0],
                self.config["color"][1],
                self.config["color"][2],
                self.interpData["y"][index])

        return infoText

    def autoscale(self):
        if self.config["enabled"]:
            return [self.plot]
        else:
            return []

    def setHighlight(self, highlight):
        self.config["highlight"] = highlight
        self.plot.setDraggable(highlight)
        self.updatePlot()

    def setEnabled(self, enabled):
        self.config["enabled"] = enabled
        self.updatePlot()

    def setZIndex(self, zIndex):
        raise NotImplementedError


# modified class from user Spencer at
# https://stackoverflow.com/questions/20922836/increases-decreases-qspinbox-value-when-click-drag-mouse-python-pyside
class SuperSpinner(QtWidgets.QLineEdit):
    valueChanged = QtCore.pyqtSignal("float")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setValidator(QtGui.QDoubleValidator(parent=self))
        self.setMaxLength(5)
        self.setReadOnly(True)
        self.textChanged.connect(lambda t: self.valueChanged.emit(float(t)))
        self.setCursor(QtCore.Qt.SizeHorCursor)

        self.mouseStartPos = False
        self.startValue = 0

        self.min = self.max = 0

    def setRange(self, min, max):
        self.min = min
        self.max = max

    def setValue(self, val):
        self.setText(str(val))

    def mouseDoubleClickEvent(self, e):
        self.setValue(0)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.mouseStartPos = e.pos().x()
        self.startValue = float(self.text())

    def mouseMoveEvent(self, e):
        if self.mouseStartPos:

            if e.modifiers() == QtCore.Qt.ShiftModifier:
                multiplier = 1
            elif e.modifiers() == QtCore.Qt.ControlModifier:
                multiplier = 0.01
            else:
                multiplier = 0.1

            valueOffset = round( (self.mouseStartPos + e.pos().x()) * multiplier, 3)
            value = self.startValue + valueOffset
            value = min((self.max, max((self.min, value))))
            self.setValue(value)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.mouseStartPos = False
        # self.unsetCursor()
