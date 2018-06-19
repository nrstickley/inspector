from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton
import matplotlib

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import pyplot as plt


class PlotWindow(QWidget):
    """
    A container in which to place plots generated by matplotlib.
    """
    closing = pyqtSignal([str])

    def __init__(self, title, shape=None, *args):
        super().__init__(*args)

        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.Window, True)
        self.setContentsMargins(0, 0, 0, 0)
        self._descriptor = ''

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title = title

        if shape is None:
            self.fig, self.axis = plt.subplots()
            self.axis.set_title(self.title)
        else:
            rows, columns = shape
            self.fig, self.axis = plt.subplots(rows, columns)
            self.fig.suptitle(title)

        self.fig.set_dpi(100)

        self.figure_widget = FigureCanvas(self.fig)

        toolbar = NavigationToolbar(self.figure_widget, self)

        layout.addWidget(self.figure_widget)
        layout.addWidget(toolbar)

        self._command_box = None
        self._run_command_btn = None

        self.setLayout(layout)

    @property
    def descriptor(self):
        return self._descriptor

    @descriptor.setter
    def descriptor(self, descriptor):
        if not isinstance(descriptor, str):
            raise TypeError('The descriptor must be a string.')

        self._descriptor = descriptor

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q or event.key() == Qt.Key_Escape:
            self.close()
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_E:
            self.show_editor()

    def closeEvent(self, event):
        self.closing.emit(self._descriptor)
        plt.close(self.fig)
        super().closeEvent(event)

    def show_editor(self):
        if self._command_box is None:
            self._command_box = QTextEdit()
            self._command_box.setPlaceholderText('Enter plotting commands here, using `fig` and `axis`.')
            self._command_box.setMinimumHeight(25)
            self._command_box.setFont(QFont('monospace'))
            self._run_command_btn = QPushButton('Execute Command')
            self._run_command_btn.setMinimumSize(150, 25)
            self._run_command_btn.setMaximumSize(200, 30)
            self._run_command_btn.pressed.connect(self.exec_command)

            self.layout().addWidget(self._command_box)
            self.layout().setAlignment(self._run_command_btn, Qt.AlignHCenter)
            self.layout().addWidget(self._run_command_btn)
        else:
            print('removing the editor')
            self._command_box.hide()
            self._run_command_btn.hide()
            # TODO: check on this:
            self.layout().removeWidget(self._run_command_btn)
            self.layout().removeWidget(self._command_box)
            self._run_command_btn = None
            self._command_box = None
            self.layout().update()
            self.update()

    def exec_command(self):
        command_text = self._command_box.toPlainText()
        print("running command:")
        print(command_text)
        exec(command_text, {}, self.__dict__)
        self.fig.canvas.draw()
