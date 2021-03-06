# CSViewer.py
# by Robin Prillwitz
# 11.2.2020
#

import sys
import os.path
import copy
from pathlib import Path
import json

import Config
import Optimizer
import ListWidget
import PlotViewer
import DataFile
import Process
import Cursor

import pyqtgraph as pg
import pandas as pd
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
import qtmodern.styles
import qtmodern.windows

# function tries to generate unique Colors for graphs
def getColor(i):
    if i < len(Config.COLORS):
        return Config.COLORS[i].copy()
    else:
        color = Config.COLORS[i % len(Config.COLORS)].copy()
        color[0] = (color[0] + 10 + 10 * i) % 360
        return color


class CSViewerWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(CSViewerWindow, self).__init__()

        self.sourceList = None
        self.destList = None

        self.setWindowTitle("CSViewer")
        self.setGeometry(50, 50, 1000, 600)

        # Set Window to screen center
        geometry = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        geometry.moveCenter(center)
        self.move(geometry.topLeft())

        # Viewer handles the plotting section
        viewer = QtWidgets.QVBoxLayout()
        self.plot = PlotViewer.PlotViewer(self)
        self.plot.plt.vb.sigRangeChanged.connect(self.recalculateDownsampling)
        self.plotProxy = pg.SignalProxy(self.plot.plt.scene().sigMouseMoved,
             rateLimit=60, slot=self.cursorUpdate)
        viewer.addLayout(self.plot.layout)
        self.plotView = QtWidgets.QWidget(self)
        self.plotView.setLayout(viewer)
        self.plotView.setMinimumSize(300, 300)

        # File list keeping track of all loaded files
        self.fileList = ListWidget.DeselectableListWidget()
        self.fileList.setMinimumWidth(300)
        self.fileList.setObjectName("fileList")
        self.__connectProcess(self)

        self.fileListDock = QtWidgets.QDockWidget("Dateien")
        self.fileListDock.setTitleBarWidget(QtWidgets.QWidget())
        self.fileListDock.setFeatures(
            QtWidgets.QDockWidget.DockWidgetMovable |
            QtWidgets.QDockWidget.DockWidgetFloatable
        )
        self.fileListDock.setWidget(self.fileList)

        self.toolbar = QtWidgets.QToolBar()

        self.addNew = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/add_new.png")), "Hinzufügen")
        self.addNew.clicked.connect(self.openFileNameDialog)
        self.addNew.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.toolbar.addWidget(self.addNew)

        self.addProcessBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/add_process.png")), "Prozess")
        self.addProcessBtn.clicked.connect(self.addProcess)
        self.addProcessBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.toolbar.addWidget(self.addProcessBtn)

        self.addCursorBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/set_max.png")), "Cursor")
        self.addCursorBtn.clicked.connect(self.addCursor)
        self.addCursorBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.toolbar.addWidget(self.addCursorBtn)

        self.removeSelectedBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/delete_select.png")), "Löschen")
        self.removeSelectedBtn.clicked.connect(self.deleteSelected)
        self.removeSelectedBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.toolbar.addWidget(self.removeSelectedBtn)

        self.toolbar.addSeparator()

        self.saveBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/save.png")), "Speichern")
        self.saveBtn.clicked.connect(self.save)
        self.saveBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.toolbar.addWidget(self.saveBtn)

        self.toolbar.addSeparator()

        self.resetBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/fit_screen.png")), "Anpassen")
        self.resetBtn.clicked.connect(self.autoscale)
        self.resetBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.toolbar.addWidget(self.resetBtn)

        self.aspectBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/ratio.png")), "Verhältniss")
        self.aspectBtn.clicked.connect(lambda isLocked: self.plot.plt.vb.setAspectLocked(lock=isLocked, ratio=1))
        self.aspectBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.aspectBtn.setCheckable(True)
        self.toolbar.addWidget(self.aspectBtn)

        # Spacer to push info button to the right
        self.toolbar.addSeparator()

        self.claculateBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/magic.png")), "Berechnen")
        self.claculateBtn.clicked.connect(lambda _: Optimizer.optimizeTime(self)) # TODO pass selected list or self
        self.claculateBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.toolbar.addWidget(self.claculateBtn)

        self.spacer = QtWidgets.QWidget()
        self.spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.toolbar.addWidget(self.spacer)
        self.toolbar.addSeparator()

        self.infoButton = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/help.png")), "Info")
        self.infoButton.clicked.connect(self.showInfo)
        self.infoButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.toolbar.addWidget(self.infoButton)

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.fileListDock)
        self.setCentralWidget(self.plotView)

        self.show()

    def recalculateDownsampling(self):
        for item in self.fileList.list:
            item.updatePlot()

    # disable context menu
    def createPopupMenu(self):
        pass

    # gets all cursors and sets the info text
    def cursorUpdate(self, evt):
        pos = evt[0]  # using signal proxy turns original arguments into a tuple
        if self.plot.plt.sceneBoundingRect().contains(pos):
            mousePoint = self.plot.plt.vb.mapSceneToView(pos)
            self.plot.vLine.setPos(mousePoint.x())

            info = "<span>x={:05.3f}</span>".format(mousePoint.x())

            for index, item in enumerate(self.fileList.list):
                info += item.updateCursor(mousePoint)

            self.plot.setInfoText(info)

    # scales plot based on all enabled objects
    def autoscale(self):
        # disabled graphs and cursors shouldn't influence the view
        cst = {
            "xmin": np.nan,
            "xmax": np.nan,
            "ymin": np.nan,
            "ymax": np.nan
        }

        for item in self.fileList.list:
            icst = item.autoscale()

            cst["xmin"] = min(icst["xmin"], cst["xmin"])
            cst["xmax"] = max(icst["xmax"], cst["xmax"])
            cst["ymin"] = min(icst["ymin"], cst["ymin"])
            cst["ymax"] = max(icst["ymax"], cst["ymax"])

        self.plot.plt.setRange(xRange=(cst["xmin"], cst["xmax"]), yRange=(cst["ymin"], cst["ymax"]),
                padding=0.2, update=True, disableAutoRange=True)

    def deleteSpecific(self, li):
        self.fileList.deleteSelected(self.plot, li.item)
        self.reorder()

    def deleteSelected(self):
        self.fileList.deleteSelected(self.plot)
        self.reorder()

    # sets z-index based on fileList order
    def reorder(self):
        self.fileList.setZIndex(Config.Z_IDX_TOP - 1)

    def updateDisabledButtons(self):
        self.removeSelectedBtn.setDisabled(not (self.fileList.getSelected()))

    def deselectAll(self):
        self.fileList.deselectAll()

# ---------------------------------- Adding ---------------------------------- #

    def beginDrag(self, list):
        if self.sourceList == None and self.destList == None:
            self.sourceList = list

    def endDrag(self, list):
        self.destList = list

    def doDrag(self):

        if self.sourceList == None or self.destList == None:
            return

        if self.sourceList != self.destList:

            item = None
            widget = None

            # get item
            for i in range(0, self.destList.count()):
                match = False
                for j in range(0, len(self.destList.list)):
                    if self.destList.item(i) == self.destList.list[j].item:
                        match = True
                        break
                if not match:
                    item = QtWidgets.QListWidgetItem(self.destList.item(i))
                    self.destList.takeItem(i)
                    break

            # get widget
            for i in range(0, len(self.sourceList.list)):
                match = False
                for j in range(0, self.sourceList.count()):
                    if self.sourceList.list[i].item == self.sourceList.item(j):
                        match = True
                        break
                if not match:
                    widget = self.sourceList.list.pop(i)
                    break

            # clone
            newWidget = copy.copy(widget)

            self.plot.plt.removeItem(widget.plot)
            self.plot.plt.removeItem(widget.cursor)
            # del widget

            self.destList.addItem(newWidget)
            self.plot.addPlot(newWidget)

            if isinstance(newWidget, Process.Process):
                self.__connectProcess(newWidget)

            self.__connectListItem(newWidget)

            self.sourceList.sigCalc.emit()
            self.sourceList.sigUpdateUI.emit()

        self.sourceList = None
        self.destList = None

        self.reorder()
        self.deselectAll()

    def addProcess(self):
        pc = Process.Process(getColor(self.fileList.getCount()))
        self.__connectProcess(pc)
        self.__connectListItem(pc)

        self.fileList.addItem(pc)
        self.plot.addPlot(pc)
        self.reorder()

    def addFile(self, df=None, list=None):
        if not list:
            list = self.fileList

        if not df:
            return

        if df:
            self.__connectListItem(df)
            list.addItem(df)
            self.plot.addPlot(df)
            self.reorder()

    def addCursor(self):
        c = Cursor.Cursor(getColor(self.fileList.getCount()))
        self.fileList.addItem(c)
        self.plot.addPlot(c)

    def __createFile(self, name):
        return DataFile.DataFile(
            name,
            getColor(self.fileList.getCount())
        )

    def __addFileFromName(self, name, list):
        self.addFile(
            self.__createFile(name),
            list
        )

    def __connectListItem(self, li):
        li.sigDeleteMe.connect(self.deleteSpecific)

    def __connectProcess(self, pc):
        pc.fileList.sigSource.connect(self.beginDrag)
        pc.fileList.sigDest.connect(self.endDrag)
        pc.fileList.sigTrigger.connect(self.doDrag)
        pc.fileList.sigDeselect.connect(self.deselectAll)
        pc.fileList.sigUpdateUI.connect(self.updateDisabledButtons)

        pc.fileList.sigAddFile.connect(self.__addFileFromName)

# -------------------------------- Save / Load ------------------------------- #

    # prompts user for input file
    def openFileNameDialog(self):
        options = QtWidgets.QFileDialog.Options()
        filename, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Datei Hinzufügen", "",
                    "CSV Dateien (*.csv);;CSViewer Datei (*.csviewer);;JSON Dateien (*.json);;Alle Dateinen (*)", options=options)

        if filename:
            if filetype == "CSV Dateien (*.csv)":
                self.addFile(df=self.__createFile(filename))
            elif filetype == "CSViewer Datei (*.csviewer)" or filetype == "JSON Dateien (*.json)":
                self.load(filename)

    # prompts user for save-file location and saves data
    def save(self):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                  "CSV Datei (*.csviewer);;JSON Datei (*.json);;Alle Dateinen (*)", options=options)
        if filename:
            file = open(filename, "w")

            dataMainArray = []
            for item in self.fileList.list:
                dataMainArray.append(item.toDict())
                pass

            dataJson = json.dumps({
                "data": dataMainArray
            })
            file.write(dataJson)

            file.close()

    # loads save file
    def load(self, filename):
        file = open(filename, "r")
        dataJson = json.loads(file.read())
        file.close()

        self.load_recursive(dataJson["data"], parentList=self.fileList)
        self.reorder()

    def load_recursive(self, dataJson, parentList):
        for data in dataJson:
            if data["type"] == "cursor":
                c = Cursor.Cursor(
                    data["containing"]["config"]["color"],
                    config=data["containing"]["config"]
                )
                self.__connectListItem(c)
                parentList.addItem(c)
                self.plot.addPlot(c)
            elif data["type"] == "datafile":
                d = DataFile.DataFile(
                    data["containing"]["filename"],
                    data["containing"]["config"]["color"],
                    config=data["containing"]["config"]
                )
                d.data = pd.DataFrame(data["containing"]["data"])
                self.__connectListItem(d)

                parentList.addItem(d)
                self.plot.addPlot(d)
            elif data["type"] == "process":
                p = Process.Process(
                    data["containing"]["config"]["color"],
                    data["containing"]["config"]
                )
                p.data = pd.DataFrame(data["containing"]["data"])
                self.__connectProcess(p)
                self.__connectListItem(p)

                parentList.addItem(p)
                self.plot.addPlot(p)

                self.load_recursive(data["containing"]["children"], p.fileList)


    # shows info box
    def showInfo(self):
        msgBox = QtWidgets.QMessageBox()

        with open(Config.getResource("assets/style.qss"), "r") as fh:
            msgBox.setStyleSheet(fh.read())
        # msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setIconPixmap(splashImg.scaledToWidth(
                app.primaryScreen().size().width() / 3,
                QtCore.Qt.SmoothTransformation
            )
        )
        msgBox.setWindowTitle("Info")
        msgBox.setText("CSViewer")
        msgBox.setInformativeText("""
            <p>von Robin Prillwitz 2020</p>
            <p>Icons von icons8.com in Style iOS Filled.</p>
            In python 3.7 mit pyqt, qtmodern, pyqtgraph, numpy, pandas und scipy, sowie mit Hilfe von Stackoverflow :).</p>
        """)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)

        for button in msgBox.buttons():
            button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        msgBox.exec_()

# ----------------------------------- main ----------------------------------- #

if __name__ == "__main__":

    # set paths for frozen mode
    root = Path()
    if getattr(sys, 'frozen', False):
        root = Path(sys._MEIPASS) # sys has attribute if it's frozen
        qtmodern.styles._STYLESHEET = root / 'qtmodern/style.qss'
        qtmodern.windows._FL_STYLESHEET = root / 'qtmodern/frameless.qss'

    # setup High DPI Support
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    # Create main App
    app = QtWidgets.QApplication(sys.argv)

    app.setApplicationName("CSViewer")
    app.setWindowIcon(QtGui.QIcon(Config.getResource("assets/icon-512.png")))

    # show splash screen
    splashImg = QtGui.QPixmap(Config.getResource("assets/banner.png"))
    splash = QtGui.QSplashScreen(
        splashImg.scaledToWidth(
            app.primaryScreen().size().width() / 2,
            QtCore.Qt.SmoothTransformation
        ),
        QtCore.Qt.WindowStaysOnTopHint
    )
    splash.show()

    # set style (order is important)
    qtmodern.styles.dark(app)
    # initialize program
    gui = CSViewerWindow()

    # start qtmodern
    mw = qtmodern.windows.ModernWindow(gui)
    # close splash on completion
    splash.finish(mw)
    # restore native window frame
    # hacky but works until an official implementation exists
    mw.setWindowFlags(QtCore.Qt.Window)
    mw.titleBar.hide()
    # add handler for global positioning
    gui.window = mw

    # load custom styles
    with open(Config.getResource("assets/style.qss"), "r") as fh:
        gui.setStyleSheet(fh.read())

    highlights = QtGui.QPalette()
    highlights.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0, 230, 118))
    highlights.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(0, 200, 83))
    app.setPalette(highlights)

    mw.show()

    # trigger event loop all 100ms
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    sys.exit(app.exec_())
