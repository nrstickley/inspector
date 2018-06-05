from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import matplotlib

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import pyplot as plt


class PlotWindow(QWidget):
    def __init__(self, title, shape=None, *args):
        super().__init__(*args)

        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.Window, True)
        self.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title = title

        if shape is None:
            self.fig, self.axis = plt.subplots()
            self.axis.set_title(self.title)
        else:
            rows, columns = shape
            self.fig, self.axis = plt.subplots(rows, columns)
            self.fig.suptitle(title)

        self.fig.set_dpi(100)

        self.figure_widget = FigureCanvas(self.fig)

        toolbar = NavigationToolbar(self.figure_widget, self)

        layout.addWidget(self.figure_widget)
        layout.addWidget(toolbar)

        self.setLayout(layout)

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Q or event.key() == Qt.Key_Escape:
            self.close()
