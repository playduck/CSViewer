# CSViewer.py
# by Robin Prillwitz
# 11.2.2020
#

import sys
import os.path
import json
import Plot
import DataFile
import pandas as pd
from PyQt5 import QtGui, QtCore, QtWidgets
import qtmodern.styles
import qtmodern.windows

# Colors in HSV for Graphs
COLORS = [
    [47, 81, 100],
    [197, 88, 100],
    [116, 73, 96],
    [273, 86, 100],
    [10, 88, 96]
]


# function tries to generate unique Colors for graphs
def getColor(i):
    if i < len(COLORS):
        return COLORS[i].copy()
    else:
        color = COLORS[i % len(COLORS)].copy()
        color[0] = (color[0] + 20 * i) % 360
        return color


class CSViewerWindow(QtWidgets.QWidget):
    def __init__(self):
        super(CSViewerWindow, self).__init__()

        self.globalFileList = []
        self.window = None

        self.setWindowTitle("CSViewer")
        self.setGeometry(50, 50, 1000, 500)
        # Set Window to screen center
        geometry = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        geometry.moveCenter(center)
        self.move(geometry.topLeft())

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.subLayout = QtWidgets.QHBoxLayout()

        # Toolbar related Buttons
        self.toolbar = QtWidgets.QToolBar()

        self.addNew = QtWidgets.QPushButton(QtGui.QIcon("./assets/add_new.png"), "Hinzufügen")
        self.addNew.clicked.connect(self.openFileNameDialog)
        self.toolbar.addWidget(self.addNew)

        self.removeSelectedBtn = QtWidgets.QPushButton(QtGui.QIcon("./assets/delete_select.png"), "Löschen")
        self.removeSelectedBtn.clicked.connect(self.deleteSelected)
        self.toolbar.addWidget(self.removeSelectedBtn)

        self.toolbar.addSeparator()

        self.saveBtn = QtWidgets.QPushButton(QtGui.QIcon("./assets/save.png"), "Speichern")
        self.saveBtn.clicked.connect(self.saveOptions)
        self.toolbar.addWidget(self.saveBtn)

        self.loadBtn = QtWidgets.QPushButton(QtGui.QIcon("./assets/load.png"), "Laden")
        self.loadBtn.clicked.connect(self.load)
        self.toolbar.addWidget(self.loadBtn)

        self.toolbar.addSeparator()

        # Viewer handles the plotting section
        self.viewer = QtWidgets.QVBoxLayout()
        self.plot = Plot.Plot(self.toolbar, self)
        self.viewer.addLayout(self.plot.layout)

        # Spacer to push info button to the right
        self.toolbar.addSeparator()
        self.spacer = QtWidgets.QWidget()
        self.spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.toolbar.addWidget(self.spacer)
        self.toolbar.addSeparator()

        self.infoButton = QtWidgets.QPushButton(QtGui.QIcon("./assets/help.png"), "Info")
        self.infoButton.clicked.connect(self.showInfo)
        self.toolbar.addWidget(self.infoButton)

        # File list keeping track of all loaded files
        self.fileList = QtWidgets.QListWidget()
        self.fileList.setMinimumWidth(320)
        self.fileList.setMaximumWidth(350)
        self.fileList.itemClicked.connect(self.highlightSelected)

        # adding widgets and layouts
        self.subLayout.addWidget(self.fileList)
        self.subLayout.addLayout(self.viewer)
        self.mainLayout.addWidget(self.toolbar)
        self.mainLayout.addLayout(self.subLayout)

        self.setLayout(self.mainLayout)
        self.show()

        self.updatePlot()

    # update drawing and redraw
    def updatePlot(self):
        self.plot.update(self.globalFileList)

    # highlight plot based on itemList
    def highlightSelected(self, item):
        for i in range(0, len(self.globalFileList)):
            self.globalFileList[i].highlight = item == self.globalFileList[i].item
        self.updatePlot()

    # gets selected datafile
    def deleteSelected(self):
        selected = self.fileList.currentItem()
        for i in range(0, len(self.fileList)):
            if self.fileList.item(i) == selected:
                self.deleteFileList(self.globalFileList[i])

    # deletes given datafile from self and the list
    def deleteFileList(self, df):
        self.plot.plt.removeItem(df.plot)
        self.plot.plt.removeItem(df.cursor)
        for i in range(0, len(self.globalFileList)):
            if self.globalFileList[i] == df:
                self.globalFileList.pop(i)
                break
        for i in range(0, len(self.fileList)):
            if self.fileList.item(i) == df.item:
                self.fileList.takeItem(i)
                break
        del df
        self.plot.update(self.globalFileList)

    # adds a datafile from a file
    def addFileList(self, df):
        temp = df.showListItem()
        self.fileList.addItem(temp[0])
        self.fileList.setItemWidget(temp[0], temp[1])

        self.plot.update(self.globalFileList)

        return df

    # prompts user for input file
    def openFileNameDialog(self):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                            "CSV Dateien (*.csv);;Alle Dateinen (*)", options=options)
        if filename:
            df = DataFile.DataFile(filename, self, getColor(len(self.globalFileList)))
            df.initSettings()
            df.calculateData()
            df.plot, df.cursor = self.plot.initilizePlot(df)
            self.globalFileList.append(df)
            self.addFileList(df)

    # show Option Dialog for saving
    def saveOptions(self):
        saveDialogBox = QtWidgets.QDialog()
        saveDialogBox.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint
        )
        layout = QtWidgets.QGridLayout()

        embed = QtWidgets.QCheckBox()
        embedLabel = QtWidgets.QLabel("Daten Einbetten: ")
        embedLabel.setBuddy(embed)

        color = QtWidgets.QCheckBox()
        colorLabel = QtWidgets.QLabel("Farbe speichern: ")
        colorLabel.setBuddy(color)

        OKButton = QtWidgets.QPushButton("Ok")
        OKButton.clicked.connect(saveDialogBox.accept)

        CancelButton = QtWidgets.QPushButton("Abbrechen")
        CancelButton.clicked.connect(saveDialogBox.reject)

        layout.addWidget(embedLabel,    0,0)
        layout.addWidget(embed,         0,1)
        layout.addWidget(colorLabel,    1,0)
        layout.addWidget(color,         1,1)

        layout.addWidget(OKButton,      2,0)
        layout.addWidget(CancelButton,  2,1)

        saveDialogBox.setLayout(layout)
        saveDialogBox.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        ret = saveDialogBox.exec_()
        saveDialogBox.close()

        if ret:
            self.save(embed.isChecked(), color.isChecked())

    # prompts user for save-file location and saves data
    def save(self, embed, color):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                  "CSV Datei (*.csviewer);;JSON Datei (*.json);;Alle Dateinen (*)", options=options)
        if filename:
            file = open(filename, "w")

            dataMainArray = []
            for i, df in enumerate(self.globalFileList):
                data = {
                    "filename": df.filename,
                    "enabled": df.enabled,
                    "color": df.color if color else None,
                    "width": df.width,
                    "xOffset": df.xOffset,
                    "yOffset": df.yOffset,
                    "interpolation": df.interpolation,
                    "interpolationAmount": df.interpolationAmount,
                    "integrate": df.integrate,
                    "filter": df.filter,
                    "dataEmbed": df.data.to_json() if embed else None
                }
                dataMainArray.append(data)

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
            for i, data in enumerate(dataJson["data"]):
                if os.path.isfile(data["filename"]) or data["dataEmbed"]:

                    color = data["color"] if data["color"] else getColor(len(self.globalFileList))

                    df = DataFile.DataFile(data["filename"], self, color)
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

                    df.plot, df.cursor = self.plot.initilizePlot(df)
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
            self.updatePlot()

    # shows info box
    def showInfo(self):
        msgBox = QtWidgets.QMessageBox()
        # msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setIconPixmap(QtGui.QPixmap("./assets/logo.png"))
        msgBox.setWindowTitle("Info")
        msgBox.setText("CSViewer")
        msgBox.setInformativeText("""
            <p>von Robin Prillwitz 2020</p>
            <p>Icons von icons8.com in Style Office.</p>
            In python 3.7 mit pyqt, qtmodern, pyqtgraph, numpy, pandas und scipy, sowie mit Hilfe von Stackoverflow :).</p>
        """)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.exec_()


# main entry point
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # show splash screen
    splashImg = QtGui.QPixmap("./assets/logo.png")
    splash = QtGui.QSplashScreen(splashImg, QtCore.Qt.WindowStaysOnTopHint)
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
    with open("./style.qss", "r") as fh:
        gui.setStyleSheet(fh.read())

    mw.show()

    sys.exit(app.exec_())
