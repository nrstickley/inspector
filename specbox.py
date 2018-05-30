import matplotlib as mpl
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import (QWidget, QGraphicsRectItem, QMenu, QAction, QGraphicsTextItem, QGraphicsItem,
                             QTableWidget, QGraphicsSceneMouseEvent, QDockWidget, QVBoxLayout)

red_pen = QPen(QColor('red'))
green_pen = QPen(QColor('green'))


class Rect(QGraphicsRectItem):

    inactive_opacity = 0.21  # the opacity of rectangles that are not in focus

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
        self._contam_table = None

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
        event.button()

        if keys & Qt.CTRL:
            self.grabKeyboard()
        elif event.button() == Qt.LeftButton:
            self.handle_pinning(event)
            self.grabKeyboard()
        elif event.button() == Qt.RightButton:
            self.handle_right_click(event.screenPos())

    def handle_pinning(self, event):
        if self.pinned:  # it's already pinned; unpin it
            self.unpin()
        else:  # it's not pinned; pin it
            self.pin(event.scenePos())

    def pin(self, label_pos=None):
        if label_pos is not None:
            self.label = QGraphicsTextItem(f"{self._spec.id}", parent=self)
            self.label.setPos(label_pos)
            self.label.setDefaultTextColor(QColor('red'))
        else:
            self.label = QGraphicsTextItem(f"{self._spec.id}")
            self.label.setDefaultTextColor(QColor('red'))
            self.scene().addItem(self.label)
            self.label.setPos(self.scenePos())

        self.setPen(red_pen)
        self.setOpacity(1.0)
        self.pinned = True

    def unpin(self):
        self.setPen(green_pen)
        if self.label is not None:
            self.scene().removeItem(self.label)
            self.label = None
        self.pinned = False

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Up or event.key() == Qt.Key_Down:
            self.plot_column_sums()
            return

        if event.key() == Qt.Key_Right or event.key() == Qt.Key_Left:
            self.plot_row_sums()
            return

        if event.key() == Qt.Key_S:
            plt.close()
            plt.imshow(self._spec.science)
            plt.title('Decontaminated Spectrum')
            plt.show()
            return

        if event.key() == Qt.Key_V:
            plt.close()
            plt.imshow(self._spec.variance)
            plt.title('Variance')
            plt.show()
            return

        if event.key() == Qt.Key_C:
            plt.close()
            plt.imshow(self._spec.contamination)
            plt.title('Contamination')
            plt.show()
            return

        if event.key() == Qt.Key_O:
            plt.close()
            plt.imshow(self.spec.contamination + self.spec.science)
            plt.title('Original Data')
            plt.show()
            return

        # todo: show the residual. raise main window to top or make it active at least (better).
        # add ability to add multiple plots to the same canvas

        if event.key() == Qt.Key_L:
            print("Contaminants:")
            print(self._spec.contaminants)

    def handle_right_click(self, pos):

        print(f'handling right click for {self.spec.id}')
        menu = QMenu()

        open_in_analysis = menu.addAction("Open in analysis tab", self.open_analysis_tab)

        show_info_window = menu.addAction("Show Info window", self.scene().views()[0]._main.inspector.show_info)

        plot_columns = QAction('Plot column sums', menu)
        plot_columns.setStatusTip('Plot the sums of the columns of pixels in the 2D spectrum.')
        plot_columns.triggered.connect(self.plot_column_sums)

        plot_rows = QAction('Plot row sums', menu)
        plot_rows.setStatusTip('Plot the sums of the rows of pixels in the 2D spectrum.')
        plot_rows.triggered.connect(self.plot_row_sums)

        table_of_contaminants = QAction('Show table of contaminants')
        table_of_contaminants.setStatusTip('Show a table containing information about the spectra that '
                                           'contaminate this source.')
        table_of_contaminants.triggered.connect(self.show_contaminant_table)

        menu.addAction(plot_columns)
        menu.addAction(plot_rows)
        menu.addAction(table_of_contaminants)
        menu.exec(pos)

    def plot_column_sums(self):
        self.plot_pixel_sums(0, 'Column')

    def plot_row_sums(self):
        self.plot_pixel_sums(1, 'Row')

    def plot_pixel_sums(self, axis, label):
        plt.close()
        science = self.spec.science.sum(axis=axis)
        contamination = self.spec.contamination.sum(axis=axis)
        plt.plot(contamination, alpha=0.6, label='Contamination')
        plt.plot(science + contamination, alpha=0.6, label='Original')
        plt.plot(science, label='Decontaminated')
        plt.title(f'Object ID: {self.spec.id}')
        plt.xlabel(f'Pixel {label}')
        plt.ylabel(f'{label} Sum')
        plt.legend()
        plt.show()

    def show_contaminant_table(self):
        print('showing contaminants')
        contents = self.spec.contaminants
        rows = len(contents)
        columns = 2
        self._contam_table = QTableWidget(rows, columns)
        self._contam_table.setWindowFlag(Qt.Window, True)
        self._contam_table.setHorizontalHeaderLabels(['Object ID', 'Order'])
        self._contam_table.show()
        # https://evileg.com/en/post/236/
        # http://doc.qt.io/qt-5/qtablewidget.html

    def open_analysis_tab(self):
        print('this is where I would open an analysis tab.')
