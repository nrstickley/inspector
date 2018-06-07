
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QGraphicsView, QMenu,)

from specbox import Rect


class View(QGraphicsView):

    def __init__(self, main):
        super().__init__()
        self._main = main
        self.setDragMode(QGraphicsView.RubberBandDrag)

        self._scale_factor = 1.0

        self._ignore_count = 0

        self.setMouseTracking(True)

    def contextMenuEvent(self, event):

        item = self.scene().itemAt(event.globalPos(), self.transform())

        if isinstance(item, Rect) and item.contains(event.pos()):
            return

        if self.clicks_ignored():
            return

        menu = QMenu(self)
        show_hide = 'Hide' if self._main.boxes_visible else 'Show'
        show_hide_bounding = menu.addAction(show_hide + " bounding boxes", self._main.toggle_bounding_boxes)

        if self._main.n_pinned_boxes() > 0:
            menu.addAction('Remove pinned boxes', self._main.remove_pinned_boxes)

        if not self._main.active_detector_has_spectral_data():
            show_hide_bounding.setDisabled(True)

        menu.exec(event.globalPos())

    def ignore_clicks(self):
        self._ignore_count += 1

    def clicks_ignored(self):
        result = self._ignore_count > 0
        self._ignore_count = max(0, self._ignore_count - 1)
        return result

    def keyPressEvent(self, event):

        increment = 1.05

        if event.key() == Qt.Key_Plus:
            self._scale_factor *= increment
            self.scale(increment, increment)
            return

        if event.key() == Qt.Key_Minus:
            self._scale_factor /= increment
            self.scale(1.0 / increment, 1.0 / increment)
            return

        if event.key() == Qt.Key_1:
            self.resetTransform()
            return

        self.scene().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        position = self.mapToScene(event.pos())

        self.main.inspector.detector_info_window.update_cursor_position(position)

        super().mouseMoveEvent(event)

    @property
    def main(self):
        return self._main