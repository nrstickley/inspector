#! /usr/bin/env python3.6

"""
General plan:

 * make an analysis area class that can be inserted into new tabs
    - example showing how to embed MatPlotLib into Qt Widget:
          https://matplotlib.org/gallery/user_interfaces/embedding_in_qt_sgskip.html
    - make customizable plots that can be added to the analysis widget
 * add the ability to load location tables
 * add the ability to to compute wavelengths
 * add the ability to to convert to physical flux values
 * in blank tabs, show a note about using the file menu or Ctrl+N to load exposures.

 New classes to implement:

 * AnalysisTab (and probably a few associated classes)
 * ContaminantTable for displaying the list of contaminants
 * InfoWindow for viewing x-y coords, RA, DEC, wavelengths of a specific spectrum, raw values of pixels,
   flux values of pixels
 * Plotter (probably)
 """

import sys
import os
import json

from astropy.io import fits

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QFileDialog, QAction, QMessageBox)

from view_tab import ViewTab
from analysis_tab import AnalysisTab

from reader import DecontaminatedSpectraCollection


NISP_DETECTOR_MAP = {1: '11',
                     2: '21',
                     3: '31',
                     4: '41',
                     5: '12',
                     6: '22',
                     7: '32',
                     8: '42',
                     9: '13',
                     10: '23',
                     11: '33',
                     12: '43',
                     13: '14',
                     14: '24',
                     15: '34',
                     16: '44'}

DETECTOR_ID = {val: key for key, val in NISP_DETECTOR_MAP.items()}


class Inspector:
    def __init__(self, app):

        self.app = app

        self.collection = None  # this will hold the DecontaminatedSpectraCollection
        self.exposures = None  # this will hold the detectors as a nested map {dither: {detector: pixels}}
        self.spectra = None # this will hold a map connecting object IDs with spectra, in the format:
                            # {object_id: {dither: {detector: spectrum}}

        self.main, self.tabs = self.init_main()

        self.view_tab = [ViewTab(self)]

        self.tabs.addTab(self.view_tab[0], "view 0")

        # self.analysis_tab = [AnalysisTab(self, 'test-object')]

        # self.tabs.addTab(self.analysis_tab[0], 'MatPlotLib test')

        self.tabs.setTabShape(QTabWidget.Triangular)

        self.tabs.setTabsClosable(True)

        self.tabs.tabCloseRequested.connect(self.close_tab)

        self.tabs.tabBarDoubleClicked.connect(self.new_view_tab)

        self.tabs.setMovable(True)

        self.menu = self.init_menu()

    def init_menu(self):
        """Creates the main menu."""
        menu = self.main.menuBar()

        self.init_file_menu(menu)

        self.init_windows_menu(menu)

        return menu

    def init_file_menu(self, main_menu):
        file_menu = main_menu.addMenu('File')

        load_nisp = QAction('Load Exposures', main_menu)
        load_nisp.setShortcut('Ctrl+N')
        load_nisp.setStatusTip('Load one or more NISP exposures, listed in a JSON file.')
        load_nisp.triggered.connect(self.load_exposures)

        file_menu.addAction(load_nisp)

        load_decon = QAction('Load Spectra', main_menu)
        load_decon.setShortcut('Ctrl+S')
        load_decon.setStatusTip('Load one or more decontaminated spectra collections, listed in a JSON file.')
        load_decon.triggered.connect(self.load_spectra)

        file_menu.addAction(load_decon)

        exit_app = QAction('Exit', main_menu)
        exit_app.setStatusTip('Close the application.')
        exit_app.triggered.connect(self.exit)

        file_menu.addAction(exit_app)

        return file_menu

    def init_windows_menu(self, main_menu):
        windows_menu = main_menu.addMenu('Windows')

        show_info = QAction('Show Info Window', main_menu)
        show_info.setShortcut('Ctrl+I')
        show_info.triggered.connect(self.show_info)

        windows_menu.addAction(show_info)

        return windows_menu

    def load_spectra(self):
        filename, _ = QFileDialog.getOpenFileName(self.main, caption='Open Decontaminated Spectra', filter='*.json')

        if os.path.isfile(filename):
            print(f"Loading {filename}.")
            self.app.setOverrideCursor(Qt.WaitCursor)
            try:
                self.collection = DecontaminatedSpectraCollection(filename, self.main)
            except:
                self.collection = None
                message = QMessageBox(0, 'Error', 'Could not load the spectra. Verify that the file format is correct.')
                message.exec()
            self.app.restoreOverrideCursor()

            # connect the search box
            if self.collection is not None:
                for view_tab in self.view_tab:
                    view_tab.selection_area.searchbox.returnPressed.connect(view_tab.select_spectrum)

        self.organize_spectra_by_object_id()

    def load_exposures(self):
        """Loads Background-subtracted NISP Exposures."""

        nisp_exposures_json_file, _ = QFileDialog.getOpenFileName(self.main,
                                                                  caption='Open NISP Exposures',
                                                                  filter='*.json')

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
                message = QMessageBox(0, 'File Format Error', f'{exposure_name} is not a FITS file.')
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
        m = QMessageBox(0, 'Info Window Placeholder',
                        "This is where we can show things like x and y pixel coordinates, RA, DEC, "
                        "additional info about the exposures and detectors, etc.",
                        QMessageBox.NoButton)
        m.setWindowFlag(Qt.Window, True)
        m.exec()

    def new_view_tab(self, dither=None, detector=None):
        new_view_tab = ViewTab(inspector)
        self.view_tab.append(new_view_tab)
        self.tabs.addTab(new_view_tab, f'view {len(self.view_tab) - 1}')
        if self.exposures is not None:
            new_view_tab.init_view()
            new_view_tab.selection_area.searchbox.returnPressed.connect(new_view_tab.select_spectrum)

        if dither is not None and detector is not None:
            new_view_tab.change_dither(dither - 1)
            new_view_tab.change_detector(detector - 1)
            self.rename_tab(new_view_tab)

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

    inspector = Inspector(app)

    app.exec()
