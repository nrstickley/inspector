import matplotlib as mpl
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import (QGraphicsRectItem, QMenu, QAction, QGraphicsTextItem, QGraphicsItem,
                             QGraphicsSceneMouseEvent, QApplication)

from spec_table import SpecTable
from plot_window import PlotWindow


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

    @property
    def view(self):
        return self.scene().views()[0]

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
            self.show_variance()
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
            self.show_contaminant_table()

    def handle_right_click(self, pos):
        menu = QMenu()

        table_of_contaminants = QAction('Show table of contaminants')
        table_of_contaminants.setStatusTip('Show a table containing information about the spectra that '
                                           'contaminate this source.')
        table_of_contaminants.triggered.connect(self.show_contaminant_table)

        plot_columns = QAction('Plot column sums', menu)
        plot_columns.setStatusTip('Plot the sums of the columns of pixels in the 2D spectrum.')
        plot_columns.triggered.connect(self.plot_column_sums)

        plot_rows = QAction('Plot row sums', menu)
        plot_rows.setStatusTip('Plot the sums of the rows of pixels in the 2D spectrum.')
        plot_rows.triggered.connect(self.plot_row_sums)

        menu.addAction("Open in analysis tab", self.open_analysis_tab)
        menu.addAction(f"Open all spectra of object {self.spec.id}", self.open_all_spectra)
        menu.addAction("Show Info window", self.view.main.inspector.show_info)
        menu.addAction(table_of_contaminants)

        menu.addSection('Plots')
        menu.addAction(plot_columns)
        menu.addAction(plot_rows)

        menu.exec(pos)

    def contextMenuEvent(self, event: 'QGraphicsSceneContextMenuEvent'):
        self.handle_right_click(event.screenPos())

    def plot_column_sums(self):
        self.plot_pixel_sums(0, 'Column')

    def plot_row_sums(self):
        self.plot_pixel_sums(1, 'Row')

    def plot_pixel_sums(self, axis, label):

        plot = PlotWindow(f'{self.spec.id} {label} Sum')

        plt.sca(plot.axis)
        science = self.spec.science.sum(axis=axis)
        contamination = self.spec.contamination.sum(axis=axis)
        plt.plot(contamination, alpha=0.6, label='Contamination')
        plt.plot(science + contamination, alpha=0.6, label='Original')
        plt.plot(science, label='Decontaminated')
        plt.title(f'Object ID: {self.spec.id}')
        plt.xlabel(f'Pixel {label}')
        plt.ylabel(f'{label} Sum')
        plt.legend()
        plt.draw()
        plot.show()
        plot.adjustSize()
        plt.close()

    def show_variance(self):
        title = f'Variance of {self.spec.id}'

        plot = PlotWindow(title)

        plt.sca(plot.axis)
        plt.imshow(self.spec.variance)
        #plt.colorbar()
        plt.subplots_adjust(top=0.985, bottom=0.025, left=0.025, right=0.985)
        plt.draw()
        plot.show()
        geom = QApplication.desktop().geometry()
        geom.setWidth(int(0.95 * geom.width()))
        geom.setHeight(int(0.95 * geom.height()))
        plot.setGeometry(geom)
        plt.close()

    def show_contaminant_table(self):
        contents = self.spec.contaminants
        rows = len(contents)
        columns = 2

        self._contam_table = SpecTable(self.view, rows, columns)
        self._contam_table.setWindowTitle('Contaminants')
        self._contam_table.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self._contam_table.setWindowFlag(Qt.Window, True)
        self._contam_table.add_spectra(contents)
        self._contam_table.show()

    def open_analysis_tab(self):
        print('this is where I would open an analysis tab.')

    def open_all_spectra(self):
        print(f'this will open all spectra of {self.spec.id}')
