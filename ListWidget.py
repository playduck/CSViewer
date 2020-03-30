# ListItem.py
# by Robin Prillwitz
# 16.3.2020
#

import Process
from PyQt5 import QtGui, QtCore, QtWidgets

# Custom List to Deselect Items when whitespace is clicked on
class DeselectableListWidget(QtWidgets.QListWidget):
    sigSource = QtCore.pyqtSignal(["QListWidget"])
    sigDest = QtCore.pyqtSignal(["QListWidget"])
    sigTrigger = QtCore.pyqtSignal()
    sigDeselect = QtCore.pyqtSignal()
    sigUpdateUI = QtCore.pyqtSignal()

    sigAddFile = QtCore.pyqtSignal("QString", "QListWidget")

    sigUpdateUI = QtCore.pyqtSignal()
    sigCalc = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent

        self.list = []

        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.itemClicked.connect(self.activateSelected)

    def addItem(self, li):
        li.sigUpdateUI.connect(self.sigUpdateUI.emit)
        li.sigCalc.connect(self.sigCalc.emit)

        self.list.append(li)
        super().addItem(li.item)
        super().setItemWidget(li.item, li.frame)

        self.sigUpdateUI.emit()
        self.sigCalc.emit()

    def deleteSelected(self, plot, selected=None):
        # get selected item of this list
        if selected == None:
            selected = self.selectedItems()
            if selected:
                selected = selected[0]
            else:
                selected = None

        for index, item in enumerate(self.list):
            # try deleting every sub item
            if not item.deleteSelected(plot, selected):
                # if the item was deleted, remove own references to it
                self.takeItem(index)
                self.list.pop(index)

                self.sigUpdateUI.emit()
                self.sigCalc.emit()
                return

    def deleteChildren(self, plot):
        for item in self.list:
            item.deleteSelected(plot, item.item)

        self.sigUpdateUI.emit()
        self.sigCalc.emit()

    def activateSelected(self, current):
        for item in self.list:
            if item.item == current:
                item.setHighlight(True)
                item.updatePlot()
                return

    def deselectAll(self):
        self.clearSelection()

        for item in self.list:
            item.deselect()

    def getSelected(self):
        selected = self.selectedItems()
        if selected:
            return selected[0]

        for item in self.list:
            selected = item.getSelected()

        return selected

    def getCount(self, i=0):
        for index, item in enumerate(self.list):
            i = item.getCount(i)
        return i

    def setZIndex(self, index):
        for i in range(0, self.count()):
            for j in range(0, len(self.list)):
                if self.item(i) == self.list[j].item:
                    index = self.list[j].setZIndex(index)

        self.list.sort(key=lambda item: item.config["zIndex"], reverse=True)
        return index

# ------------------------------- event handler ------------------------------ #

    def mousePressEvent(self, event):
        self.sigDeselect.emit()
        QtWidgets.QListWidget.mousePressEvent(self, event)
        self.sigUpdateUI.emit()

    def startDrag(self, event):
        self.sigSource.emit(self)
        super().startDrag(event)
        self.sigTrigger.emit()
        self.sigCalc.emit()
        self.sigUpdateUI.emit()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()

            for url in event.mimeData().urls():
                self.sigAddFile.emit(str(url.toLocalFile()), self)

        elif event.mimeData().hasText() or event.mimeData().hasHtml():
            event.ignore()
        else:
            super().dropEvent(event)
            self.sigDest.emit(self)

    def dragHandler(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        elif event.mimeData().hasText() or event.mimeData().hasHtml():
            event.ignore()
        else:
            event.accept()

    def dragEnterEvent(self, event):
        self.dragHandler(event)

    def dragMoveEvent(self, event):
        self.dragHandler(event)
