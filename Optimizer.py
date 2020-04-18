# Optimizer.py
# by Robin Prillwitz
# 2.4.2020
#

import Config
import Process
import Cursor
import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5 import QtTest, QtCore, QtWidgets, QtGui
from scipy.signal import find_peaks
from scipy.optimize import minimize

def __showDialog(type, title, message):
    dialog = QtWidgets.QMessageBox()

    with open(Config.getResource("assets/style.qss"), "r") as fh:
        dialog.setStyleSheet(fh.read())

    dialog.setIcon(type)
    dialog.setWindowTitle(title)
    dialog.setText(title)
    dialog.setInformativeText(message)
    dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)

    for button in dialog.buttons():
        button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

    dialog.exec_()

def __extractObjects(lst):
    limitCursor = None
    compound_data = None

    for item in lst.fileList.list:
        if isinstance(item, Cursor.Cursor):
            if limitCursor == None:
                limitCursor = item
            else:
                __showDialog(QtWidgets.QMessageBox.Warning, "Mehrere Cursor gefunden!", "Das ausgewählte Level enthält mehrere Cursor. Es wird der erste (oberste) verwendet. Alle anderen werden ignoriert.")
        elif isinstance(item, Process.Process):
            if compound_data == None:
                # treating all items in top-level process as datafiles to be optimized
                compound_data = item
            else:
                __showDialog(QtWidgets.QMessageBox.Warning, "Mehrere Prozesse gefunden!", "Das ausgewählte Level enthält mehrere Prozesse. Es wird der erste (oberste) verwendet. Alle anderen werden ignoriert.")
        else:
            __showDialog(QtWidgets.QMessageBox.Warning, "Dateien außerhalb eines Prozesses gefunden!", "Das ausgewählte Level enthält mehrere Dateien außerhalb eines Prozesses. Diese werden ignoriert.")

    if limitCursor == None:
        __showDialog(QtWidgets.QMessageBox.Critical, "Kein Cursor gefunden!", "Das ausgewählte Level enthält keinen Cursor. Es wird ein Cursor benötigt um die Obergrenze anzugeben.")
        return (None, None)

    if compound_data == None:
        __showDialog(QtWidgets.QMessageBox.Critical, "Kein Prozess gefunden!", "Das ausgewählte Level enthält keinen Prozess. Es wird ein Prozess benötigt, dessen Dateien modifiziert werden können.")
        return (None, None)

    if len(compound_data.fileList.list) <= 1:
        __showDialog(QtWidgets.QMessageBox.Critical, "Ungenügend Dateien!", "Der Prozess muss wenigstens zwei Dateien beinhalten um optimiert werden zu können.")
        return (None, None)

    return (limitCursor, compound_data)

def __exceedesLimit(data, limit):
    return (np.where(data["y"] > limit))[0].size > 0

def __error(compound, limit):
    maximum = np.amax(compound["y"])
    error = maximum - limit
    return error

def __doOptimization(compound_data, s):
    compound_data.fileList.list[0].config["xOffset"] += s
    compound_data.fileList.list[0].update()
    QtTest.QTest.qWait(5)

def optimizeTime(lst):
    limitCursor, compound_data = __extractObjects(lst)

    if not limitCursor and not compound_data:
        return

    maxLimit = limitCursor.config["yOffset"]

    if __exceedesLimit(compound_data.interpData, maxLimit) == 0:
        __showDialog(QtWidgets.QMessageBox.Critical, "Keine Optimierung notwendig!", "Der Prozess überschreitet das Limit des Cursors in keinem Punkt. Es wird keine Optimierung durchgeführt.")
        return

    # Generate UI
    progressDialog = QtWidgets.QDialog(flags=QtCore.Qt.WindowStaysOnTopHint)
    layout = QtWidgets.QVBoxLayout()

    dlg = pg.ProgressDialog("Optimierung", cancelText="Abbrechen", busyCursor=True, wait=0, disable=False)
    layout.addWidget(dlg)

    info = QtWidgets.QListWidget()
    layout.addWidget(info)

    progressDialog.setMinimumWidth(500)
    progressDialog.setLayout(layout)
    progressDialog.show()

    dlg.setValue(0)

    # first optimization to get an estimate
    for i in range(0, 3):
        s = round(0.1 ** i, Config.PRECISION)
        iteration = 0

        if __error(compound_data.interpData, maxLimit) > 0:
            condition = lambda: __error(compound_data.interpData, maxLimit) > 0
        else:
            s *= -1
            condition = lambda: __error(compound_data.interpData, maxLimit) < 0

        info.addItem("Optimierung {0} mit größe {1}".format(i, s))
        while condition():
            __doOptimization(compound_data, s)
            iteration += 1
            if dlg.wasCanceled():
                return
            if iteration > 50:
                info.addItem("Iterationslimit von Optimierung {0} erreicht, wird übersprungen".format(i))
                break

        dlg.setValue(dlg.value() + 10)

    aoi = compound_data.fileList.list[0].config["xOffset"]
    s = 0.1
    info.addItem("Ammahe bei {0} mit Unsicherheit {1}".format(round(aoi, 4), s))

    # generate error function
    x = np.linspace(
        aoi - s,
        aoi + s,
        int(2 * Config.PPD))
    y = np.full(len(x), 0.0)

    dlg.setValue(40)
    info.addItem("Erstelle Error Funktion mit {0} Samples zwischen {1} - {2}".format(
            len(x), round(aoi - s, 4), round(aoi + s, 4)))

    increment = 1.0 / (50.0 / len(x))

    # populate error function
    for i, val in enumerate(x):
        compound_data.fileList.list[0].config["xOffset"] = val
        compound_data.fileList.list[0].update()
        y[i] = abs(__error(compound_data.interpData, maxLimit))

        if i % increment == 0:
            dlg.setValue(min([dlg.value() + 1, 90]))
            if dlg.wasCanceled():
                return

    dlg.setValue(95)
    info.addItem("Error Funktion wird evaluiert")

    # eval error function
    minIdxA = np.where(y == y.min())
    minIdx = minIdxA[0][0]

    # set result
    compound_data.fileList.list[0].config["xOffset"] = x[minIdx]
    compound_data.fileList.list[0].update()

    dlg.setValue(99)
    info.addItem("Abgeschlossen")
    QtTest.QTest.qWait(1000 * 2)
    dlg.setValue(100)
