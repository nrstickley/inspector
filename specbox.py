import numpy as np
import matplotlib as mpl
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import (QGraphicsRectItem, QMenu, QAction, QGraphicsTextItem, QGraphicsItem,
                             QGraphicsSceneMouseEvent, QApplication, QMessageBox)

from spec_table import SpecTable
from plot_window import PlotWindow
from info_window import ObjectInfoWindow


flag = {"ZERO": np.uint32(2**18),     # zeroth-order: bit 18
        "MISSING": np.uint32(2**19),  # missing data: bit 19
        "SIGCONT": np.uint32(2**20)}  # significantly contaminated; contamination flux is > 10% of source flux: bit 20


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
        self._model = None
        self._contam_table = None
        self._info_window = None

        self._key_bindings = {Qt.Key_Up:   self.plot_column_sums,
                              Qt.Key_Down: self.plot_column_sums,
                              Qt.Key_Right: self.plot_row_sums,
                              Qt.Key_Left: self.plot_row_sums,
                              Qt.Key_S:    self.show_decontaminated,
                              Qt.Key_D:    self.show_decontaminated,
                              Qt.Key_V:    self.show_variance,
                              Qt.Key_C:    self.show_contamination,
                              Qt.Key_L:    self.show_contaminant_table,
                              Qt.Key_T:    self.show_contaminant_table,
                              Qt.Key_0:    self.show_zeroth_orders,
                              Qt.Key_Z:    self.show_zeroth_orders,
                              Qt.Key_R:    self.show_residual,
                              Qt.Key_O:    self.show_original,
                              Qt.Key_A:    self.show_all_layers,
                              Qt.Key_M:    self.show_model,
                              Qt.Key_I:    self.show_info,
                              Qt.Key_Home: self.open_analysis_tab,
                              Qt.Key_Space: self.open_all_spectra}

    @property
    def spec(self):
        return self._spec

    @spec.setter
    def spec(self, spec):
        self._spec = spec

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        self._model = model

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

        if event.key() in self._key_bindings:
            self._key_bindings[event.key()]()

    def handle_right_click(self, pos):
        menu = QMenu()

        table_of_contaminants = QAction('Show table of contaminants')
        table_of_contaminants.setStatusTip('Show a table containing information about the spectra that '
                                           'contaminate this source.')
        table_of_contaminants.setShortcut('T')
        table_of_contaminants.setShortcutVisibleInContextMenu(True)
        table_of_contaminants.triggered.connect(self.show_contaminant_table)

        object_info = QAction('Show Object Info')
        object_info.setStatusTip('Show details about this object')
        object_info.setShortcut('I')
        object_info.setShortcutVisibleInContextMenu(True)
        object_info.triggered.connect(self.show_info)

        object_tab = QAction('Open Object tab')
        object_tab.setShortcut(Qt.Key_Home)
        object_tab.setShortcutVisibleInContextMenu(True)
        object_tab.triggered.connect(self.open_analysis_tab)

        show_in_all = QAction('Show in all detectors')
        show_in_all.setStatusTip('Show this object in all detectors')
        show_in_all.setShortcut(Qt.Key_Space)
        show_in_all.setShortcutVisibleInContextMenu(True)
        show_in_all.triggered.connect(self.open_all_spectra)

        show_all_layers = QAction('Show all layers')
        show_all_layers.setShortcut('A')
        show_all_layers.setShortcutVisibleInContextMenu(True)
        show_all_layers.triggered.connect(self.show_all_layers)

        # show_decon = QAction()
        # show_decon.setStatusTip()
        # show_decon.setShortcut()
        # show_decon.setShortcutVisibleInContextMenu(True)
        # show_decon.triggered.connect(self.)
        #
        # show_original = QAction()
        # show_original.setStatusTip()
        # show_original.setShortcut()
        # show_original.setShortcutVisibleInContextMenu(True)
        # show_original.triggered.connect(self.)
        #
        # show_contamination = QAction()
        # show_contamination.setStatusTip()
        # show_contamination.setShortcut()
        # show_contamination.setShortcutVisibleInContextMenu(True)
        # show_contamination.triggered.connect(self.)
        #
        # show_variance = QAction()
        # show_variance.setStatusTip()
        # show_variance.setShortcut()
        # show_variance.setShortcutVisibleInContextMenu(True)
        # show_variance.triggered.connect(self.)
        #
        # show_zeroth = QAction()
        # show_zeroth.setStatusTip()
        # show_zeroth.setShortcut()
        # show_zeroth.setShortcutVisibleInContextMenu(True)
        # show_zeroth.triggered.connect(self.)
        #
        # show_residual = QAction()
        # show_residual.setStatusTip()
        # show_residual.setShortcut()
        # show_residual.setShortcutVisibleInContextMenu(True)
        # show_residual.triggered.connect(self.)
        #
        # show_model = QAction()
        # show_model.setStatusTip()
        # show_model.setShortcut()
        # show_model.setShortcutVisibleInContextMenu(True)
        # show_model.triggered.connect(self.)

        plot_columns = QAction('Plot column sums', menu)
        plot_columns.setStatusTip('Plot the sums of the columns of pixels in the 2D spectrum.')
        plot_columns.setShortcut(Qt.Key_Up)
        plot_columns.setShortcutVisibleInContextMenu(True)
        plot_columns.triggered.connect(self.plot_column_sums)

        plot_rows = QAction('Plot row sums', menu)
        plot_rows.setStatusTip('Plot the sums of the rows of pixels in the 2D spectrum.')
        plot_rows.setShortcut(Qt.Key_Right)
        plot_rows.setShortcutVisibleInContextMenu(True)
        plot_rows.triggered.connect(self.plot_row_sums)

        menu.addSection(f'Object {self.spec.id}')

        menu.addAction(table_of_contaminants)
        menu.addAction(object_info)
        menu.addAction(object_tab)
        menu.addAction(show_in_all)

        menu.addSection('Plots')

        menu.addAction(plot_columns)
        menu.addAction(plot_rows)
        menu.addAction(show_all_layers)
        menu.addAction("Show decontaminated spectrum", self.show_decontaminated)
        menu.addAction("Show original spectrum", self.show_original)
        menu.addAction("Show contamination", self.show_contamination)
        menu.addAction("Show decontaminated variance", self.show_variance)
        menu.addAction("Show zeroth-order positions", self.show_zeroth_orders)
        menu.addAction("Show residual", self.show_residual)
        menu.addAction("Show model spectrum", self.show_model)

        menu.exec(pos)

        self.view.ignore_clicks()

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
        self.show_spec_layer(title, self.spec.variance)

    def show_decontaminated(self):
        title = f'Decontaminated Spectrum of {self.spec.id}'
        self.show_spec_layer(title, self.spec.science)

    def show_contamination(self):
        title = f'Contamination of {self.spec.id}'
        self.show_spec_layer(title, self.spec.contamination)

    def show_zeroth_orders(self):
        title = f'Zeroth-order contamination regions of {self.spec.id}'
        data = (flag['ZERO'] & self.spec.mask) == flag['ZERO']
        self.show_spec_layer(title, data)

    def show_original(self):
        title = f'{self.spec.id} before decontamination'
        self.show_spec_layer(title, self.spec.contamination + self.spec.science)

    def show_residual(self):
        if self.model is not None:
            title = f"residual spectrum of {self.spec.id}"
            self.show_spec_layer(title, self.spec.science - self.model)

    def show_model(self):
        if self.model is not None:
            title = f"Model of {self.spec.id}"
            self.show_spec_layer(title, self.model)

    def show_spec_layer(self, title, data):
        plot = PlotWindow(title)

        plt.sca(plot.axis)
        plt.imshow(data)
        plt.subplots_adjust(top=0.975, bottom=0.025, left=0.025, right=0.975)
        plt.draw()
        plot.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        plot.show()

        padding = 32

        display = QApplication.desktop()
        current_screen = display.screenNumber(self.view)
        geom = display.screenGeometry(current_screen)
        width = geom.width() - 2 * padding
        height = geom.height() - 2 * padding
        plot.setGeometry(geom.left() + padding, geom.top() + padding, width, height)
        plt.close()

    def show_all_layers(self):
        title = f'All Layers of {self.spec.id}'
        horizontal = self.rect().width() > self.rect().height()
        subplot_grid_shape = (7, 1) if horizontal else (1, 7)

        plot = PlotWindow(title, shape=subplot_grid_shape)

        plt.sca(plot.axis[0])
        plt.imshow(self.spec.contamination + self.spec.science)
        plt.title('Original')
        plt.draw()

        plt.sca(plot.axis[1])
        plt.imshow(self.spec.contamination)
        plt.title('Contamination')
        plt.draw()

        plt.sca(plot.axis[2])
        plt.imshow(self.spec.science)
        plt.title('Decontaminated')
        plt.draw()

        plt.sca(plot.axis[3])
        if self.model is not None:
            plt.imshow(self.model)
            plt.title('Model')
        else:
            plt.title('N/A')
        plt.draw()

        plt.sca(plot.axis[4])
        if self.model is not None:
            plt.imshow(self.spec.science - self.model)
            plt.title('Residual')
        else:
            plt.title('N/A')
        plt.draw()

        plt.sca(plot.axis[5])
        plt.imshow(self.spec.variance)
        plt.title('Variance')
        plt.draw()

        plt.sca(plot.axis[6])
        data = (flag['ZERO'] & self.spec.mask) == flag['ZERO']
        plt.imshow(data)
        plt.title('Zeroth Orders')
        plt.draw()

        if horizontal:
            plt.subplots_adjust(top=0.97, bottom=0.025, left=0.025, right=0.975, hspace=0, wspace=0)
        else:
            plt.subplots_adjust(top=0.9, bottom=0.03, left=0.025, right=0.975, hspace=0, wspace=0)

        plt.draw()
        plot.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        plot.show()

        padding = 50

        display = QApplication.desktop()
        current_screen = display.screenNumber(self.view)
        geom = display.screenGeometry(current_screen)
        width = geom.width() - 2 * padding
        height = geom.height() - 2 * padding
        plot.setGeometry(geom.left() + padding, geom.top() + padding, width, height)
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
        view_tab = self.view.main
        inspector = view_tab.inspector
        inspector.new_analysis_tab(view_tab.current_dither, view_tab.current_detector, self.spec.id)

    def open_all_spectra(self):
        view_tab = self.view.main
        inspector = view_tab.inspector

        # make a list of all open detectors (detectors currently being viewed in tabs)

        open_detectors = []

        for tab_index in range(inspector.tabs.count()):
            tab = inspector.tabs.widget(tab_index)
            if isinstance(tab, type(view_tab)):
                open_detectors.append((tab.current_dither, tab.current_detector))

        # open new tabs, where necessary

        for dither in inspector.get_object_dithers(self.spec.id):
            for detector in inspector.get_object_detectors(dither, self.spec.id):
                if (dither, detector) not in open_detectors:
                    inspector.new_view_tab(dither, detector)

        # pin the object in all tabs:

        for tab_index in range(inspector.tabs.count()):
            tab = inspector.tabs.widget(tab_index)
            if isinstance(tab, type(view_tab)):
                tab.select_spectrum_by_id(self.spec.id)

    def show_info(self):

        view_tab = self.view.main
        inspector = view_tab.inspector

        if inspector.location_tables is not None:
            info = inspector.location_tables.get_info(self.spec.id)
            info_window = ObjectInfoWindow(info, inspector)
            info_window.show()
            # todo: refine window placement (imitate table placement)
            self._info_window = info_window
        else:
            m = QMessageBox(0, 'No Object info available',
                            "Location tables containing the requested information must be loaded before showing info.",
                            QMessageBox.NoButton)
            m.setWindowFlag(Qt.Window, True)
            m.exec()
