

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtWidgets import (QGraphicsScene, QWidget, QComboBox, QHBoxLayout, QLabel,
                             QLineEdit, QVBoxLayout, QSpacerItem, QSizePolicy)

from specbox import Rect
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

        pixmap = utils.np_to_pixmap(data, data.max())

        self.scene.clear()
        self.scene.addPixmap(pixmap)

        self.boxes_visible = False

        self.inspector.rename_tab(self)

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

    def show_boxes_in_view(self):
        self.show_bounding_boxes(self.current_dither, self.current_detector)
        self.boxes_visible = True

    def remove_boxes_in_view(self):
        for item in self.scene.items():
            if isinstance(item, Rect) and not item.pinned:
                self.scene.removeItem(item)
        self.boxes_visible = False

    def remove_pinned_boxes(self):
        for item in self.scene.items():
            if isinstance(item, Rect) and item.pinned:
                self.scene.removeItem(item)

        if len(self.scene.items()) == 0:
            self.boxes_visible = False

    def n_pinned_boxes(self):
        n = 0
        for item in self.scene.items():
            if isinstance(item, Rect) and item.pinned:
                n += 1

        return n

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
                    return None

            # this point is only reached if the specified spectrum is not already pinned. Pin the spec
            spec_box, pos = self.show_bounding_box(self.current_dither, self.current_detector, object_id)
            spec_box.pin(pos)

        return spec

    def unselect_spectrum_by_id(self, object_id):
        for item in self.get_pinned_spectra():
            if item.spec.id == object_id:
                self.scene.removeItem(item)

    def get_pinned_spectra(self):
        items = []
        for item in self.scene.items():
            if isinstance(item, Rect) and item.pinned:
                items.append(item)
        return items
