
from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QPen, QFont, QTransform
from PyQt5.QtWidgets import (QWidget, QGraphicsView, QGraphicsWidget, QGraphicsScene, QGraphicsGridLayout,
                             QGraphicsTextItem, QGraphicsRectItem, QGraphicsDropShadowEffect, QVBoxLayout,
                             QGraphicsLayoutItem, QLabel, QGridLayout)


flip_vertical = QTransform(1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0)


def box_id(row, column):
    return row * 4 + column + 1


class DetectorBoxLayout(QGraphicsLayoutItem):
    def __init__(self, box, *args):
        super().__init__(*args)
        self.box = box
        self.setGraphicsItem(box)

    def sizeHint(self, which, constraint):
        return self.box.size

    def setGeometry(self, rect):
        self.box.setRect(rect)
        self.box.place_label(rect)


class DetectorBox(QGraphicsRectItem):
    """
    Represents a single detector box in the MultiDetectorSelector widget.
    """
    length = 32
    disabled_brush = QBrush(QColor(210, 210, 210, 200))
    enabled_brush = QBrush(QColor(120, 123, 135, 255))
    hovered_brush = QBrush(QColor(156, 186, 252, 255))
    selected_brush = QBrush(QColor(80, 110, 206, 255))
    invisible_pen = QPen(QColor(255, 255, 255, 0))
    red_pen = QPen(QColor('red'))

    def __init__(self, row, column, enabled, *args):

        self._detector_id = box_id(row, column)

        self._enabled = enabled

        self._selected = False
        self._rect = QRectF(*args)
        self._rect.setHeight(self.length)
        self._rect.setWidth(self.length)

        super().__init__(self._rect)

        self.setPen(self.invisible_pen)

        self.setAcceptHoverEvents(True)

        if enabled:
            self.setBrush(self.enabled_brush)
        else:
            self.setBrush(self.disabled_brush)

        # states: enabled, disabled, hovered, selected
        self._label = QGraphicsTextItem(str(self.detector_id), self)

        self._label.setTransform(flip_vertical, True)

        self._label.setFont(QFont('Arial', 14))

        self._label.setDefaultTextColor(QColor('white'))

        self._detector_selector = None

    @property
    def detector_id(self):
        return self._detector_id

    @property
    def size(self):
        return self._rect.size()

    @property
    def selected(self):
        return self._selected

    def set_parent_selector(self, parent):
        self._detector_selector = parent

    def hoverEnterEvent(self, event):
        if self._enabled:
            self.setBrush(self.hovered_brush)

    def hoverLeaveEvent(self, event):
        if self._enabled:
            if self._selected:
                self.setBrush(self.selected_brush)
            else:
                self.setBrush(self.enabled_brush)
        else:
            self.setBrush(self.disabled_brush)

    def mousePressEvent(self, event):
        if self._enabled:
            if event.button() == Qt.LeftButton:
                if not self._selected:
                    self._selected = True
                    self.setBrush(self.selected_brush)
                    self.setPen(self.red_pen)
                else:
                    self._selected = False
                    self.setBrush(self.enabled_brush)
                    self.setPen(self.invisible_pen)

            self._detector_selector.selection_changed()

    def place_label(self, rect):
        # FIXMe: placement should be done differently, so that flipping the text leaves it in the same place.
        x_center = 0.5 * (rect.left() + rect.right()) - 0.5 * self._label.boundingRect().width()
        y_center = 0.5 * (rect.bottom() + rect.top()) - 0.5 * self._label.boundingRect().height() + self.length
        self._label.setPos(x_center, y_center)


class MultiDetectorSelector(QWidget):
    """
    Constructs a detector selector consisting of 4 x 4 squares, numbered to be consistent with the SIR numbering scheme.
    This allows the user to specify which detectors they are interested in viewing / inspecting.
    """

    updated = pyqtSignal()

    def __init__(self, dither, detectors, *args):
        super().__init__(*args)

        self._enabled_detectors = detectors

        self._boxes = {}  # this will be of the form {detector_number: DetectorBox}

        self.gv_layout = QGraphicsGridLayout()

        self.gv_layout.setSpacing(0)

        min_length = DetectorBox.length * 4 + 6

        self._min_length = min_length

        self._dither = dither

        self.gv_layout.setMinimumSize(min_length, min_length)
        self.gv_layout.setMaximumSize(min_length, min_length)
        self.gv_layout.setContentsMargins(0, 0, 0, 0)

        self.setMinimumWidth(min_length)
        self.setMinimumHeight(min_length)

        self.setMaximumWidth(min_length + 20)
        self.setMaximumHeight(min_length + 20)

        self._init_boxes()

        gv_widget = QGraphicsWidget()

        gv_widget.setLayout(self.gv_layout)

        gv_widget.setContentsMargins(0, 0, 0, 0)

        scene = QGraphicsScene()

        scene.addItem(gv_widget)

        scene.setSceneRect(0,0, min_length, min_length)

        view = QGraphicsView()

        view.setMouseTracking(True)

        view.setViewportMargins(0, 0, 0, 0)

        view.setGeometry(0, 0, min_length, min_length)

        view.setStyleSheet("border: 0px; margin: 0px; padding: 0px;")

        view.setScene(scene)

        view.setTransform(flip_vertical, True)

        layout = QVBoxLayout()

        layout.addWidget(view)

        self.setLayout(layout)

    @property
    def dither_number(self):
        return self._dither

    @property
    def min_length(self):
        return self._min_length

    def _init_boxes(self):
        for row in range(4):
            for column in range(4):
                detector_id = box_id(row, column)
                enabled = detector_id in self._enabled_detectors
                box = DetectorBox(row, column, enabled)
                box.set_parent_selector(self)
                self._boxes[detector_id] = box
                box_layout = DetectorBoxLayout(box)
                self.gv_layout.addItem(box_layout, row, column)
                self.gv_layout.setRowAlignment(row, Qt.AlignCenter)
                self.gv_layout.setColumnAlignment(column, Qt.AlignCenter)

    def selected_detectors(self):
        '''
        Returns a list of IDs of the selected boxes. If there are no selected boxes, then None is returned
        '''
        selected = [box.detector_id for box in self._boxes.values() if box.selected]

        return selected if len(selected) > 0 else None

    def selection_changed(self):
        self.updated.emit()


class MultiDitherDetectorSelector(QWidget):
    """
    A collection of 4 MultiDetectorSelector widgets, which allows the user to choose multiple detectors in multiple
    dithers for analysis.
    """
    updated = pyqtSignal()

    def __init__(self, detectors, *args):
        super().__init__(*args)

        self.setStyleSheet("border: 0px; margin: 0px; padding: 0px;")

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.dithers = []

        row_index = 0
        for i in range(4):
            label = QLabel(f' Dither {i + 1}')
            selector = MultiDetectorSelector(i + 1, detectors[i + 1])
            selector.updated.connect(self.detectors_updated)
            self.dithers.append(selector)
            layout.addWidget(label, row_index, 0)
            row_index += 1
            layout.addWidget(selector, row_index, 0)
            layout.setRowMinimumHeight(row_index, self.dithers[0].min_length)
            row_index += 1

        layout.setColumnMinimumWidth(0, self.dithers[0].min_length)

        self.setMaximumWidth(self.dithers[0].min_length + 20)
        self.setMinimumWidth(self.dithers[0].min_length + 20)
        self.setMinimumHeight(720)
        self.setMaximumHeight(720)

        self.setLayout(layout)

    def selected_detectors(self):
        '''
        Returns the detectors that are currently selected, as a dict: {dither: [detector0, detector1, ... detectorN]}
        where the dither and detectorN are integers. If a dither contains no selected detectors, None, is returned for
        the associated dither number. Results might look like this: {1: None, 2: [1, 2], 3: [2], 4: None}
        '''
        return {dither.dither_number: dither.selected_detectors() for dither in self.dithers}

    def detectors_updated(self):
        self.updated.emit()
