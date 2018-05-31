from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import matplotlib

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt4agg import FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import pyplot as plt


class PlotWindow(QWidget):
    def __init__(self, title, *args):
        super().__init__(*args)

        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.Window, True)

        layout = QVBoxLayout()

        self.fig = plt.figure()
        self.fig.title(title)

        self.figure_widget = FigureCanvas(self.fig)

        toolbar = NavigationToolbar(self.figure_widget, self)

        layout.addWidget(self.figure_widget)
        layout.addWidget(toolbar)