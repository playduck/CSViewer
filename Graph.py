# Graph.py
# by Robin Prillwitz
# 16.3.2020
#

from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg


class Graph(pg.PlotDataItem):
    sigPositionDelta = QtCore.pyqtSignal(float, float)

    def __init__(self, *args, **kwds):
        pg.PlotDataItem.__init__(self, **kwds)
        self.setData(*args)
        self.allowDrag = False

        self.curve.setClickable(True)
        self.curve.mouseDragEvent = self.mouseDragEvent
        self.scatter.mouseDragEvent = self.mouseDragEvent

    def setDraggable(self, isDraggable):
        self.allowDrag = isDraggable

    def mouseDragEvent(self, ev):
        if self.allowDrag:
            if ev.button() != QtCore.Qt.LeftButton:
                ev.ignore()
                return

            delta = ev.pos() - ev.lastPos()
            direction = ev.pos() - ev.buttonDownPos()

            if ev.modifiers() == QtCore.Qt.ShiftModifier:
                if abs(direction[0]) > abs(direction[1]):
                    delta[1] = 0
                else:
                    delta[0] = 0

            self.sigPositionDelta.emit(delta[0], delta[1])
            ev.accept()
        else:
            ev.ignore()
