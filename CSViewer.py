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
import ListWidget
import PlotViewer
import DataFile
import Process

import pyqtgraph as pg
import pandas as pd
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

        # self.mainLayout = QtWidgets.QVBoxLayout()
        # self.subLayout = QtWidgets.QHBoxLayout()

        # Viewer handles the plotting section
        viewer = QtWidgets.QVBoxLayout()
        self.plot = PlotViewer.PlotViewer(self)
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

        # self.fileList.sigSource.connect(self.beginDrag)
        # self.fileList.sigDest.connect(self.endDrag)
        # self.fileList.sigTrigger.connect(self.doDrag)
        # self.fileList.sigDeselect.connect(self.deselectAll)

        self.fileListDock = QtWidgets.QDockWidget("Dateien")
        self.fileListDock.setTitleBarWidget(QtWidgets.QWidget())
        self.fileListDock.setFeatures(
            QtWidgets.QDockWidget.DockWidgetMovable |
            QtWidgets.QDockWidget.DockWidgetFloatable
        )
        self.fileListDock.setWidget(self.fileList)

        # Toolbar related Buttons
        # FIXME toolbar cannot produce extension popup on samall screen width when it's not a child of QMainWindow
        self.toolbar = QtWidgets.QToolBar()

        self.addNew = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/add_new.png")), "Hinzufügen")
        self.addNew.clicked.connect(self.addFile)
        self.addNew.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.toolbar.addWidget(self.addNew)

        self.addProcessBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/add_process.png")), "Prozess")
        self.addProcessBtn.clicked.connect(self.addProcess)
        self.addProcessBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.toolbar.addWidget(self.addProcessBtn)

        self.setMaxBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/set_max.png")), "Maximum")
        # self.setMaxBtn.clicked.connect()
        self.setMaxBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setMaxBtn.setDisabled(True) # TODO
        self.toolbar.addWidget(self.setMaxBtn)

        self.removeSelectedBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/delete_select.png")), "Löschen")
        self.removeSelectedBtn.clicked.connect(self.deleteSelected)
        self.removeSelectedBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.toolbar.addWidget(self.removeSelectedBtn)

        self.toolbar.addSeparator()

        self.saveBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/save.png")), "Speichern")
        self.saveBtn.clicked.connect(self.saveOptions)
        self.saveBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.saveBtn.setDisabled(True) # FIXME
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
        # self.claculateBtn.clicked.connect()
        self.claculateBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.claculateBtn.setDisabled(True) # TODO
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
        considerations = []

        for item in self.fileList.list:
            considerations = considerations + item.autoscale()

        self.plot.plt.autoRange(padding=0.2, items=considerations)

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
        self.deselectAll()
        self.reorder()

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
            df = self.openFileNameDialog()

        if df:
            self.__connectListItem(df)
            list.addItem(df)
            self.plot.addPlot(df)
            self.reorder()

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

        pc.fileList.sigAddFile.connect(self.__addFileFromName)

# -------------------------------- Save / Load ------------------------------- #

    # prompts user for input file
    def openFileNameDialog(self):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                            "CSV Dateien (*.csv);;Alle Dateinen (*)", options=options)
        if filename:
            return self.__createFile(filename)

    # show Option Dialog for saving
    def saveOptions(self):
        saveDialogBox = QtWidgets.QDialog()
        saveDialogBox.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint
        )
        saveDialogBox.setWindowTitle("Speichern")
        with open(Config.getResource("assets/style.qss"), "r") as fh:
            saveDialogBox.setStyleSheet(fh.read())

        layout = QtWidgets.QGridLayout()

        embed = QtWidgets.QCheckBox()
        embedLabel = QtWidgets.QLabel("Daten Einbetten: ")
        embedLabel.setBuddy(embed)

        color = QtWidgets.QCheckBox()
        colorLabel = QtWidgets.QLabel("Farbe speichern: ")
        colorLabel.setBuddy(color)

        rule = QtWidgets.QFrame()
        rule.setFrameShape(QtWidgets.QFrame.HLine)
        rule.setFrameShadow(QtWidgets.QFrame.Sunken)

        OKButton = QtWidgets.QPushButton("Ok")
        OKButton.clicked.connect(saveDialogBox.accept)

        CancelButton = QtWidgets.QPushButton("Abbrechen")
        CancelButton.clicked.connect(saveDialogBox.reject)

        layout.addWidget(embedLabel,    0,0)
        layout.addWidget(embed,         0,1)
        layout.addWidget(colorLabel,    1,0)
        layout.addWidget(color,         1,1)
        layout.addWidget(rule,          2,0,1,0)
        layout.addWidget(OKButton,      3,0,1,0)
        layout.addWidget(CancelButton,  4,0,1,0)

        saveDialogBox.setLayout(layout)
        saveDialogBox.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        ret = saveDialogBox.exec_()
        saveDialogBox.close()

        if ret:
            self.save(embed.isChecked(), color.isChecked())

    # prompts user for save-file location and saves data
    # TODO
    def save(self, embed, color):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                  "CSV Datei (*.csviewer);;JSON Datei (*.json);;Alle Dateinen (*)", options=options)
        if filename:
            file = open(filename, "w")

            dataMainArray = []
            for item in self.fileList.list:
                # dataMainArray.append(data)
                pass

            dataMainDict = {
                "data": dataMainArray
            }
            dataJson = json.dumps(dataMainDict)
            file.write(dataJson)

            file.close()

    # loads save file
    def load(self):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                            "CSV Datei (*.csviewer);;JSON Datei (*.json);;Alle Dateinen (*)",
                                                            options=options)
        if filename:
            file = open(filename, "r")
            dataJson = json.loads(file.read())
            for data in dataJson["data"]:
                if os.path.isfile(data["filename"]) or data["dataEmbed"]:

                    color = data["color"] if data["color"] else getColor(len(self.globalFileList))

                    df = DataFile.DataFile(data["filename"], color, self)
                    df.enabled = data["enabled"]
                    df.width = data["width"]
                    df.xOffset = data["xOffset"]
                    df.yOffset = data["yOffset"]
                    df.interpolation = data["interpolation"]
                    df.interpolationAmount = data["interpolationAmount"]
                    df.integrate = data["integrate"]
                    df.filter = data["filter"]

                    if data["dataEmbed"]:
                        df.data = pd.read_json(data["dataEmbed"])

                    df.initSettings()
                    df.calculateData()

                    # df.plot, df.cursor = self.plot.initPlot(df)
                    self.globalFileList.append(df)
                    self.addFileList(df)
                else:
                    msgBox = QtWidgets.QMessageBox()
                    msgBox.setIcon(QtWidgets.QMessageBox.Critical)
                    msgBox.setWindowTitle("Datei Fehler!")
                    msgBox.setText("{:s} kann nicht gefunden werden!".format(data["filename"]))
                    msgBox.setInformativeText("Die Datei {:s} kann nicht gefunden oder nicht geöffnet werden. Die Datei wird übersprungen.".format(data["filename"]))
                    msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                    msgBox.addButton(QtWidgets.QMessageBox.Abort)

                    if QtWidgets.QMessageBox.Abort == msgBox.exec_():
                        break

            file.close()
            df.updatePlot()

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
