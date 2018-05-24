#! /usr/bin/env python3

import sys
import os
import json

import numpy as np
from astropy.io import fits
import matplotlib as mpl

mpl.use('Qt5Agg')

import matplotlib.pyplot as plt

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QImage, QPixmap, QColor, QPen, QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
                             QGridLayout, QWidget, QGraphicsRectItem, QTabWidget,
                             QMenu, QFileDialog, QAction, QComboBox, QHBoxLayout,
                             QGroupBox, QLabel, QGraphicsTextItem, QGraphicsItem,
                             QLineEdit)

from reader import DecontaminatedSpectraCollection


plt.ion()

red_pen = QPen(QColor('red'))
green_pen = QPen(QColor('green'))


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

DETECTOR_ID = {val:key for key, val in NISP_DETECTOR_MAP.items()}


def to_bytes(im, maxval=None):
    """
    Scales the input image to fit the dynamic range between 0 and 255, inclusive. Then returns
    the array as an array of bytes (a string).
    """
    if maxval is None:
        maxval = im.max()

    data = (im - im.min()) / (maxval - im.min())
    counts, bins = np.histogram(data.flatten(), bins=300)
    scale_factor = 0.017 / bins[1 + counts.argmax()]
    scaled = 2 * 350 * scale_factor * (np.arctan(1.1e6 * data.astype(np.float32) / maxval) / np.pi)
    scaled -= np.percentile(scaled, 0.05)
    counts, bins = np.histogram(scaled.flatten(), bins=300, range=(0, 300))
    scale_factor2 = 44.0 / bins[1 + counts.argmax()]
    scaled *= scale_factor2
    #plt.hist(scaled.flatten(), bins=128, log=True, histtype='step')
    clipped = np.clip(scaled, 0, 255)
    return clipped.astype(np.uint8).flatten().tobytes()


def np_to_pixmap(array, maxval):
    height, width = array.shape
    image_bytes = to_bytes(array, maxval)
    image = QImage(image_bytes, width, height, width, QImage.Format_Grayscale8)
    return QPixmap(image)


class View(QGraphicsView):

    def __init__(self, main):
        super().__init__()
        self._main = main
        #self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setDragMode(QGraphicsView.RubberBandDrag)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        show_hide = 'Hide' if self._main.boxes else 'Show'
        show_bounding = menu.addAction(show_hide + " bounding boxes", self._main.toggle_bounding_boxes)

        if not self._main.active_detector_has_spectral_data():
            show_bounding.setDisabled(True)

        menu.exec(event.globalPos())


class Rect(QGraphicsRectItem):

    inactive_opacity = 0.25  # the opacity of rectangles that are not in focus

    def __init__(self, *args):
        rect = QRectF(*args)
        super().__init__(rect)
        self.setOpacity(Rect.inactive_opacity)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setPen(green_pen)

        self.pinned = False
        self.label = None
        self._spec = None

    @property
    def spec(self):
        return self._spec

    @spec.setter
    def spec(self, spec):
        self._spec = spec

    def hoverEnterEvent(self, event):
        self.setPen(red_pen)
        self.setOpacity(1.0)

    def hoverLeaveEvent(self, event):
        if not self.pinned:
            self.setPen(green_pen)
            self.setOpacity(Rect.inactive_opacity)

    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent'):
        keys = event.modifiers()
        
        if keys & Qt.CTRL:
            self.grabKeyboard()
        else:
            self.handle_pinning(event)
            self.grabKeyboard()

    def handle_pinning(self, event):
        if self.pinned:  # it's already pinned; unpin it
            self.setPen(green_pen)
            if self.label is not None:
                self.scene().removeItem(self.label)
                self.label = None
            self.pinned = False
        else:  # it's not pinned; pin it
            self.setPen(red_pen)

            self.label = QGraphicsTextItem(f"{self._spec.id}", parent=self)
            self.label.setPos(event.scenePos())
            self.label.setDefaultTextColor(QColor('red'))
            self.pinned = True

    def keyPressEvent(self, event):
        print('a key was pressed')
        print(event.key())
        if event.key() == Qt.Key_Up or  event.key() == Qt.Key_Down:
            self.plot_culumn_sums()

        if event.key() == Qt.Key_Right or event.key() == Qt.Key_Left:
            plt.close()
            plt.plot(self._spec.science.sum(axis=1))

        if event.key() == Qt.Key_S:
            plt.close()
            plt.imshow(self._spec.science)

        if event.key() == Qt.Key_V:
            plt.close()
            plt.imshow(self._spec.variance)

        if event.key() == Qt.Key_C:
            plt.close()
            plt.imshow(self._spec.contamination)

        # todo: also show original image and the residual. raise main window to top or make it active at least (better).
        # add ability to add multiple plots to the same canvas

        if event.key() == Qt.Key_L:
            print("Contaminants:")
            print(self._spec.contaminants)

        self.window().activateWindow()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        show_spectrum_info = menu.addAction("inspect in 'Spectrum View'", self._main.toggle_bounding_boxes)

        plot_columns = QAction('Plot column sums', menu)

        plot_columns = QAction('Load Exposures', menu)
        plot_columns.setShortcut(Qt.Key_Up)
        plot_columns.setStatusTip('Plot the sums of the colums of pixels in the 2D spectrum.')
        plot_columns.triggered.connect(self.plot_culumn_sums)

        menu.addAction(plot_columns)

        menu.exec(event.globalPos())

    def plot_culumn_sums(self):
        plt.close()
        plt.plot(self._spec.science.sum(axis=0))
        # TODO: consider plotting both the decontaminated sums, the original, and the contaminants, labeled appropriately.
        #plt.draw()


class Inspector:
    def __init__(self, app):

        self.app = app

        self.tabs = QTabWidget()

        self.single_layout = QGridLayout()

        self.single_layout.setContentsMargins(5, 10, 5, 5)

        self.multi_layout = QGridLayout()

        self.main = self.init_main()

        self.menu = self.init_menu()

        self.collection = None  # this will hold the DecontaminatedSpectraCollection
        self.exposures = None   # this will hold the detectors as a nested map {dither: {detector: pixels}}

        self.single_current_detector = 1
        self.single_current_dither = 1

        # create the dither selection drop-down menu

        self.single_dither_box = QComboBox()
        self.single_detector_box = QComboBox()

        self.make_detector_selection_box()

        # create and add the main / single view area

        self.single_view = View(self)

        self.scene = QGraphicsScene()

        self.single_view.setScene(self.scene)

        self.single_layout.addWidget(self.single_view)

        self.boxes = False


    def init_main(self):
        """Creates the main application window."""
        main = QMainWindow()
        main.setWindowTitle('Decontamination Inspector')
        main.resize(1200, 950)

        multi = QWidget()

        single = QWidget()

        single.setLayout(self.single_layout)

        multi.setLayout(self.multi_layout)

        self.tabs.addTab(single, "Detector view")

        self.tabs.addTab(multi, "Spectrum view")

        main.setCentralWidget(self.tabs)

        main.setWindowIcon(QIcon('./Euclid.png'))

        main.showMaximized()

        #main.showFullScreen()

        return main

    def init_menu(self):
        """Creates the main menu."""
        menu = self.main.menuBar()

        file_menu = menu.addMenu('File')

        load_nisp = QAction('Load Exposures', menu)
        load_nisp.setShortcut('Ctrl+N')
        load_nisp.setStatusTip('Load one or more NISP exposures, listed in a JSON file.')
        load_nisp.triggered.connect(self.load_exposures)

        file_menu.addAction(load_nisp)

        load_decon = QAction('Load Spectra', menu)
        load_decon.setShortcut('Ctrl+S')
        load_decon.setStatusTip('Load one or more decontaminated spectra collections, listed in a JSON file.')
        load_decon.triggered.connect(self.load_spectra)

        file_menu.addAction(load_decon)

        exit_app = QAction('Exit', menu)
        exit_app.setStatusTip('Close the application.')
        exit_app.triggered.connect(self.exit)

        file_menu.addAction(exit_app)

        return menu

    def make_detector_selection_box(self):
        top_region = QGroupBox('')

        top_region.setFlat(True)

        top_layout = QHBoxLayout()

        top_region.setLayout(top_layout)

        selector_box = QGroupBox("Detector Selection")

        selector_box.setMaximumWidth(400)

        top_layout.addWidget(selector_box, Qt.AlignLeft)

        searchbox = QLineEdit()
        searchbox.setMaximumWidth(250)
        searchbox.setMaximumWidth(200)
        searchbox.setPlaceholderText('Search by ID')
        # TODO set trigger ; return selects the specified object in the current view; error feedback if not present.
        # Make this a member of the class, so it is self.searchbox and connect QLineEdit::returnPressed() with a function that accepts a string as a parameter
        # self.searchbox.returnPressed.connect(self.bla)

        top_layout.addStretch(1)

        top_layout.addWidget(searchbox, Qt.AlignRight)

        selector_layout = QHBoxLayout()

        selector_box.setLayout(selector_layout)

        dither_label = QLabel("dither:")

        dither_label.setAlignment(Qt.AlignRight)

        detector_label = QLabel('detector:')

        detector_label.setAlignment(Qt.AlignRight)

        self.single_dither_box = QComboBox()
        self.single_dither_box.setStatusTip('Select a dither to display')
        self.single_dither_box.setObjectName('dither')
        self.single_dither_box.setCurrentText('dither')
        self.single_dither_box.setMinimumWidth(50)
        self.single_dither_box.setMaximumWidth(100)
        self.single_dither_box.setEnabled(False)

        selector_layout.addWidget(dither_label)
        selector_layout.addWidget(self.single_dither_box)

        # create and add the exposure drop-down menu

        self.single_detector_box.setStatusTip('Select a detector to display')
        self.single_detector_box.setObjectName('detector')
        self.single_detector_box.setCurrentText('detector')
        self.single_detector_box.setMinimumWidth(50)
        self.single_detector_box.setMaximumWidth(100)
        self.single_detector_box.setEnabled(False)

        selector_layout.addWidget(detector_label)
        selector_layout.addWidget(self.single_detector_box)

        self.single_layout.addWidget(top_region)

    def load_spectra(self):
        filename, _ = QFileDialog.getOpenFileName(self.main, caption='Open Decontaminated Spectra', filter='*.json')

        if os.path.isfile(filename):
            print(f"Loading {filename}.")
            self.app.setOverrideCursor(Qt.WaitCursor)
            self.collection = DecontaminatedSpectraCollection(filename, self.main)
            print(f"Finished loading {filename}.")
            self.app.restoreOverrideCursor()

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

        for exposure_name in nisp_exposure_filenames:
            full_path = os.path.join('data', exposure_name)
            print(f"loading {full_path}")
            exposure = fits.open(full_path, memmap=True)
            dither = exposure[0].header['DITHSEQ']
            self.exposures[dither] = {}
            for detector in NISP_DETECTOR_MAP:
                self.exposures[dither][detector] = exposure[f'DET{NISP_DETECTOR_MAP[detector]}.SCI']

        self.update_nisp_data_in_gui()

    def update_nisp_data_in_gui(self):
        print('update drop-down menus')

        # display dither 1, detector 1 in single view

        dithers = list(self.exposures.keys())

        self.single_current_dither = dithers[0]

        self.update_single()

        self.single_dither_box.setEnabled(True)
        self.single_detector_box.setEnabled(True)

        for i, dither in enumerate(dithers):
            self.single_dither_box.addItem(str(dither), dither)

        self.single_dither_box.activated[int].connect(self.update_single_dither)

        for detector in range(1, 17):
            self.single_detector_box.addItem(str(detector), detector)

        self.single_detector_box.activated[int].connect(self.update_single_detector)

        self.boxes = False

        print('updated')

    def update_single_dither(self, dither_index):
        self.single_current_dither = self.single_dither_box.itemData(dither_index)
        self.update_single()

    def update_single_detector(self, detector_index):
        self.single_current_detector = self.single_detector_box.itemData(detector_index)
        self.update_single()

    def update_single(self):
        data = self.exposures[self.single_current_dither][self.single_current_detector].data

        pixmap = np_to_pixmap(data, data.max())

        self.scene.clear()
        self.scene.addPixmap(pixmap)

    def exit(self):
        print('shutting down')
        self.main.close()
        self.app.exit(0)

    def show_bounding_box(self, dither, detector, object_id):
        spec = self.collection.get_spectrum(dither, detector, object_id)
        self.draw_spec_box(spec)

    def draw_spec_box(self, spec):
        if spec is not None:
            left = spec.x_offset
            height, width = spec.science.shape
            top = spec.y_offset

            rect = Rect(left, top, width, height)

            rect.spec = spec

            self.scene.addItem(rect)

    def show_bounding_boxes(self, dither, detector):
        for spec in self.collection.get_spectra(dither, detector):
            self.draw_spec_box(spec)

    def toggle_bounding_boxes(self):
        if self.boxes:
            self.show_boxes_in_view()
        else:
            self.remove_boxes_in_view()

    def show_boxes_in_view(self):
        self.show_bounding_boxes(self.single_current_dither, self.single_current_detector)
        self.boxes = True

    def remove_boxes_in_view(self):
        for item in self.scene.items():
            if isinstance(item, Rect) and not item.pinned:
                self.scene.removeItem(item)
        self.boxes = False

    def active_detector_has_spectral_data(self):
        if self.exposures is None or self.collection is None:
            return False

        dith = self.single_current_dither
        det = self.single_current_detector

        return dith in self.collection.get_dithers() and det in self.collection.get_detectors(dith)


if __name__ == '__main__':

    app = QApplication(sys.argv)

    inspector = Inspector(app)

    app.exec()

# https://stackoverflow.com/questions/7140994/overlaping-qgraphicsitem-s-hover-events?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa

# for context menu, we need to override a method of QGraphicsView, so we need to create a subclass of QGraphicsView
# https://stackoverflow.com/questions/10766775/showing-a-popup-menu-on-qgraphicsscene-click-or-right-click?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
# signals and slots:
# http://pyqt.sourceforge.net/Docs/PyQt5/signals_slots.html