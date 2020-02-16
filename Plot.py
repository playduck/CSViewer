# Plot.py
# by Robin Prillwitz
# 11.2.2020
#

import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

# handles all graphing
class Plot:
    def __init__(self, toolbar, parent):
        self.parent = parent

        pg.setConfigOptions(antialias=True)
        self.win = pg.GraphicsWindow()
        self.plt = self.win.addPlot()

        self.plt.showGrid(True, True, 0.6)
        self.plt.hideButtons()
        # self.pw = pg.PlotWidget()

         # vLine for vertical x-Axis cursor
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.vLine.setPen((255,255,255,200))
        self.plt.addItem(self.vLine, ignoreBounds=True)

        # proxy needed for cursors
        self.proxy = pg.SignalProxy(self.plt.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

        # Custom Toolbar Buttons
        self.btnReset = QtWidgets.QPushButton(QtGui.QIcon("./assets/fit_screen.png"), "Anpassen")
        self.btnReset.clicked.connect(lambda x, who="autoscale": self.toolbarHandler(x, who))

        toolbar.addWidget(self.btnReset)

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

            self.plt.autoRange(items=considerations)

    # adds a new plot
    def initilizePlot(self, dataFile):
        x = dataFile.modData["x"]
        y = dataFile.modData["y"]

        color = QtGui.QColor()
        color.setHsvF(dataFile.color[0] / 360, dataFile.color[1] / 100, dataFile.color[2] / 100)

        pen = pg.mkPen(color=color, width=dataFile.width)
        cursor = pg.InfiniteLine(angle=0, movable=False)
        cursor.setPen(pg.mkPen(color=color, width=1))

        plot = self.plt.plot(x, y, pen=pen, symbolPen=None, symbolBrush=None, symbol='o', symbolSize=5)
        self.plt.addItem(cursor, ignoreBounds=True)

        return plot, cursor

    # updates all plot styles and data
    def update(self, dataFiles):
        for i in range(0, len(dataFiles)):
            color = QtGui.QColor()
            color.setHsvF(dataFiles[i].color[0] / 360, dataFiles[i].color[1] / 100, dataFiles[i].color[2] / 100)
            pen = pg.mkPen(color=color, width=dataFiles[i].width)

            highlightColor = QtGui.QColor()
            highlightColor.setHsvF(dataFiles[i].color[0] / 360, dataFiles[i].color[1] / 100, dataFiles[i].color[2] / 100, 0.2)
            highlightPen = pg.mkPen(color=highlightColor, width=dataFiles[i].width * 4 + 10)

            if not dataFiles[i].enabled:
                dataFiles[i].cursor.setPen(pg.mkPen(color=(0,0,0,0), width=0))
                dataFiles[i].plot.setData(pen=None, symbolPen=None, symbolBrush=None, shadowPen=None)

            else:
                dataFiles[i].cursor.setPen(pg.mkPen(color=color, width=1))

                if dataFiles[i].interpolation == "Keine":
                    if dataFiles[i].highlight:
                        dataFiles[i].plot.setData(pen=None, symbolPen=pen, symbolBrush=highlightColor, shadowPen=None)
                    else:
                        dataFiles[i].plot.setData(pen=None, symbolPen=pen, symbolBrush=color, shadowPen=None)
                else:
                    dataFiles[i].plot.setData(pen=pen, symbolPen=None, symbolBrush=None, shadowPen=None)
                    if dataFiles[i].highlight:
                        dataFiles[i].plot.setData(shadowPen=highlightPen)

            dataFiles[i].plot.setData(dataFiles[i].modData["x"], dataFiles[i].modData["y"])

    # updates cursors and info text
    def mouseMoved(self, evt):
        pos = evt[0]  # using signal proxy turns original arguments into a tuple
        if self.plt.sceneBoundingRect().contains(pos):
            mousePoint = self.plt.vb.mapSceneToView(pos)
            self.vLine.setPos(mousePoint.x())

            info = "<span>x={:05.2f}</span>".format(mousePoint.x())

            for i in range(0, len(self.parent.globalFileList)):
                index = np.clip(np.searchsorted(self.parent.globalFileList[i].modData["x"], [mousePoint.x()])[0],
                                0, len(self.parent.globalFileList[i].modData["y"]) - 1)

                self.parent.globalFileList[i].cursor.setPos(self.parent.globalFileList[i].modData["y"][index])

                info += "\t  <span style='color: hsv({:d},{:d}%,{:d}%);'>y={:4.2f}</span>".format(
                    self.parent.globalFileList[i].color[0],
                    self.parent.globalFileList[i].color[1],
                    self.parent.globalFileList[i].color[2],
                    self.parent.globalFileList[i].modData["y"][index])

            self.info.setText(info)

