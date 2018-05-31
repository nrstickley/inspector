import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QApplication


class SpecTable(QTableWidget):

    def __init__(self, view, *args):
        super().__init__(*args)
        self.view = view
        self.setHorizontalHeaderLabels(['Object ID', 'Order'])
        self.data = None
        self.itemSelectionChanged.connect(self.handle_selection)
        self.cellActivated.connect(self.handle_activated_cell)

    def add_spectra(self, data):
        """
        Adds spectral data to the table widget

        Parameters
        ----------

        data: NumPy array
            An array with named columns. Column 0: 'id', Column1: 'order'
        """
        if self.data is None:
            self.data = data
        else:
            np.concatenate((self.data, data))

        for i, row_data in enumerate(data):
            self.add_row(i, row_data)

    def add_row(self, row_index, row_data):
        object_id, order = row_data

        id_item = QTableWidgetItem(str(object_id))
        order_item = QTableWidgetItem(str(order))

        id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
        order_item.setFlags(order_item.flags() & ~Qt.ItemIsEditable)

        self.setItem(row_index, 0, id_item)
        self.setItem(row_index, 1, order_item)

        padding = 32

        width = self.verticalHeader().width() + self.columnCount() * self.columnWidth(0) + 8
        height = self.horizontalHeader().height() + self.rowCount() * self.rowHeight(0) + 8

        display = QApplication.desktop()

        cursor_x = display.cursor().pos().x()
        cursor_y = display.cursor().pos().y()

        current_screen = display.screenNumber(self.view)

        geom = display.screenGeometry(current_screen)

        screen_height = geom.height()

        height = min(screen_height - 2 * padding, height)

        self.setGeometry(cursor_x - padding, cursor_y, width, height)

    def handle_activated_cell(self, i , j):

        print(f'cell {i}, {j}, has been activated.')

    def handle_selection(self):
        # unpin any spectra that are not selected
        for row in range(self.rowCount()):
            id_item = self.item(row, 0)
            order_item = self.item(row, 1)
            if not id_item.isSelected() and not order_item.isSelected():
                self.view.main.unselect_spectrum_by_id(id_item.text())

        # pin the selected spectra
        for item in self.selectedItems():
            row = item.row()
            object_id = self.item(row, 0).text()
            order = int(self.item(row, 1).text())
            if order == 1:
                self.view.main.select_spectrum_by_id(object_id)

