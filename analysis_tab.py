import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMdiArea, QMenuBar, QAction, QToolBar

from plot_window import PlotWindow
from detector_selector import MultiDetectorSelector


class AnalysisTab(QWidget):
    def __init__(self, inspector, dither, detector, object_id, *args):
        super().__init__(*args)

        self._inspector = inspector

        self._dither = dither

        self._detector = detector

        self._object_id = object_id

        self.contents = list()

        self.setMouseTracking(True)
        outer_layout = QHBoxLayout()
        outer_layout.setSpacing(0)
        outer_layout.setContentsMargins(5,5,5,5)

        #TODO: put 4 of these into a widget with Vbox layout

        selector_1 = MultiDetectorSelector()
        selector_1.setMinimumWidth(180)

        outer_layout.addWidget(selector_1)

        inner_layout = QVBoxLayout()
        inner_layout.setSpacing(0)

        outer_layout.addItem(inner_layout)

        self.toolbar = self.init_toolbar()

        self.mdi = QMdiArea(self)

        ##########

        spec = inspector.collection.get_spectrum(dither, detector, object_id)

        plot = PlotWindow(f'dither-{dither}, detector-{detector}, object-{object_id}')

        plot.axis.imshow(spec.science)

        sub_window = self.mdi.addSubWindow(plot)

        ##########

        # TODO: set color of the MDI area with self.mdi.setBackground()

        inner_layout.addWidget(self.toolbar)
        inner_layout.addWidget(self.mdi)

        self.setLayout(outer_layout)

    @property
    def object_id(self):
        return self._object_id

    @property
    def dither(self):
        return self._dither

    @property
    def detector(self):
        return self._detector

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