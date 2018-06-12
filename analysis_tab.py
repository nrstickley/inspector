import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QMdiArea, QAction, QGroupBox, QPushButton, QRadioButton,
                             QCheckBox)

from plot_window import PlotWindow
from detector_selector import MultiDitherDetectorSelector


class PlotSelector(QWidget):
    def __init__(self, analysis_tab, *args):
        super().__init__(*args)

        self.analysis_tab = analysis_tab

        data_series_group = QGroupBox('Data Series', self)
        data_series_group.setLayout(QVBoxLayout())  # should be a 2 x 2 grid layout
        original_check = QCheckBox('Original', data_series_group)
        decontaminated_check = QCheckBox('Decontaminated', data_series_group)
        contamination_check = QCheckBox('Contamination', data_series_group)
        model_check = QCheckBox('Model', data_series_group)
        data_series_group.layout().addWidget(original_check)
        data_series_group.layout().addWidget(decontaminated_check)
        data_series_group.layout().addWidget(contamination_check)
        data_series_group.layout().addWidget(model_check)

        y_axis_type = QGroupBox('y axis type', self)  # data number vs calibrated flux (radiobuttons)

        x_axis_type = QGroupBox('x axis type', self)  # pixel widths vs wavelength (radiobuttons)

        plot_botton = QPushButton('Make Plot(s)', self) 

        layout = QGridLayout()

        layout.addWidget(data_series_group, 0, 0)
        layout.addWidget(y_axis_type, 0, 1)
        layout.addWidget(x_axis_type, 0, 2)
        layout.addWidget(plot_botton, 0, 3)

        self.setLayout(layout)


class AnalysisTab(QWidget):
    def __init__(self, inspector, dither, detector, object_id, *args):
        super().__init__(*args)

        self._inspector = inspector
        self._dither = dither
        self._detector = detector
        self._object_id = object_id
        self.contents = list()
        self.setMouseTracking(True)

        self.plot_selector = PlotSelector(self)

        detectors = self.determine_relevant_detectors(object_id)

        selector_area = MultiDitherDetectorSelector(detectors)

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

        self.detector_selector = selector_area

        v_layout = QVBoxLayout()
        v_layout.setSpacing(0)

        v_layout.addWidget(self.plot_selector)

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

    def make_plot(self):
        print('this is where I would make a plot')

    def show_info(self):
        print('this is where I would show info')

    def print_selected_detectors(self):
        selected = self.detector_selector.selected_detectors()
        for dither, detectors in selected.items():
            print(f'for detector {dither}, the selected detectors are: {detectors}')

    def determine_relevant_detectors(self, object_id):
        """
        returns the detectors in which the spectra of the object can be found, in the format {dither: [detectors]}
        """
        detectors = {}

        for dither in self._inspector.spectra[object_id]:
            detectors[dither] = list(self._inspector.spectra[object_id][dither].keys())

        for d in (1, 2, 3, 4):
            if d not in detectors:
                detectors[d] = []

        return detectors

