#! /usr/bin/env python3.6

"""
General plan:

 * show zeroth order contaminant boxes.

 * make customizable plots that can be added to the analysis tab?
 * add the ability to to compute wavelengths
 * add the ability to to convert to physical flux values
 * in blank tabs, show a note about using the file menu or Ctrl+N to load exposures.

 In the analysis tab:

 * load grism sensitivity / calibration vector (1 for each dither)
 * load load j and h sensitivities
 * show all 2D spectra for the object
 * show all collapsed 1D spectra for the object
 * show wavelength - flux plots for the 4 dithers (along with the J and H band magnitudes)
     - this should show original, decontaminated, and model (if there is a model)
 """

import sys
import os
import json

import numpy as np
from astropy.io import fits

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QFileDialog, QAction, QMessageBox)

from view_tab import ViewTab
from analysis_tab import AnalysisTab
from info_window import DetectorInfoWindow

from reader import DecontaminatedSpectraCollection, LocationTable, NISP_DETECTOR_MAP


class Inspector:
    def __init__(self, app):

        self.app = app

        self.collection = None  # this will hold the DecontaminatedSpectraCollection
        self.exposures = None  # this will hold the detectors as a nested map {dither: {detector: pixels}}
        self.spectra = None  # this will hold a map connecting object IDs with spectra, in the format:
                             # {object_id: {dither: {detector: spectrum}}

        self.location_tables = None  # this will hold a reader.LocationTable object

        # This will hold a map: {dither: sensitivity_table} where sensitivity_table is a
        # NumPy array with two rows: wavelength and sensitivity, which is used to convert
        # from pixel value to erg/s/cm^2/AA
        self.sensitivities = {i: None for i in (1, 2, 3, 4)}

        self.main, self.tabs = self.init_main()

        self.view_tab = [ViewTab(self)]

        self.tabs.addTab(self.view_tab[0], "view 0")

        self.analysis_tab = []

        self.tabs.setTabShape(QTabWidget.Triangular)

        self.tabs.setTabsClosable(True)

        self.tabs.tabCloseRequested.connect(self.close_tab)

        self.tabs.tabBarDoubleClicked.connect(self.new_view_tab)

        self.tabs.currentChanged.connect(self._change_detector)

        self.tabs.setMovable(True)

        self.menu = self.init_menu()

        self._session = {}

        self._loading_session = False

        self._detector_info_window = DetectorInfoWindow(self)

    def init_menu(self):
        """Creates the main menu."""
        menu = self.main.menuBar()

        self.init_file_menu(menu)

        self.init_windows_menu(menu)

        return menu

    def init_file_menu(self, main_menu):
        file_menu = main_menu.addMenu('File')

        load_nisp = QAction('Load Exposures', main_menu)
        load_nisp.setShortcut('Ctrl+E')
        load_nisp.setStatusTip('Load one or more NISP exposures, listed in a JSON file.')
        load_nisp.triggered.connect(self.load_exposures)

        load_decon = QAction('Load Spectra', main_menu)
        load_decon.setShortcut('Ctrl+D')
        load_decon.setStatusTip('Load one or more decontaminated spectra collections, listed in a JSON file.')
        load_decon.triggered.connect(self.load_spectra)

        load_loctab = QAction('Load Location Tables', main_menu)
        load_loctab.setShortcut('Ctrl+L')
        load_loctab.setToolTip('Load spectral metadata from the location tables.')
        load_loctab.triggered.connect(self.load_location_tables)

        load_sensitivities = QAction('Load Grism Sensitivities', main_menu)
        load_sensitivities.setShortcut('Ctrl+G')
        load_sensitivities.setToolTip('Load flux calibration curves for each grism / dither')
        load_sensitivities.triggered.connect(self.load_sensitivities)

        save_session = QAction('Save Session As...', main_menu)
        save_session.setShortcut('Ctrl+S')
        save_session.setStatusTip('Saves session information, regarding the currently loaded files.')
        save_session.triggered.connect(self.save_session)

        load_session = QAction('Load Session', main_menu)
        load_session.setShortcut('Ctrl+O')
        load_session.setStatusTip('Loads all files from a previous session.')
        load_session.triggered.connect(self.load_session)

        exit_app = QAction('Exit', main_menu)
        exit_app.setStatusTip('Close the application.')
        exit_app.triggered.connect(self.exit)

        file_menu.addAction(load_nisp)

        file_menu.addAction(load_decon)

        file_menu.addAction(load_loctab)

        file_menu.addAction(load_sensitivities)

        file_menu.addSeparator()

        file_menu.addAction(save_session)

        file_menu.addAction(load_session)

        file_menu.addSeparator()

        file_menu.addAction(exit_app)

        return file_menu

    def init_windows_menu(self, main_menu):
        windows_menu = main_menu.addMenu('Windows')

        show_info = QAction('Show Info Window', main_menu)
        show_info.setShortcut('Ctrl+I')
        show_info.triggered.connect(self.show_info)

        windows_menu.addAction(show_info)

        return windows_menu

    @property
    def detector_info_window(self):
        return self._detector_info_window

    def load_spectra(self):
        if not self._loading_session:
            filename, _ = QFileDialog.getOpenFileName(self.main, caption='Open Decontaminated Spectra', filter='*.json')
        else:
            filename = self._session['spectra']
            if filename == '':
                return

        if os.path.isfile(filename):
            print(f"Loading {filename}.")
            self.app.setOverrideCursor(Qt.WaitCursor)
            try:
                self.collection = DecontaminatedSpectraCollection(filename, self.main)
            except:
                self.collection = None
                message = QMessageBox(self, 'Error', 'Could not load the spectra. Verify that the file format is correct.')
                message.exec()
            self.app.restoreOverrideCursor()

            # connect the search box
            if self.collection is not None:
                for view_tab in self.view_tab:
                    view_tab.selection_area.searchbox.returnPressed.connect(view_tab.select_spectrum)

        if self.collection is None:
            m = QMessageBox(self, 'Error', 'Encountered error while loading the spectra. Make sure the correct paths '
                                           'were specified.')
            m.exec()
            return

        self.organize_spectra_by_object_id()

        self._session['spectra'] = filename

    def load_exposures(self):
        """Loads Background-subtracted NISP Exposures."""
        if not self._loading_session:
            nisp_exposures_json_file, _ = QFileDialog.getOpenFileName(self.main,
                                                                      caption='Open NISP Exposures',
                                                                      filter='*.json')
        else:
            nisp_exposures_json_file = self._session['exposures']
            if nisp_exposures_json_file == '':
                return

        if not os.path.isfile(nisp_exposures_json_file):
            return

        with open(nisp_exposures_json_file) as f:
            nisp_exposure_filenames = json.load(f)

        self.exposures = {}  # {dither: {detector: image}}

        fits_magic = 'SIMPLE  =                    T'

        for exposure_name in nisp_exposure_filenames:
            full_path = os.path.join(os.path.dirname(nisp_exposures_json_file), 'data', exposure_name)
            print(f"loading {full_path}")
            try:
                f = open(full_path)
                magic = f.read(30)
            except:
                magic = ''
            if magic != fits_magic:
                message = QMessageBox(self, 'File Format Error', f'{exposure_name} is not a FITS file.')
                message.exec()
                self.exposures = None
                f.close()
                return
            if not f.closed:
                f.close()
            exposure = fits.open(full_path, memmap=True)
            dither = exposure[0].header['DITHSEQ']
            self.exposures[dither] = {}
            for detector in NISP_DETECTOR_MAP:
                self.exposures[dither][detector] = exposure[f'DET{NISP_DETECTOR_MAP[detector]}.SCI']

        for view_tab in self.view_tab:
            view_tab.init_view()

        self._session['exposures'] = nisp_exposures_json_file

    def load_location_tables(self):
        if not self._loading_session:
            filename, _ = QFileDialog.getOpenFileName(self.main, caption='Load Decontaminated Spectra', filter='*.json')
        else:
            filename = self._session['location_tables']
            if filename == '':
                return

        if os.path.isfile(filename):
            print(f"Loading {filename}.")
            self.app.setOverrideCursor(Qt.WaitCursor)
            try:
                self.location_tables = LocationTable(filename, self.main)
            except:
                self.collection = None
                message = QMessageBox(0, 'Error', 'Could not load the location tables. '
                                                  'Verify that the file format is correct.')
                message.exec()
            self.app.restoreOverrideCursor()

            self._session['location_tables'] = filename

    def load_sensitivities(self):
        if not self._loading_session:
            filename, _ = QFileDialog.getOpenFileName(self.main, caption='Load grism sensitivities', filter='*.json')
        else:
            filename = self._session['grism_sensitivities']
            if filename == '':
                return

        if os.path.isfile(filename):
            # populate self.sensitivities

            with open(filename) as f:
                sensitivities = json.load(f)
                if not isinstance(sensitivities, dict):
                    raise TypeError('')
                    message = QMessageBox(self, 'Error',
                                          'The JSON file specifying the sensitivity curves must contain a dictionary.')
                    message.exec()
                    return
                dithers = (1, 2, 3, 4)

                for d in dithers:
                    if str(d) in sensitivities:
                        sens_file = sensitivities[str(d)]
                        full_path = os.path.join(os.path.dirname(filename), 'data', sens_file)
                        self.sensitivities[d] = np.loadtxt(full_path)
                    else:
                        self.sensitivities[d] = None

            self._session['grism_sensitivities'] = filename

    def organize_spectra_by_object_id(self):
        """
        Constructs a map in the format {object_id: {dither: {detector: spectrum}} from self.collection
        """
        self.spectra = {}
        for dither in self.collection.get_dithers():
            for detector in self.collection.get_detectors(dither):
                for object_id in self.collection.get_object_ids(dither, detector):
                    if object_id not in self.spectra:
                        self.spectra[object_id] = {dither: {}}
                    if dither not in self.spectra[object_id]:
                        self.spectra[object_id][dither] = {}
                    if detector not in self.spectra[object_id][dither]:
                        self.spectra[object_id][dither][detector] = None
                    spec = self.collection.get_spectrum(dither, detector, object_id)
                    self.spectra[object_id][dither][detector] = spec

    def get_object_dithers(self, object_id):
        return list(self.spectra[object_id].keys())

    def get_object_detectors(self, dither, object_id):
        return list(self.spectra[object_id][dither].keys())

    def show_info(self):
        if self.exposures is not None:
            self._detector_info_window.show()

    def new_view_tab(self, dither=None, detector=None):
        new_view_tab = ViewTab(inspector)
        self.view_tab.append(new_view_tab)
        index = self.tabs.addTab(new_view_tab, f'view {len(self.view_tab) - 1}')
        self.tabs.setCurrentIndex(index)

        if self.exposures is not None:
            new_view_tab.init_view()
            new_view_tab.selection_area.searchbox.returnPressed.connect(new_view_tab.select_spectrum)

        if dither is not None and detector is not None:
            new_view_tab.change_dither(dither - 1)
            new_view_tab.change_detector(detector - 1)
            self.rename_tab(new_view_tab)

    def new_analysis_tab(self, dither, detector, object_id):
        tab = AnalysisTab(self, dither, detector, object_id)
        self.analysis_tab.append(tab)
        index = self.tabs.addTab(tab, f'Object {object_id}')
        self.tabs.setCurrentIndex(index)

    def rename_tab(self, view_tab):
        # find the index of the view_tab and then use that index to change the name of the tab
        tab_index = self.tabs.indexOf(view_tab)
        self.tabs.setTabText(tab_index, f'dither-{view_tab.current_dither} det-{view_tab.current_detector}')

    def close_tab(self, tab_index):
        item = self.tabs.widget(tab_index)
        if item in self.view_tab:
            self.view_tab.remove(item)
        self.tabs.removeTab(tab_index)

        if self.tabs.count() == 0:
            self.exit()

    def _change_detector(self, tab_index):
        item = self.tabs.widget(tab_index)
        if item in self.view_tab:
            item.current_detector
            item.current_dither
            self.detector_info_window.update_detector(item.current_dither, item.current_detector)

    def save_session(self):
        filename, _ = QFileDialog.getSaveFileName(self.main, caption='Save Session', filter='*.sir')

        fields = ['exposures',
                  'spectra',
                  'location_tables',
                  'grism_sensitivities',
                  'j_sens',
                  'h_sens']

        for field in fields:
            if field not in self._session:
                self._session[field] = ''

        if (len(filename) > 4 and filename[-4:] != '.sir') or 0 < len(filename) < 4:
            filename += '.sir'
        elif len(filename) == 0:
            filename -= 'untitled_session.sir'

        with open(filename, 'w') as f:
            json.dump(self._session, f)

    def load_session(self):
        filename, _ = QFileDialog.getOpenFileName(self.main, caption='Save Session', filter='*.sir')

        if filename == '':
            return

        with open(filename) as f:
            self._session = json.load(f)

        self._loading_session = True

        self.load_exposures()
        self.load_spectra()
        self.load_location_tables()
        self.load_sensitivities()

        self._loading_session = False

    def exit(self):
        print('shutting down')
        self.main.close()
        self.app.exit(0)

    @staticmethod
    def init_main():
        """Creates the main application window."""
        main = QMainWindow()
        main.setWindowTitle('Decontamination InSpector')
        main.resize(1200, 950)

        tabs = QTabWidget()

        main.setCentralWidget(tabs)

        main.setWindowIcon(QIcon('./Euclid.png'))

        main.setContentsMargins(0, 5, 0, 0)

        main.showMaximized()

        return main, tabs


if __name__ == '__main__':

    app = QApplication(sys.argv)

    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    inspector = Inspector(app)

    app.exec()

    app.closeAllWindows()

    app.exit(0)
