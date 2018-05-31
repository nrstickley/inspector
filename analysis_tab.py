import numpy as np
import matplotlib

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt4agg import FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import pyplot as plt

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout


class PlotView(QWidget):
    def __init__(self, *args):
        super().__init__(*args)

        mpl_layout = QVBoxLayout()

        fig = plt.figure()

        x = np.arange(-10, 10, 0.1)

        y = np.arctan(x)

        plt.plot(x, y, label='arctan(x)')
        plt.xlabel('the x-coordinate')
        plt.ylabel('$f(x)$')
        plt.title("This is an embedded MatPlotLib figure!")
        plt.legend()

        fig_canvas = FigureCanvas(fig)

        toolbar = NavigationToolbar(fig_canvas, self)

        mpl_layout.addWidget(toolbar)
        mpl_layout.addWidget(fig_canvas)

        self.setLayout(mpl_layout)


class AnalysisTab(QWidget):
    def __init__(self, inspector, object_id, *args):
        super().__init__(*args)

        self._inspector = inspector

        self._object_id = object_id

        self.contents = list()

        layout = QGridLayout()
        layout.setSpacing(0)

        self.setLayout(layout)

        self.layout().addWidget(PlotView(), 0, 0)
        self.layout().addWidget(PlotView(), 0, 1)
        self.layout().addWidget(PlotView(), 1, 0)
        self.layout().addWidget(PlotView(), 1, 1)

    @property
    def object_id(self):
        return self._object_id


def make_plot_window(title):
    window = QWidget()
    window.setWindowTitle(title)
    window.setWindowFlag(Qt.WindowStaysOnTopHint, True)
    window.setWindowFlag(Qt.Window, True)

    layout = QVBoxLayout()
    window.setLayout(layout)

    fig = plt.figure()
    fig.title(title)

    figure_widget = FigureCanvas(fig)

    toolbar = NavigationToolbar(figure_widget, window)

    layout.addWidget(figure_widget)
    layout.addWidget(toolbar)


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
