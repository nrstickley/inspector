#! /usr/bin/env python3

"""
General plan:

 * figure out how to forward right-click events to graphics items.
 * add an option along the lines of 'open in analysis tab'
 * make an analysis area class that can be inserted into new tabs
    - figure out how to embed MatPlotLib plots into widgets
    - make customizable plots that can be added to the analysis widget
 * put table of contaminants into a table widget
    - the table entries should be clickable  (or right clickable), so you can view the contaminants
    - in another tab or in the main view
 * add the ability to load location tables
 * add the ability to to compute wavelengths
 * add the ability to to convert to physical flux values
 * Implement the info window for viewing x-y coords, RA, DEC, wavelengths of a specific spectrum, raw values of pixels,
   flux values of pixels
 """

import sys
import os
import json

from astropy.io import fits

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QImage, QPixmap, QColor, QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
                             QGridLayout, QWidget, QTabWidget, QMenu, QFileDialog,
                             QAction, QComboBox, QHBoxLayout, QGroupBox, QLabel,
                             QGraphicsItem, QLineEdit, QTableWidget, QTableWidgetItem,
                             QGraphicsPixmapItem, QMessageBox, QVBoxLayout, QSpacerItem,
                             QSizePolicy)

from reader import DecontaminatedSpectraCollection
from specbox import Rect
from detector_view import View
import utils


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


class ObjectSelectionArea(QHBoxLayout):

    def __init__(self, *args):
        super().__init__(*args)

        self.setContentsMargins(5, 9, 0, 9)

        self.setSpacing(10)

        selector_layout = QHBoxLayout()

        selector_layout.setContentsMargins(0, 0, 0, 0)

        selector_layout.setSpacing(10)

        # set up the dither selector and label

        dither_label, self.dither_selector = self.make_selector('dither')

        detector_label, self.detector_selector = self.make_selector('detector')

        selector_layout.addSpacerItem(QSpacerItem(130, 10, QSizePolicy.Maximum, QSizePolicy.Maximum))
        selector_layout.addWidget(dither_label, Qt.AlignCenter)
        selector_layout.addWidget(self.dither_selector)
        selector_layout.addSpacerItem(QSpacerItem(75, 10, QSizePolicy.Maximum, QSizePolicy.Maximum))
        selector_layout.addWidget(detector_label, Qt.AlignCenter)
        selector_layout.addWidget(self.detector_selector)

        self.searchbox = QLineEdit()

        self.insertLayout(0, selector_layout)
        self.searchbox.setMaximumWidth(250)
        self.searchbox.setMinimumWidth(125)
        self.searchbox.setPlaceholderText('Search by ID')

        self.addStretch(1)

        self.addWidget(self.searchbox, Qt.AlignRight)

        print('SelectionArea is created')

    @staticmethod
    def make_selector(name: 'str'):
        label = QLabel(f"{name}:")

        label.setAlignment(Qt.AlignRight)

        selector_box = QComboBox()
        selector_box.setStatusTip(f'Select a {name} to display')
        selector_box.setObjectName(name)
        selector_box.setMinimumWidth(50)
        selector_box.setMaximumWidth(100)
        selector_box.setEnabled(False)

        return label, selector_box


class ViewTab(QWidget):

    def __init__(self, inspector, *args):

        super().__init__(*args)

        self.inspector = inspector

        self.current_detector = 1
        self.current_dither = 1
        self.boxes_visible = False

        self._layout = QVBoxLayout()

        self._layout.setContentsMargins(5, 0, 5, 5)

        self._layout.setSpacing(0)

        self.selection_area = ObjectSelectionArea()

        self._layout.insertLayout(0, self.selection_area)

        # create and add the view area

        self.view = View(self)

        self.scene = QGraphicsScene()

        self.view.setScene(self.scene)

        self._layout.addWidget(self.view)

        self.setLayout(self._layout)

        print('ViewTab is created')

    def init_view(self):
        # display dither 1, detector 1 in single view

        dithers = list(self.inspector.exposures.keys())

        self.current_dither = dithers[0]

        self.update_view()

        self.selection_area.dither_selector.setEnabled(True)
        self.selection_area.detector_selector.setEnabled(True)

        for i, dither in enumerate(dithers):
            self.selection_area.dither_selector.addItem(str(dither), dither)

        self.selection_area.dither_selector.activated[int].connect(self.change_dither)

        for detector in range(1, 17):
            self.selection_area.detector_selector.addItem(str(detector), detector)

        self.selection_area.detector_selector.activated[int].connect(self.change_detector)

        self.boxes_visible = False

    def change_dither(self, dither_index):
        self.current_dither = self.selection_area.dither_selector.itemData(dither_index)
        self.update_view()

    def change_detector(self, detector_index):
        self.current_detector = self.selection_area.detector_selector.itemData(detector_index)
        self.update_view()

    def update_view(self):
        data = self.inspector.exposures[self.current_dither][self.current_detector].data

        pixmap = utils.np_to_pixmap(data, data.max())

        self.scene.clear()
        self.scene.addPixmap(pixmap)

        self.boxes_visible = False

    def show_bounding_box(self, dither, detector, object_id):
        spec = self.inspector.collection.get_spectrum(dither, detector, object_id)
        return self.draw_spec_box(spec)

    def draw_spec_box(self, spec):
        if spec is not None:
            left = spec.x_offset
            height, width = spec.science.shape
            top = spec.y_offset

            rect = Rect(left, top, width, height)

            rect.spec = spec

            self.scene.addItem(rect)

            return rect, QPointF(left, top)

    def show_bounding_boxes(self, dither, detector):
        for spec in self.inspector.collection.get_spectra(dither, detector):
            self.draw_spec_box(spec)

    def toggle_bounding_boxes(self):
        if not self.boxes_visible:
            self.show_boxes_in_view()
        else:
            self.remove_boxes_in_view()

    def show_boxes_in_view(self):
        self.show_bounding_boxes(self.current_dither, self.current_detector)
        self.boxes_visible = True

    def remove_boxes_in_view(self):
        for item in self.scene.items():
            if isinstance(item, Rect) and not item.pinned:
                self.scene.removeItem(item)
        self.boxes_visible = False

    def active_detector_has_spectral_data(self):
        if self.inspector.exposures is None or self.inspector.collection is None:
            return False

        dith = self.current_dither
        det = self.current_detector

        return dith in self.inspector.collection.get_dithers() and det in self.inspector.collection.get_detectors(dith)

    def select_spectrum(self):
        object_id = self.selection_area.searchbox.text()

        if self.inspector.collection is None or self.inspector.exposures is None:
            return

        spec = self.inspector.collection.get_spectrum(self.current_dither, self.current_detector, object_id)

        if spec is None:
            self.selection_area.searchbox.setText('Not found')
        else:
            spec_box, pos = self.show_bounding_box(self.current_dither, self.current_detector, object_id)
            spec_box.pin(pos)


class Inspector:
    def __init__(self, app):

        self.app = app

        self.collection = None  # this will hold the DecontaminatedSpectraCollection
        self.exposures = None  # this will hold the detectors as a nested map {dither: {detector: pixels}}

        self.main, self.tabs = self.init_main()

        self.view_tab = ViewTab(self)

        self.tabs.addTab(self.view_tab, "Detector view")

        self.tabs.setTabShape(QTabWidget.Triangular)

        self.tabs.setTabsClosable(True)

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
                self.view_tab.selection_area.searchbox.returnPressed.connect(inspector.view_tab.select_spectrum)

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

        self.view_tab.init_view()

    def show_info(self):
        m = QMessageBox(0, 'Info Window Placeholder',
                        "This is where we can show things like x and y pixel coordinates, RA, DEC, "
                        "additional info about the exposures and detectors, etc.",
                        QMessageBox.NoButton)
        m.setWindowFlag(Qt.Window, True)
        m.exec()
        print('showed message')

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
