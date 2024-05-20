#!/usr/bin/python

import sys, random, os, sip
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

BRUSH_SIZE=3

from pydemo.canvas_panel import CanvasPanel
from pydemo.mypaint_canvas import MypaintCanvas
        
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()
        
    def initUI(self):
        # main window
        self.setGeometry(300, 200, 500, 700)
        self.center()
        self.setWindowTitle('MyPaint demo')

        # central widget
        canvas = MypaintCanvas(QSize(1024, 1024))
        cwidget = CanvasPanel(canvas)
        self.setCentralWidget(cwidget)
        # status bar
        self.statusBar().showMessage('Ready')

        # menu bar
        menubar = self.menuBar()
        #menubar.setNativeMenuBar(False)
        fileMenu = menubar.addMenu('&File')

        undoAct = QAction('Undo', self)
        undoAct.setShortcut('Ctrl+Z')
        undoAct.setStatusTip('Undo last action')
        undoAct.triggered.connect(cwidget.undo)
        
        undoAct = QAction('Redo', self)
        undoAct.setShortcut('Ctrl+Shift+Z')
        undoAct.setStatusTip('Reverse last undo operation')
        undoAct.triggered.connect(cwidget.undo)
        
        exitAct = QAction('&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAct)
        
        # toolbar
        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.addAction(exitAct)

        # show
        self.show()

    def contextMenuEvent(self, event):
           cmenu = QMenu(self)
           openAct = cmenu.addAction("Open")
           quitAct = cmenu.addAction("Quit")
           action = cmenu.exec_(self.mapToGlobal(event.pos()))
           if action == quitAct:
               qApp.quit()
               
    def xcloseEvent(self, event):
        print("closeEvent handler.")
        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def center(self):
        windowrec = self.frameGeometry()
        centerpt = QDesktopWidget().availableGeometry().center()
        windowrec.moveCenter(centerpt)
        self.move(windowrec.topLeft())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
