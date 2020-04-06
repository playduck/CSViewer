# ListItem.py
# by Robin Prillwitz
# 16.3.2020
#

from PyQt5 import QtGui, QtCore, QtWidgets
from scipy import integrate
from scipy.signal import decimate
from scipy.interpolate import make_interp_spline
from scipy.ndimage.filters import gaussian_filter1d
import pyqtgraph as pg
import numpy as np
import pandas as pd
import Config
import Graph
import Exporter

class ListItem(QtWidgets.QWidget):
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
                "cursorEnabled": True,
                "zIndex": 0,
                "xOffset": 0,
                "yOffset": 0,
                "xColumn": -1,
                "yColumn": -1,
                "color": color,
                "width": 3,
                "interpolation": "linear",
                "interpolationAmount":  100,
                "integrate": 0,
                "filter": 0
            }

        self.cursor = None
        self.plot = None
        self.modData = None
        self.interpData = None
        self.ignore = False
        self.dataUpdated = False

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
        menu.addAction(QtGui.QAction('Interpolation Exportieren', self))
        menu.addAction(QtGui.QAction('Modifikation Exportieren', self))
        menu.addAction(QtGui.QAction('Wave Exportieren', self))
        menu.addSeparator()
        menu.addAction(QtGui.QAction('Löschen', self))

        action = menu.exec_(self.frame.mapToGlobal(event))

        if action:
            if "Exportieren" in action.text():
                Exporter.export(self, action.text())
                # self.__export(action.text())
            elif action.text() == "Löschen":
                self.sigDeleteMe.emit(self)

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

    def calculateCommon(self, dlg=None):
        x = self.data[self.config["xColumn"]].copy()
        y = self.data[self.config["yColumn"]].copy()

        if dlg:
            dlg += 10

        # apply gaussian filter
        if self.config["filter"] > 0:
            y = gaussian_filter1d(y, sigma=self.config["filter"])

        if dlg:
            dlg += 5

        # calculate numeric integration / differential
        if self.config["integrate"] > 0:
            for i in range(self.config["integrate"]):
                for j, val in enumerate(x):
                    y[j] = integrate.quad(lambda _: y[j], 0, val)[0]
                if dlg:
                    dlg += 1
        elif self.config["integrate"] < 0:
            for i in range(abs(self.config["integrate"])):
                y = np.gradient(y, x[1] - x[0])
                if dlg:
                    dlg += 1

        # Add Offsets
        x = x + self.config["xOffset"]
        y = y + self.config["yOffset"]

        if dlg:
            dlg += 10

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

        # set cursors
        if self.config["cursorEnabled"]:
            self.cursor.setPen(pg.mkPen(color=color, width=max(1, self.config["width"] / 2)))
        else:
            self.cursor.setPen(pg.mkPen(color=(0, 0, 0, 0), width=0))

        # hide if not enabled
        if not self.config["enabled"]:
            self.plot.setData(pen=None, symbolPen=None, symbolBrush=None, shadowPen=None)

        else:
            self.cursor.setZValue(self.config["zIndex"])

            # set to appropritae interpolation with respect to highlighting
            if self.config["interpolation"] == "keine":
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

        # if self.dataUpdated:
        # self.plot.setData(self.interpData["x"], self.interpData["y"])
        if self.config["enabled"]:
            self.plot.setDownsampleData(self.interpData["x"], self.interpData["y"])
        self.dataUpdated = False

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
        if self.config.get("enabled") or self.config.get("cursorEnabled"):
            # find nearest x-sample to mouse-x pos
            index = np.clip(
                np.searchsorted(self.interpData["x"],
                [mousePoint.x()])[0],
                0, len(self.interpData["y"]) - 1
            )

            if self.config.get("cursorEnabled"):
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
        if isinstance(self.plot, Graph.Graph):
            self.plot.setDraggable(highlight)
        self.updatePlot()

    def setEnabled(self, enabled):
        self.config["enabled"] = enabled
        self.config["cursorEnabled"] = enabled
        self.updatePlot()

    def setZIndex(self, zIndex):
        raise NotImplementedError


# modified class from user Spencer at
# https://stackoverflow.com/questions/20922836/increases-decreases-qspinbox-value-when-click-drag-mouse-python-pyside
class SuperSpinner(QtWidgets.QLineEdit):
    valueChanged = QtCore.pyqtSignal("float")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setValidator(QtGui.QDoubleValidator(-100000, 100000, Config.PRECISION, parent=self))

        self.editingFinished.connect(self.__handleChange)
        self.setCursor(QtCore.Qt.SizeHorCursor)

        self.beeingEdited = False
        self.mouseStartPos = False
        self.startValue = 0.0
        self.value = 0.0

        self.min = self.max = 0.0
        self.setValue(0.0, True)

    def __handleChange(self):
        t = self.text()
        if (self.beeingEdited or self.mouseStartPos) and t and float(t):
            val = round(float(t), Config.PRECISION)
            # self.valueChanged.emit(val)
            print("Set Val")
            self.setValue(val, True)

    def setRange(self, min, max):
        self.min = min
        self.max = max

    def setValue(self, val, override=False):
        val = round(val, Config.PRECISION)
        if (not self.beeingEdited or override) and (val != self.value):
            self.setText(str(val))
            self.value = val
            self.valueChanged.emit(self.value)

    def focusInEvent(self, QFocusEvent):
        self.beeingEdited = True
        return super().focusInEvent(QFocusEvent)

    def focusOutEvent(self, QFocusEvent):
        self.beeingEdited = False
        return super().focusOutEvent(QFocusEvent)

    def mouseDoubleClickEvent(self, e):
        self.setValue(0.0, True)
        self.valueChanged.emit(0.0)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.mouseStartPos = e.pos().x()
        self.startValue = self.value

    def mouseMoveEvent(self, e):
        if self.mouseStartPos:

            if e.modifiers() == QtCore.Qt.ShiftModifier:
                multiplier = 10
            elif e.modifiers() == QtCore.Qt.ControlModifier:
                multiplier = 0.01
            else:
                multiplier = 0.1

            valueOffset = ( self.mouseStartPos - e.pos().x() ) * multiplier
            value = self.startValue - valueOffset
            value = min((self.max, max((self.min, value))))
            self.value = value
            self.setText(str(value))
            self.valueChanged.emit(self.value)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.mouseStartPos = False
        # self.unsetCursor()
