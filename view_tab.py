import os
import inspect

import numpy as np

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QBrush, QColor, QImage, QPixmap
from PyQt5.QtWidgets import (QGraphicsScene, QWidget, QComboBox, QHBoxLayout, QLabel,
                             QLineEdit, QVBoxLayout, QSpacerItem, QSizePolicy)

from specbox import SpecBox
from detector_view import View
import utils


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

        data_label, self.data_selector = self.make_selector('data')
        self.data_selector.setMinimumWidth(175)

        selector_layout.addSpacerItem(QSpacerItem(130, 10, QSizePolicy.Maximum, QSizePolicy.Maximum))
        selector_layout.addWidget(dither_label, Qt.AlignCenter)
        selector_layout.addWidget(self.dither_selector)
        selector_layout.addSpacerItem(QSpacerItem(55, 10, QSizePolicy.Maximum, QSizePolicy.Maximum))
        selector_layout.addWidget(detector_label, Qt.AlignCenter)
        selector_layout.addWidget(self.detector_selector)
        selector_layout.addSpacerItem(QSpacerItem(55, 10, QSizePolicy.Maximum, QSizePolicy.Maximum))
        selector_layout.addWidget(data_label, Qt.AlignCenter)
        selector_layout.addWidget(self.data_selector)

        self.searchbox = QLineEdit()

        self.insertLayout(0, selector_layout)
        self.searchbox.setMaximumWidth(250)
        self.searchbox.setMinimumWidth(125)
        self.searchbox.setPlaceholderText('Search by ID')

        self.addStretch(1)

        self.addWidget(self.searchbox, Qt.AlignRight)

    @staticmethod
    def make_selector(name: 'str'):
        label = QLabel(f"{name}:")

        label.setAlignment(Qt.AlignRight)

        selector_box = QComboBox()
        selector_box.setStatusTip(f'Select a {name} to display')
        selector_box.setObjectName(name)
        selector_box.setMinimumWidth(85)
        selector_box.setMaximumWidth(85)
        selector_box.setEnabled(False)

        return label, selector_box


class ViewTab(QWidget):

    LAYERS = ('original', 'model', 'decontaminated residual', 'model residual')

    def __init__(self, inspector, *args):

        super().__init__(*args)

        self.inspector = inspector

        self.current_detector = 1
        self.current_dither = 1
        self.boxes_visible = False

        self.pixmap_item = {}  # {dither: {detector: {layer: pixmap}}

        for dither in (1, 2, 3, 4):
            self.pixmap_item[dither] = {}
            for detector in range(1, 17):
                self.pixmap_item[dither][detector] = {layer :None for layer in self.LAYERS}

        self._layout = QVBoxLayout()

        self._layout.setContentsMargins(5, 0, 5, 5)

        self._layout.setSpacing(0)

        self.selection_area = ObjectSelectionArea()

        self._layout.insertLayout(0, self.selection_area)

        # create and add the view area

        self.view = View(self)

        self.scene = QGraphicsScene()

        self._background = QBrush(QColor('#56595e'))

        executable_directory = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))

        self._blank_image = QPixmap(QImage(executable_directory + '/load-exposure-message.svg'))

        self.scene.setBackgroundBrush(self._background)

        self._blank_pixmap = self.scene.addPixmap(self._blank_image)

        self.view.setScene(self.scene)

        self._layout.addWidget(self.view)

        self.setLayout(self._layout)

        self.current_layer = 'original'

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

        for layer in self.LAYERS:
            self.selection_area.data_selector.addItem(layer)

        self.selection_area.data_selector.activated[str].connect(self.change_layer)

        self.boxes_visible = False

    def change_dither(self, dither_index):
        self.current_dither = self.selection_area.dither_selector.itemData(dither_index)
        if dither_index != self.selection_area.dither_selector.currentIndex():
            self.selection_area.dither_selector.blockSignals(True)
            self.selection_area.dither_selector.setCurrentIndex(dither_index)
            self.selection_area.dither_selector.blockSignals(False)
        self.update_view()

    def change_detector(self, detector_index):
        self.current_detector = self.selection_area.detector_selector.itemData(detector_index)
        if detector_index != self.selection_area.detector_selector.currentIndex():
            self.selection_area.detector_selector.blockSignals(True)
            self.selection_area.detector_selector.setCurrentIndex(detector_index)
            self.selection_area.detector_selector.blockSignals(False)
        self.update_view()

    def update_view(self):
        if self.current_dither is None or self.current_detector is None:
            return

        data = self.inspector.exposures[self.current_dither][self.current_detector].data

        pixmap, _ = utils.np_to_pixmap(data, data.max())

        self.scene.clear()
        self.current_layer = 'original'
        original_index = self.selection_area.data_selector.findText(self.current_layer)
        self.selection_area.data_selector.setCurrentIndex(original_index)
        self.pixmap_item[self.current_dither][self.current_detector][self.current_layer] = self.scene.addPixmap(pixmap)
        self.pixmap_item[self.current_dither][self.current_detector][self.current_layer].setZValue(-1.0)

        self.boxes_visible = False

        self.inspector.rename_tab(self)

        self.inspector.detector_info_window.update_detector(self.current_dither, self.current_detector)

        if self.inspector.collection is not None:
            collection = self.inspector.collection
            dither = self.current_dither
            detector = self.current_detector
            if dither in collection.get_dithers() and detector in collection.get_detectors(dither):
                self.selection_area.data_selector.setEnabled(True)
        else:
            self.selection_area.data_selector.setDisabled(True)

    def show_bounding_box(self, dither, detector, object_id):
        spec = self.inspector.collection.get_spectrum(dither, detector, object_id)
        return self.draw_spec_box(spec)

    def draw_spec_box(self, spec):
        if spec is not None:
            left = spec.x_offset
            height, width = spec.science.shape
            top = spec.y_offset

            rect = SpecBox(left, top, width, height)

            rect.spec = spec

            model = self.inspector.collection.get_model(self.current_dither,
                                                        self.current_detector,
                                                        spec.id, order=1)

            if model is not None:
                rect.model = model.pixels

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

    def toggle_decontaminated(self):
        if not self.decontamination_visible:
            self.show_decontaminated_in_view()
        else:
            self.remove_decontaminated_in_view()

    def show_boxes_in_view(self):
        self.show_bounding_boxes(self.current_dither, self.current_detector)
        self.boxes_visible = True

    def remove_boxes_in_view(self):
        for item in self.scene.items():
            if isinstance(item, SpecBox) and not item.pinned:
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

        spec = self.select_spectrum_by_id(object_id)

        if spec is None:
            self.selection_area.searchbox.setText('Not found')

    def select_spectrum_by_id(self, object_id):

        if self.inspector.collection is None or self.inspector.exposures is None:
            return None

        spec = self.inspector.collection.get_spectrum(self.current_dither, self.current_detector, object_id)

        if spec is not None:
            # make sure that the spec is not already pinned

            for pinned_item in self.get_pinned_spectra():
                if pinned_item.spec.id == object_id:
                    pinned_item.grabKeyboard()
                    return None

            # this point is only reached if the specified spectrum is not already pinned. Pin the spec
            spec_box, pos = self.show_bounding_box(self.current_dither, self.current_detector, object_id)
            spec_box.pin(pos)
            spec_box.grabKeyboard()

        return spec

    def unselect_spectrum_by_id(self, object_id):
        for item in self.get_pinned_spectra():
            if item.spec.id == object_id:
                self.scene.removeItem(item)

    def get_pinned_spectra(self):
        items = []
        for item in self.scene.items():
            if isinstance(item, SpecBox) and item.pinned:
                items.append(item)
        return items

    def get_model_residual_image(self):
        """removes all model contaminants from the detector and returns the model residual"""
        data = self.inspector.exposures[self.current_dither][self.current_detector].data
        return data - self.get_model_image()

    def get_model_image(self):
        data = self.inspector.exposures[self.current_dither][self.current_detector].data
        sim = np.zeros_like(data)

        for object_id in self.inspector.collection.get_object_ids(self.current_dither, self.current_detector):
            model = self.inspector.collection.get_model(self.current_dither, self.current_detector, object_id, 1)
            if model is not None:
                height, width = model.pixels.shape
                region = (slice(model.y_offset, model.y_offset + height), slice(model.x_offset, model.x_offset + width))
                sim[region] += model.pixels
            else:
                # there is no model because this was not contaminated. The spectrum itself is essentially the model.
                model = self.inspector.collection.get_spectrum(self.current_dither, self.current_detector, object_id)
                height, width = model.science.shape
                region = (slice(model.y_offset, model.y_offset + height), slice(model.x_offset, model.x_offset + width))
                sim[region] += model.science

        return sim

    def get_residual_image(self):
        data = self.inspector.exposures[self.current_dither][self.current_detector].data
        decon = np.zeros_like(data)

        for object_id in self.inspector.collection.get_object_ids(self.current_dither, self.current_detector):
            spec = self.inspector.collection.get_spectrum(self.current_dither, self.current_detector, object_id)
            height, width = spec.science.shape
            region = (slice(spec.y_offset, spec.y_offset + height), slice(spec.x_offset, spec.x_offset + width))
            decon[region] += spec.science

        return data - decon

    def get_pixmap(self, image_data):
        data = self.inspector.exposures[self.current_dither][self.current_detector].data
        _, pixmap = utils.np_to_pixmap(data, data.max(), data.min(), image_data)
        return pixmap

    def remove_pinned_boxes(self):
        for item in self.scene.items():
            if isinstance(item, SpecBox) and item.pinned:
                self.scene.removeItem(item)

        if len(self.scene.items()) == 0:
            self.boxes_visible = False

    def n_pinned_boxes(self):
        n = 0
        for item in self.scene.items():
            if isinstance(item, SpecBox) and item.pinned:
                n += 1

        return n

    def change_layer(self, layer):
        if self.current_layer == layer:
            return

        print('switching to', layer)

        if layer not in self.LAYERS:
            return

        self.scene.removeItem(self.pixmap_item[self.current_dither][self.current_detector][self.current_layer])

        if self.pixmap_item[self.current_dither][self.current_detector][layer] is None:
            if layer == 'original':
                image_data = self.inspector.exposures[self.current_dither][self.current_detector].data
                pixmap = utils.np_to_pixmap(image_data, image_data.max())
            elif layer == 'model residual':
                image_data = self.get_model_residual_image()
                pixmap = self.get_pixmap(image_data)
            elif layer == 'decontaminated residual':
                image_data = self.get_residual_image()
                pixmap = self.get_pixmap(image_data)
            elif layer == 'model':
                print('switching to the model layer')
                image_data = self.get_model_image()
                pixmap = self.get_pixmap(image_data)

            pixmap_item = self.scene.addPixmap(pixmap)
            pixmap_item.setZValue(-1.0)
            self.pixmap_item[self.current_dither][self.current_detector][layer] = pixmap_item
        else:
            self.scene.addItem(self.pixmap_item[self.current_dither][self.current_detector][layer])

        self.current_layer = layer




