# Graph.py
# by Robin Prillwitz
# 16.3.2020
#

from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import numpy as np
import Config


class Graph(pg.PlotDataItem):
    sigPositionDelta = QtCore.pyqtSignal(float, float)

    def __init__(self, *args, **kwds):
        pg.PlotDataItem.__init__(self, **kwds)
        self.setData(*args)
        self.allowDrag = False
        self.limit = 500

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

    # modified from the pyqtgraph example at
    # https://github.com/pyqtgraph/pyqtgraph/blob/develop/examples/hdf5.py
    def setDownsampleData(self, x, y):
        if x is None or y is None:
            self.setData([])
            return

        vb = self.getViewBox()
        if vb is None:
            return  # no ViewBox yet

        # Determine what data range must be read
        xrange = vb.viewRange()[0]
        limits = [
            max(0,int(xrange[0])-1),
            min(len(x), int(xrange[1]+2)) ]
        start = np.min(limits)
        stop = np.max(limits)

        # Decide by how much we should downsample
        ds = int((stop-start) / self.limit) + 1

        if ds == 1:
            # Small enough to display with no intervention.
            visible = y
            scale = 1
            start = 0
        else:
            # Here convert data into a down-sampled array suitable for visualizing.
            # Must do this piecewise to limit memory usage.
            samples = 1 + ((stop-start) // ds)
            visible = np.zeros(samples*2, dtype=y.dtype)
            sourcePtr = start
            targetPtr = 0

            chunkSize = (100000//ds) * ds
            while sourcePtr < stop-1:
                chunk = y[sourcePtr:min(stop,sourcePtr+chunkSize)]
                sourcePtr += len(chunk)

                # reshape chunk to be integral multiple of ds
                chunk = chunk[:(len(chunk)//ds) * ds].reshape(len(chunk)//ds, ds)

                # compute max and min
                chunkMax = chunk.max(axis=1)
                chunkMin = chunk.min(axis=1)

                # interleave min and max into plot data to preserve envelope shape
                visible[targetPtr:targetPtr+chunk.shape[0]*2:2] = chunkMin
                visible[1+targetPtr:1+targetPtr+chunk.shape[0]*2:2] = chunkMax
                targetPtr += chunk.shape[0]*2

            visible = visible[:targetPtr]
            scale = ds * 0.5

        self.setData(x[0:len(visible)], visible) # update the plot
        self.setPos(start, 0) # shift to match starting index
        self.resetTransform()
        self.scale(scale, 1)  # scale to match downsampling
