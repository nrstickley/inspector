import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMdiArea, QMenuBar, QAction, QToolBar

from plot_window import PlotWindow


class AnalysisTab(QWidget):
    def __init__(self, inspector, dither, detector, object_id, *args):
        super().__init__(*args)

        self._inspector = inspector

        self._dither = dither

        self._detector = detector

        self._object_id = object_id

        self.contents = list()

        self.setMouseTracking(True)

        layout = QVBoxLayout()
        layout.setSpacing(0)

        self.menubar = self.init_menu()

        self.toolbar = self.init_toolbar()

        self.mdi = QMdiArea(self)

        ##########

        spec = inspector.collection.get_spectrum(dither, detector, object_id)

        plot = PlotWindow(f'dither-{dither}, detector-{detector}, object-{object_id}')

        plot.axis.imshow(spec.science)

        sub_window = self.mdi.addSubWindow(plot)

        ##########

        # TODO: set color of the MDI area with self.mdi.setBackground()

        layout.addWidget(self.menubar)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.mdi)

        self.setLayout(layout)

    @property
    def object_id(self):
        return self._object_id

    @property
    def dither(self):
        return self._dither

    @property
    def detector(self):
        return self._detector

    def init_menu(self):
        menubar = QMenuBar(self)
        menubar.setMouseTracking(True)

        plots = menubar.addMenu('Plots')

        plots.addAction('plot option 1', self.make_plot)
        plots.addAction('plot option 2', self.make_plot)

        info = menubar.addMenu('Info')
        info.addAction('show contaminant table', self.show_info)

        return menubar

    def init_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMouseTracking(True)

        show_table = QAction(QIcon('./table_icon.png'), '', toolbar)
        show_table.setToolTip('show the table of contaminants')
        show_table.triggered.connect(self.show_info)

        toolbar.addAction(show_table)

        return toolbar

    def make_plot(self):
        print('this is where I would make a plot')

    def show_info(self):
        print('this is where I would show info')