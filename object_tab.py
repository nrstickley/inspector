import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QMdiArea, QGroupBox, QPushButton, QRadioButton,
                             QCheckBox, QMessageBox)

from plot_window import PlotWindow
from info_window import ObjectInfoWindow
from view_tab import ViewTab
from detector_selector import MultiDitherDetectorSelector
import utils


# FIXME: these should be provided as inputs

J_WAV = 13697.01  # in angstroms
H_WAV = 17761.52  # in angstroms


class PlotSelector(QWidget):
    """
    A widget for selecting the type of plot that will be generated. This also contains the Plot button, which triggers
    the plotting.
    """
    X_PIX = 0
    X_WAV = 1

    Y_DN = 0
    Y_FLUX = 1

    S_ORIG = 1
    S_DECON = 2
    S_CONTAM = 4
    S_MODEL = 8

    def __init__(self, object_tab, *args):
        super().__init__(*args)

        self.object_tab = object_tab

        # data series selection

        data_series_group = QGroupBox('Data Series', self)
        data_series_group.setAlignment(Qt.AlignCenter)
        data_series_group.setMaximumWidth(550)
        data_series_group.setMinimumWidth(300)

        original_check = QCheckBox('Original', data_series_group)
        original_check.setChecked(True)

        decontaminated_check = QCheckBox('Decontaminated', data_series_group)
        decontaminated_check.setChecked(True)

        contamination_check = QCheckBox('Contamination', data_series_group)
        contamination_check.setChecked(True)

        model_check = QCheckBox('Model', data_series_group)

        data_series_group.setLayout(QGridLayout())
        data_series_group.layout().addWidget(original_check, 0, 0)
        data_series_group.layout().addWidget(decontaminated_check, 0, 1)
        data_series_group.layout().addWidget(contamination_check, 1, 0)
        data_series_group.layout().addWidget(model_check, 1, 1)

        self._original = original_check
        self._decon = decontaminated_check
        self._contam = contamination_check
        self._model = model_check

        # y-axis type selection

        y_axis_type = QGroupBox('y-axis type', self)
        y_axis_type.setAlignment(Qt.AlignCenter)
        y_axis_type.setMaximumWidth(300)
        y_axis_type.setMinimumWidth(200)
        data_number_radio = QRadioButton('Image Units', y_axis_type)
        calibrated_flux_radio = QRadioButton('Calibrated Flux', y_axis_type)
        if self.object_tab.inspector.sensitivities[self.object_tab.dither] is None:
            calibrated_flux_radio.setDisabled(True)
            data_number_radio.setChecked(True)
        else:
            calibrated_flux_radio.setChecked(True)
        y_axis_type.setLayout(QVBoxLayout())
        y_axis_type.layout().addWidget(data_number_radio)
        y_axis_type.layout().addWidget(calibrated_flux_radio)

        self._data_number = data_number_radio
        self._flux = calibrated_flux_radio

        # x-axis type selection

        x_axis_type = QGroupBox('x-axis type', self)
        x_axis_type.setAlignment(Qt.AlignCenter)
        x_axis_type.setMaximumWidth(300)
        x_axis_type.setMinimumWidth(200)
        wavelength_radio = QRadioButton('Wavelength', x_axis_type)
        wavelength_radio.setChecked(True)
        pixel_number_radio = QRadioButton('Pixel number', x_axis_type)
        x_axis_type.setLayout(QVBoxLayout())
        x_axis_type.layout().addWidget(pixel_number_radio)
        x_axis_type.layout().addWidget(wavelength_radio)

        self._wavelength = wavelength_radio
        self._pixel_num = pixel_number_radio

        # buttons

        detector_button = QPushButton('Show Detectors', self)
        detector_button.setMaximumWidth(128)
        detector_button.pressed.connect(self.object_tab.open_detectors)
        detector_button.setDisabled(True)
        plot_button = QPushButton('Make Plot(s)', self)
        plot_button.setMaximumWidth(128)
        plot_button.setMinimumWidth(100)
        plot_button.pressed.connect(self.object_tab.make_plots)
        plot_button.setDisabled(True)

        self.detector_button = detector_button
        self.plot_button = plot_button

        buttons = QVBoxLayout()
        buttons.addSpacing(23)
        buttons.addWidget(detector_button)
        buttons.addWidget(plot_button)

        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(10, 0, 10, 10)

        layout.addWidget(data_series_group, 0, 0)
        layout.addWidget(y_axis_type, 0, 1)
        layout.addWidget(x_axis_type, 0, 2)
        layout.addLayout(buttons, 0, 3)

        self.setContentsMargins(8, 0, 8, 8)

        self.setLayout(layout)

    @property
    def x_type(self):
        if self._wavelength.isChecked():
            return self.X_WAV
        else:
            return self.X_PIX

    @property
    def y_type(self):
        if self._data_number.isChecked():
            return self.Y_DN
        else:
            return self.Y_FLUX

    @property
    def series(self):
        result = 0
        if self._original.isChecked():
            result |= self.S_ORIG

        if self._contam.isChecked():
            result |= self.S_CONTAM

        if self._decon.isChecked():
            result |= self.S_DECON

        if self._model.isChecked():
            result |= self.S_MODEL

        return result


class SpecPlot:

    def __init__(self, inspector, plot_selector, detector_selector):
        self._inspector = inspector
        self._plot_selector = plot_selector
        self._detector_selector = detector_selector
        self._detectors = None
        self._object_id = None
        self._x_type = None
        self._y_type = None
        self._data_series = None
        self._windows = []

    @property
    def windows(self):
        return self._windows

    def make_plots(self, object_id):
        self._object_id = object_id
        self._detectors = self._detector_selector.selected_detectors()
        self._x_type = self._plot_selector.x_type
        self._y_type = self._plot_selector.y_type
        self._data_series = self._plot_selector.series

        for dither, detectors in self._detectors.items():
            if detectors is not None:
                for detector in detectors:
                    plot = self._plot(dither, detector)
                    self._windows.append(plot)

    def _calibrate_spectrum(self, dither, spec_1d, wavelengths):
        """
        Applies the calibration correction to convert `spec_1d` from detector units to erg/s/cm^2/Angstrom
        """
        if self._inspector.sensitivities[dither] is None:
            m = QMessageBox(self._inspector, 'You need to load the grism sensitivity curves first.')
            m.exec()
            return

        exposure_time = self._inspector.exposures[dither][1].header['EXPTIME']

        dl = np.fabs(np.diff(wavelengths))

        denom = np.append(dl, dl[0]) * exposure_time

        sensitivity_wav, sensitivity_value = self._inspector.sensitivities[dither]

        inverse_sensitivity = utils.div0(1.0, sensitivity_value)

        return utils.interp_multiply(wavelengths, spec_1d / denom, sensitivity_wav, inverse_sensitivity)

    def _plot(self, dither, detector):
        if self._data_series == 0:
            return

        plot = PlotWindow(f"object {self._object_id} detector: {dither}.{detector}")

        spec = self._inspector.collection.get_spectrum(dither, detector, self._object_id)
        dispersion_axis = spec.solution.dispersion_orientation()

        plot_flux = self._y_type == PlotSelector.Y_FLUX
        plot_wavelength = self._x_type == PlotSelector.X_WAV

        if dispersion_axis == 0:
            pixels = spec.x_offset + np.arange(0, spec.science.shape[1])
            wavelengths = spec.solution.compute_wavelength(pixels)
        else:
            pixels = spec.y_offset + np.arange(0, spec.science.shape[0])
            wavelengths = spec.solution.compute_wavelength(pixels)

        min_wav, max_wav = 12400, 18600

        short_wav_end = np.argmin(np.fabs(wavelengths - min_wav))
        long_wav_end = np.argmin(np.fabs(wavelengths - max_wav))
        i_min = min(short_wav_end, long_wav_end)
        i_max = max(short_wav_end, long_wav_end)

        x_values = wavelengths[i_min: i_max] if plot_wavelength else pixels[i_min: i_max]

        # determine and set the limits of the x-axis

        if plot_wavelength and plot_flux:
            plot.axis.set_xlim((min_wav, max_wav))
        elif plot_flux and not plot_wavelength:
            short_wav_end = np.argmin(np.fabs(wavelengths - min_wav))
            long_wav_end = np.argmin(np.fabs(wavelengths - max_wav))
            x_min = min(pixels[short_wav_end], pixels[long_wav_end])
            x_max = max(pixels[short_wav_end], pixels[long_wav_end])
            plot.axis.set_xlim((x_min, x_max))

        if self._data_series & PlotSelector.S_ORIG == PlotSelector.S_ORIG:
            if plot_flux:
                uncalibrated = np.sum(spec.science + spec.contamination, axis=dispersion_axis)
                y_values = self._calibrate_spectrum(dither, uncalibrated, wavelengths)
            else:
                y_values = np.sum(spec.science + spec.contamination, axis=dispersion_axis)

            plot.axis.plot(x_values, y_values[i_min: i_max], label='original spectrum', color='k', linewidth=0.5,
                           alpha=0.7)

        if self._data_series & PlotSelector.S_CONTAM == PlotSelector.S_CONTAM:
            if plot_flux:
                y_values = self._calibrate_spectrum(dither, spec.contamination.sum(dispersion_axis), wavelengths)
            else:
                y_values = spec.contamination.sum(dispersion_axis)

            plot.axis.plot(x_values, y_values[i_min: i_max], label='contamination', color='g', linewidth=0.75,
                           alpha=0.8)

        if self._data_series & PlotSelector.S_DECON == PlotSelector.S_DECON:
            if plot_flux:
                y_values = self._calibrate_spectrum(dither, spec.science.sum(dispersion_axis), wavelengths)
            else:
                y_values = spec.science.sum(dispersion_axis)

            plot.axis.plot(x_values, y_values[i_min: i_max], label='decontaminated spectrum', color='b', linewidth=0.9)

        if self._data_series & PlotSelector.S_MODEL == PlotSelector.S_MODEL:
            model = self._inspector.collection.get_model(dither, detector, self._object_id, order=1)
            if model is not None:
                if plot_flux:
                    y_values = self._calibrate_spectrum(dither, model.pixels.sum(dispersion_axis), wavelengths)
                else:
                    y_values = model.pixels.sum(dispersion_axis)

                plot.axis.plot(x_values, y_values[i_min: i_max], label='model spectrum', color='r', linewidth=0.9,
                               alpha=0.9)

        # plot the J and H band fluxes if the plot shows flux vs wavelength

        if plot_wavelength and plot_flux:
            info = self._inspector.location_tables.get_info(self._object_id)
            j_microjansky = utils.mag_to_fnu(info.jmag, zero_point=22)
            h_microjansky = utils.mag_to_fnu(info.hmag, zero_point=22)
            j_fnu = utils.mjy_to_angstrom(j_microjansky, J_WAV)
            h_fnu = utils.mjy_to_angstrom(h_microjansky, H_WAV)
            plot.axis.scatter(J_WAV, j_fnu, color='r', label='J and H band fluxes')
            plot.axis.scatter(H_WAV, h_fnu, color='r')

        x_label = r'Wavelength $\rm (\AA)$' if self._x_type == PlotSelector.X_WAV else 'Pixel'
        y_label = r'Flux ($\rm erg/s/cm^2/\AA$)' if self._y_type == PlotSelector.Y_FLUX else 'Electrons / second'

        plot.axis.set_xlabel(x_label)
        plot.axis.set_ylabel(y_label)
        plot.axis.legend()

        # set the descriptor; a string in the format: id.dither.detector.data_series.y_type.x_type
        plot.descriptor = f'{self._object_id}.{dither}.{detector}.{self._data_series}.{self._y_type}.{self._x_type}'

        return plot


class ObjectTab(QWidget):
    """
    This class constructs the entire contents of the Object tab.
    """
    def __init__(self, inspector, dither, detector, object_id, *args):
        super().__init__(*args)

        self._inspector = inspector
        self._dither = dither  # remove
        self._detector = detector  # remove
        self._object_id = object_id
        self.contents = list()
        self.setMouseTracking(True)

        self.plot_selector = PlotSelector(self)

        detectors = self.determine_relevant_detectors(object_id)

        selector_area = MultiDitherDetectorSelector(detectors)
        selector_area.updated.connect(self.update_plot_button)

        self.mdi = QMdiArea(self)
        self.mdi.setContentsMargins(0, 0, 0, 0)
        self.mdi.setBackground(QBrush(QColor('#56595e')))

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
        self.setContentsMargins(0, 0, 0, 0)
        self._spec_plots = None

        self._plot_descriptors = set()

        self._info_window = None

    @property
    def object_id(self):
        return self._object_id

    @property
    def dither(self):
        return self._dither

    @property
    def detector(self):
        return self._detector

    @property
    def inspector(self):
        return self._inspector

    def make_plots(self):
        self._spec_plots = SpecPlot(self._inspector, self.plot_selector, self.detector_selector)
        self._spec_plots.make_plots(self._object_id)
        for window in self._spec_plots.windows:
            if window.descriptor not in self._plot_descriptors:
                self.mdi.addSubWindow(window)
                self._plot_descriptors.add(window.descriptor)
                window.closing.connect(self.handle_closed_subwindow)
                window.activateWindow()
                window.show()

    def show_info(self):
        if self._inspector.location_tables is not None:
            info = self._inspector.location_tables.get_info(self._object_id)
            info_window = ObjectInfoWindow(info, self._inspector)
            self.mdi.addSubWindow(info_window)
            info_window.activateWindow()
            info_window.show()
            self._info_window = info_window
        else:
            m = QMessageBox(0, 'Missing Data',
                            'Location tables containing the requested information must be loaded before showing info.')
            m.exec()

    def determine_relevant_detectors(self, object_id):
        """
        Returns the detectors in which the spectra of the object can be found, in the format {dither: [detectors]}
        """
        detectors = {}

        for dither in self._inspector.spectra[object_id]:
            detectors[dither] = list(self._inspector.spectra[object_id][dither].keys())

        for d in (1, 2, 3, 4):
            if d not in detectors:
                detectors[d] = []

        return detectors

    def update_plot_button(self):
        selected = list(self.detector_selector.selected_detectors().values())

        if all(item is None for item in selected):
            self.plot_selector.plot_button.setDisabled(True)
            self.plot_selector.detector_button.setDisabled(True)
        else:
            self.plot_selector.detector_button.setEnabled(True)
            self.plot_selector.plot_button.setEnabled(True)

    def handle_closed_subwindow(self, descriptor):
        self._plot_descriptors.remove(descriptor)

    def open_detectors(self):

        selected_detectors = self.detector_selector.selected_detectors()

        inspector = self._inspector

        # make a list of all open detectors (detectors currently being viewed in tabs)

        open_detectors = []

        for tab_index in range(inspector.tabs.count()):
            tab = inspector.tabs.widget(tab_index)
            if isinstance(tab, ViewTab):
                open_detectors.append((tab.current_dither, tab.current_detector))

        # open new tabs, where necessary

        for dither in selected_detectors:
            if selected_detectors[dither] is not None:
                for detector in selected_detectors[dither]:
                    if (dither, detector) not in open_detectors:
                        inspector.new_view_tab(dither, detector)

            # pin the object in all tabs:

            for tab_index in range(inspector.tabs.count()):
                tab = inspector.tabs.widget(tab_index)
                if isinstance(tab, ViewTab):
                    tab.select_spectrum_by_id(self._object_id)
