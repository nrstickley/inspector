import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QMdiArea, QAction, QToolBar

from plot_window import PlotWindow
from detector_selector import MultiDitherDetectorSelector


class AnalysisTab(QWidget):
    def __init__(self, inspector, dither, detector, object_id, *args):
        super().__init__(*args)

        self._inspector = inspector
        self._dither = dither
        self._detector = detector
        self._object_id = object_id
        self.contents = list()
        self.setMouseTracking(True)

        # TODO: put 4 of these into a widget with Vbox layout

        selector_area = MultiDitherDetectorSelector()

        self.mdi = QMdiArea(self)
        self.mdi.setContentsMargins(0, 0, 0, 0)

        h_layout = QGridLayout()
        h_layout.setSpacing(0)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addWidget(selector_area, 0, 0)
        h_layout.setAlignment(selector_area, Qt.AlignTop)
        h_layout.addWidget(self.mdi, 0, 1)

        h_layout.setColumnStretch(0, 0)
        h_layout.setColumnStretch(1, 10)

        self.toolbar = self.init_toolbar()

        v_layout = QVBoxLayout()
        v_layout.setSpacing(0)

        v_layout.addWidget(self.toolbar)

        v_layout.addItem(h_layout)

        self.setLayout(v_layout)

        ##########

        #spec = inspector.collection.get_spectrum(dither, detector, object_id)

        #plot = PlotWindow(f'dither-{dither}, detector-{detector}, object-{object_id}')

        #plot.axis.imshow(spec.science)

        #sub_window = self.mdi.addSubWindow(plot)

        ##########

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

        #show_table = QAction(QIcon('./table_icon.png'), '', toolbar)
        #show_table.setToolTip('show the table of contaminants')
        #show_table.triggered.connect(self.show_info)

        #toolbar.addAction(show_table)

        return toolbar

    def make_plot(self):
        print('this is where I would make a plot')

    def show_info(self):
        print('this is where I would show info')