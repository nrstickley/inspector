

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QMenu, QAction, QGraphicsItem,
                             QGraphicsPixmapItem)


class View(QGraphicsView):

    def __init__(self, main):
        super().__init__()
        self._main = main
        self.setDragMode(QGraphicsView.RubberBandDrag)

        self._scale_factor = 1.0

    def contextMenuEvent(self, event):

        item = self.scene().itemAt(event.pos(), self.transform())

        if issubclass(type(item), QGraphicsItem) and not isinstance(item, QGraphicsPixmapItem):
            return

        menu = QMenu(self)
        show_hide = 'Hide' if self._main.boxes_visible else 'Show'
        show_hide_bounding = menu.addAction(show_hide + " bounding boxes", self._main.toggle_bounding_boxes)

        if self._main.n_pinned_boxes() > 0:
            remove_pinned = menu.addAction('Remove pinned boxes', self._main.remove_pinned_boxes)

        if not self._main.active_detector_has_spectral_data():
            show_hide_bounding.setDisabled(True)

        menu.exec(event.globalPos())

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