import numpy as np
import matplotlib as mpl
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QPen, QTransform
from PyQt5.QtWidgets import (QGraphicsRectItem, QMenu, QAction, QGraphicsTextItem, QGraphicsItem,
                             QGraphicsSceneMouseEvent, QApplication, QMessageBox)

from spec_table import SpecTable
from plot_window import PlotWindow
from info_window import ObjectInfoWindow


flip_vertical = QTransform(1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0)

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
            self.label.setTransform(flip_vertical, True)
            self.label.setPos(label_pos)
            self.label.setDefaultTextColor(QColor('red'))
        else:
            self.label = QGraphicsTextItem(f"{self._spec.id}")
            self.label.setTransform(flip_vertical, True)
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

        def action(title, slot, caption=None, shortcut=None):
            act = QAction(title, menu)
            act.triggered.connect(slot)
            if caption is not None:
                act.setStatusTip(caption)

            if shortcut is not None:
                act.setShortcut(shortcut)
                act.setShortcutVisibleInContextMenu(True)
            return act

        menu.addSection(f'Object {self.spec.id}')

        menu.addAction(action('Show table of contaminants', self.show_contaminant_table, shortcut='T'))
        menu.addAction(action('Show Object Info', self.show_info, 'Show details about this object', 'I'))
        menu.addAction(action('Open Object tab', self.open_analysis_tab, shortcut=Qt.Key_Home))
        menu.addAction(action('Show in all detectors',  self.open_all_spectra, 'Show all spectra of object in new tabs',
                              Qt.Key_Space))

        menu.addSection('Plots')

        menu.addAction(action('Plot column sums', self.plot_column_sums, shortcut=Qt.Key_Up))
        menu.addAction(action('Plot row sums', self.plot_row_sums, shortcut=Qt.Key_Right))
        menu.addAction(action('Show all layers', self.show_all_layers, shortcut='A'))
        menu.addAction(action('Show decontaminated spectrum', self.show_decontaminated, shortcut='D'))
        menu.addAction(action('Show original spectrum', self.show_original, shortcut='O'))
        menu.addAction(action('Show contamination', self.show_contamination, shortcut='C'))
        menu.addAction(action('Show variance', self.show_variance, shortcut='V'))
        menu.addAction(action('Show zeroth-order positions', self.show_zeroth_orders, shortcut=Qt.Key_Z|Qt.Key_0))
        menu.addAction(action('Show residual', self.show_residual, shortcut='R'))
        menu.addAction(action('Show model spectrum', self.show_model, shortcut='M'))

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
        plt.imshow(data, origin='lower')
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
        plt.imshow(self.spec.contamination + self.spec.science, origin='lower')
        plt.title('Original')
        plt.draw()

        plt.sca(plot.axis[1])
        plt.imshow(self.spec.contamination, origin='lower')
        plt.title('Contamination')
        plt.draw()

        plt.sca(plot.axis[2])
        plt.imshow(self.spec.science, origin='lower')
        plt.title('Decontaminated')
        plt.draw()

        plt.sca(plot.axis[3])
        if self.model is not None:
            plt.imshow(self.model, origin='lower')
            plt.title('Model')
        else:
            plt.title('N/A')
        plt.draw()

        plt.sca(plot.axis[4])
        if self.model is not None:
            plt.imshow(self.spec.science - self.model, origin='lower')
            plt.title('Residual')
        else:
            plt.title('N/A')
        plt.draw()

        plt.sca(plot.axis[5])
        plt.imshow(self.spec.variance, origin='lower')
        plt.title('Variance')
        plt.draw()

        plt.sca(plot.axis[6])
        data = (flag['ZERO'] & self.spec.mask) == flag['ZERO']
        plt.imshow(data, origin='lower')
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
        view_tab = self.view.view_tab
        inspector = view_tab.inspector
        inspector.new_analysis_tab(view_tab.current_dither, view_tab.current_detector, self.spec.id)

    def open_all_spectra(self):
        view_tab = self.view.view_tab
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

        view_tab = self.view.view_tab
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
            m.exec()
