

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

        item = self.scene().itemAt(event.pos(), self.transform())  # This transform or the event.pos() seems to be the incorrect argument.

        if issubclass(type(item), QGraphicsItem) and not isinstance(item, QGraphicsPixmapItem):
            # TODO: forward the right-click to the item somehow
            print("forward the click!")
            return

        menu = QMenu(self)
        show_hide = 'Hide' if self._main.boxes_visible else 'Show'
        show_bounding = menu.addAction(show_hide + " bounding boxes", self._main.toggle_bounding_boxes)

        if not self._main.active_detector_has_spectral_data():
            show_bounding.setDisabled(True)

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
            self.scale(1.0 / self._scale_factor, 1.0 / self._scale_factor)
            self._scale_factor = 1.0
            return

        self.scene().keyPressEvent(event)