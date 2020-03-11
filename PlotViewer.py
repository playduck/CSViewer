# Plot.py
# by Robin Prillwitz
# 11.2.2020
#

import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

Z_IDX_TOP = 201


class Graph(pg.PlotCurveItem):
    sigUpdated = QtCore.pyqtSignal()
    def __init__(self, dataFile, *args, **kwds):

        self.dataFile = dataFile

        pg.PlotCurveItem.__init__(self, **kwds)
        pg.PlotCurveItem.setData(self, *args)

    def mouseDragEvent(self, ev):

        if self.dataFile.highlight:
            if ev.button() != QtCore.Qt.LeftButton:
                ev.ignore()
                return

            delta = ev.pos() - ev.lastPos()
            direction = ev.pos() - ev.buttonDownPos()

            # snapping isn't quite optimal
            # requires use of tempX/tempY and committing those to xOffset/yOffset on mouse up
            if ev.modifiers() == QtCore.Qt.ShiftModifier:
                if abs(direction[0]) > abs(direction[1]):
                    self.dataFile.xOffset += delta[0]
                else:
                    self.dataFile.yOffset += delta[1]
            else:
                self.dataFile.xOffset += delta[0]
                self.dataFile.yOffset += delta[1]

            self.dataFile.calculateData()
            self.dataFile.updateUIData()

            self.sigUpdated.emit()
            ev.accept()
        else:
            ev.ignore()


# handles all graphing
class PlotViewer:
    def __init__(self, toolbar, parent):
        self.parent = parent

        pg.setConfigOptions(antialias=True, background="#1E1E1E", useWeave=True)

        self.win = pg.GraphicsWindow()
        self.plt = self.win.addPlot(enableMenu=False)

        self.plt.showGrid(True, True, 0.6)
        self.plt.hideButtons()
        self.plt.autoRange(padding=0.2)

        # vLine for vertical x-Axis cursor
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.vLine.setPen((255,255,255,200))
        self.vLine.setZValue(Z_IDX_TOP + 1)
        self.plt.addItem(self.vLine, ignoreBounds=True)

        # proxy needed for cursors
        self.proxy = pg.SignalProxy(self.plt.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

        # Custom Toolbar Buttons
        self.resetBtn = QtWidgets.QPushButton(QtGui.QIcon("./assets/fit_screen.png"), "Anpassen")
        self.resetBtn.clicked.connect(lambda x, who="autoscale": self.toolbarHandler(x, who))
        self.resetBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        toolbar.addWidget(self.resetBtn)

        # Info Region below Plot
        self.info = QtWidgets.QLabel()
        self.info.setAlignment(QtCore.Qt.AlignCenter)

        # Add to Layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.win)
        self.layout.addWidget(self.info)

    # responds to toolbar buttons
    def toolbarHandler(self, on, who):
        if who == "autoscale":
            considerations = []
            for i in range(0, len(self.parent.globalFileList)):
                if self.parent.globalFileList[i].enabled:
                    considerations.append(self.parent.globalFileList[i].plot)

            self.plt.autoRange(padding=0.2, items=considerations)

    # adds a new plot
    def initPlot(self, dataFile):
        x = dataFile.modData["x"]
        y = dataFile.modData["y"]

        color = QtGui.QColor()
        color.setHsvF(dataFile.color[0] / 360, dataFile.color[1] / 100, dataFile.color[2] / 100)

        pen = pg.mkPen(color=color, width=dataFile.width)
        cursor = pg.InfiniteLine(angle=0, movable=False)
        cursor.setPen(pg.mkPen(color=color, width=dataFile.width))

        # plot = self.plt.plot(x, y, pen=pen, symbolPen=None, symbolBrush=None, symbol='o', symbolSize=5)

        plot = Graph(dataFile, np.array(x), np.array(y), pen=pen, symbolPen=None, symbolBrush=None, symbol='o', symbolSize=5)
        plot.sigClicked.connect(self.parent.highlightClicked)
        plot.sigUpdated.connect(self.parent.updatePlot)

        self.plt.addItem(plot)
        self.plt.addItem(cursor, ignoreBounds=True)

        return plot, cursor

    # updates all plot styles and data
    def update(self, dataFiles):
        for i in range(0, len(dataFiles)):
            df = dataFiles[i]

            color = QtGui.QColor()
            color.setHsvF(df.color[0] / 360,
                          df.color[1] / 100,
                          df.color[2] / 100)
            pen = pg.mkPen(color=color, width=df.width)

            highlightColor = QtGui.QColor()
            highlightColor.setHsvF(df.color[0] / 360,
                                   df.color[1] / 100,
                                   df.color[2] / 100, 0.2)
            highlightPen = pg.mkPen(color=highlightColor, width=df.width * 4 + 10)

            if not df.enabled:
                df.cursor.setPen(pg.mkPen(color=(0, 0, 0, 0), width=0))
                df.plot.setData(pen=None, symbolPen=None, symbolBrush=None, shadowPen=None)
                # df.plot.curve.setClickable(False)

            else:
                #df.cursor.setPen(pg.mkPen(color=color, width=1))
                df.cursor.setPen(pg.mkPen(color=color, width=max(1, df.width / 2)))

                df.cursor.setZValue(df.zIndex)
                # df.plot.curve.setClickable(True, width=df.width * 4 + 10)

                if df.interpolation == "Keine":
                    if df.highlight:
                        df.plot.setData(pen=None, symbolPen=pen, symbolBrush=highlightColor, shadowPen=None)
                    else:
                        df.plot.setData(pen=None, symbolPen=pen, symbolBrush=color, shadowPen=None)

                else:
                    df.plot.setData(pen=pen, symbolPen=None, symbolBrush=None, shadowPen=None)

                    if df.highlight:
                        df.plot.setData(shadowPen=highlightPen)

                if df.highlight:
                    df.cursor.setZValue(Z_IDX_TOP)
                    df.plot.setZValue(Z_IDX_TOP)
                else:
                    df.cursor.setZValue(df.zIndex)
                    df.plot.setZValue(df.zIndex)

            df.plot.setData(np.array(df.modData["x"]), np.array(df.modData["y"]))

    # updates cursors and info text
    def mouseMoved(self, evt):
        pos = evt[0]  # using signal proxy turns original arguments into a tuple
        if self.plt.sceneBoundingRect().contains(pos):
            mousePoint = self.plt.vb.mapSceneToView(pos)
            self.vLine.setPos(mousePoint.x())

            info = "<span>x={:05.2f}</span>".format(mousePoint.x())

            for i in range(0, len(self.parent.globalFileList)):
                if self.parent.globalFileList[i].enabled:

                    index = np.clip(np.searchsorted(self.parent.globalFileList[i].modData["x"], [mousePoint.x()])[0],
                                    0, len(self.parent.globalFileList[i].modData["y"]) - 1)

                    self.parent.globalFileList[i].cursor.setPos(self.parent.globalFileList[i].modData["y"][index])

                    info += "\t  <span style='color: hsv({:d},{:d}%,{:d}%);'>y={:5.3f}</span>".format(
                        self.parent.globalFileList[i].color[0],
                        self.parent.globalFileList[i].color[1],
                        self.parent.globalFileList[i].color[2],
                        self.parent.globalFileList[i].modData["y"][index])

            self.info.setText(info)
