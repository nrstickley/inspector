
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsView, QMenu

from specbox import SpecBox, flip_vertical


class View(QGraphicsView):
    """
    Constructs the widget in which detector images can be viewed. The View is zoomable, using +/- keys, and it is
    flipped such that the lower-left corner has coordinates (0, 0) and the +y direction is upward.
    """
    def __init__(self, view_tab):
        super().__init__()
        self._view_tab = view_tab
        self.setDragMode(QGraphicsView.RubberBandDrag)

        self._scale_factor = 1.0

        self._ignore_count = 0

        self.setMouseTracking(True)

        self.setTransform(flip_vertical, True)

    def contextMenuEvent(self, event):

        item = self.scene().itemAt(event.globalPos(), self.transform())

        if isinstance(item, SpecBox) and item.contains(event.pos()):
            return

        if self.clicks_ignored():
            return

        menu = QMenu(self)
        show_hide_boxes = 'Hide' if self._view_tab.boxes_visible else 'Show'
        show_hide_bounding = menu.addAction(show_hide_boxes + " bounding boxes", self._view_tab.toggle_bounding_boxes)

        if self._view_tab.n_pinned_boxes() > 0:
            menu.addAction('Remove pinned boxes', self._view_tab.remove_pinned_boxes)

        if not self._view_tab.active_detector_has_spectral_data():
            show_hide_bounding.setDisabled(True)

        menu.exec(event.globalPos())

    def ignore_clicks(self):
        """
        Instructs the `View` instance to ignore the next mouse click.
        """
        self._ignore_count += 1

    def clicks_ignored(self):
        """
        Returns True if clicks are currently being ignored, and decrements the internal counter which keeps track of
        the number of clicks that should be ignored. Returns False if clicks are not being ignored.
        """
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
            self.setTransform(flip_vertical, True)
            return

        self.scene().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        position = self.mapToScene(event.pos())

        self.view_tab.inspector.detector_info_window.update_cursor_position(position)

        super().mouseMoveEvent(event)

    @property
    def view_tab(self):
        return self._view_tab
