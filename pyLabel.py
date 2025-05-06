#!/usr/bin/python3

import sys
import pandas as pd

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtGui import QKeySequence
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QShortcut
from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QHBoxLayout
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtWidgets import QSpacerItem
from PyQt6.QtWidgets import QSizePolicy
from PyQt6.QtPrintSupport import QPrintDialog
from PyQt6.QtPrintSupport import QPrinter
from scipy.signal import find_peaks

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

__version__ = '0.5'
__author__ = 'Damon Hinz'


class mainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('pyLabel')
        self._createMenu()
        self.pyLabelWidget = mainWidget(parent=self)
        self.setCentralWidget(self.pyLabelWidget)
        self.printer = QPrinter(QPrinter.PrinterMode.HighResolution)

    def _createMenu(self):
        self.menu = self.menuBar().addMenu('&Menu')

        printAction = QAction('&Print', self)
        printAction.setShortcut('Ctrl+p')
        printAction.triggered.connect(self.printDialog)
        self.menu.addAction(printAction)

        self.menu.addAction('&Exit', self.close)

    def printDialog(self):
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec():
            painter = QPainter(self.printer)
            pixmap = self.grab()
            rect = painter.viewport()
            size = pixmap.size()
            size.scale(rect.size(), Qt.AspectRatioMode.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(pixmap.rect())
            painter.drawPixmap(0, 0, pixmap)


class mainWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.initUI()

        """signals and slots"""
        self.browseFile.clicked.connect(self._browseFiles)
        self.browseFileShort = QShortcut(QKeySequence('Ctrl+O'), self)
        self.browseFileShort.activated.connect(self._browseFiles)
        self.plotButton.clicked.connect(self._on_draw)
        self.plotButtonShort = QShortcut(QKeySequence('Ctrl+G'), self)
        self.plotButtonShort.activated.connect(self._on_draw)

    def _browseFiles(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', '', '*.txt')

        if fname != '':
            headers = ['Mass', 'Intensity']
            self.data = pd.read_csv(str(fname), delim_whitespace=True,
                                    names=headers)
            self.pathToData.setText(fname)

    def _on_draw(self):
        """Plots the data selected"""

        self.height = int(self.heightText.text())
        self.lowpass = float(self.lowpassText.text())

        self.axes.clear()
        self.axes.set_xlabel('Mass to Charge Ratio', fontsize=12)
        self.axes.set_ylabel('Intensity', fontsize=12)

        if self.label_peaks.isChecked():
            try:

                self.heights = []
                self.x = self.data['Mass']
                self.y = self.data['Intensity']
                self.sum = 0

                peaks, _ = find_peaks(self.y, self.height)
                self.peaks = [self.x[idx] for idx in peaks]

                for key in _.keys():
                    self.heights.append(_[key])
                    self.heights = self.heights[0]
                    self.heights = self.heights.tolist()

                for x, y in zip(self.peaks, self.heights):
                    if x < self.lowpass:
                        continue
                    else:
                        self.sum += y
                        self.axes.annotate('%s' %x, xy=(x, y), xytext=(-5, 4),
                                           textcoords='offset points', fontsize=7)

                cell_text = [(i, j) for i, j in zip(self.peaks, self.heights) if
                             i > self.lowpass]
                the_table = self.axes.table(cellText=cell_text,
                                            colLabels=['Peak', 'Intensity'],
                                            loc='right')
                the_table.auto_set_column_width((-1, 0, 1, 2, 3))
                the_table.scale(1, 2)
                print(f"Total of peaks: {self.sum}")
            except IndexError:
                pass

        self.axes.plot(self.data['Mass'], self.data['Intensity'])
        self.canvas.draw()

    def initUI(self):
        self.data = pd.DataFrame()

        """initiate main UI"""

        mainLayout = QVBoxLayout()

        """Add line for path to data and button for data browser"""
        self.pathToData = QLineEdit()
        self.browseFile = QPushButton('&Open')
        self.plotButton = QPushButton('&Graph')

        browseLinePosition = QHBoxLayout()
        browseLinePosition.addWidget(self.pathToData)
        browseLinePosition.addWidget(self.browseFile)
        browseLinePosition.addWidget(self.plotButton)

        """Create the canvas for MPL"""
        self.main_frame = QWidget()
        self.dpi = 100
        self.fig = Figure((10, 10), dpi=self.dpi)
        self.fig.subplots_adjust(left=0.058, right=0.915, top=0.979,
                                 bottom=0.086, hspace=0.200, wspace=0.200)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_xlabel('Mass to Charge Ratio', fontsize=12)
        self.axes.set_ylabel('Intensity', fontsize=12)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        """Widgets for peak picking"""
        height_label = QLabel('Peak height:')
        self.heightText = QLineEdit()
        self.heightText.setMaximumWidth(300)
        self.heightText.setText('1000')

        lowpass_label = QLabel("Low mass filter: ")
        self.lowpassText = QLineEdit()
        self.lowpassText.setMaximumWidth(300)
        self.lowpassText.setText("16.00")

        self.label_peaks = QCheckBox('Label peaks')
        self.label_peaks.setChecked(False)
        self.spaceItem = QSpacerItem(150, 10, QSizePolicy.Policy.Expanding)

        labelLinePosition = QHBoxLayout()
        labelLinePosition.addWidget(self.label_peaks)
        labelLinePosition.addSpacerItem(self.spaceItem)
        labelLinePosition.addWidget(height_label)
        labelLinePosition.addWidget(self.heightText)
        labelLinePosition.addWidget(lowpass_label)
        labelLinePosition.addWidget(self.lowpassText)

        """Update widget and layout"""
        mainLayout.addLayout(browseLinePosition)
        mainLayout.addWidget(self.canvas)
        mainLayout.addWidget(self.mpl_toolbar)
        mainLayout.addLayout(labelLinePosition)
        self.setLayout(mainLayout)

        self.show()


def main():
    app = QApplication(sys.argv)
    win = mainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
