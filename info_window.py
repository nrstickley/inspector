
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QGroupBox, QGridLayout, QApplication


type_name = {1: 'Galaxy', 2: 'Star'}


class ObjectInfoWindow(QWidget):
    def __init__(self, info, inspector, *args):
        super().__init__(*args)

        self._info = info
        self._inspector = inspector

        layout = QGridLayout()

        oid_label = QLabel(f"Object ID:")
        oid_value = QLabel(f"{info.id}")
        oid_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        type_label = QLabel(f"Object type:")
        type_value = QLabel(f"{info.type} ({type_name[info.type]})")
        type_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        jmag_label = QLabel(f"J Mag:")
        jmag_value_text = f"{info.jmag:0.4f}" if info.jmag is not None else 'N/A'
        jmag_value = QLabel(jmag_value_text)
        jmag_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        hmag_label = QLabel(f"H Mag:")
        hmag_value_text = f"{info.hmag:0.4f}" if info.hmag is not None else 'N/A'
        hmag_value = QLabel(hmag_value_text)
        hmag_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        ra_label = QLabel(f"RA:")
        ra_value = QLabel(f"{info.ra:0.4f}")
        ra_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        dec_label = QLabel(f"Dec:")
        dec_value = QLabel(f"{info.dec:0.4f}")
        dec_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        color_label = QLabel(f"Color:")
        color_value = QLabel(f"{info.color:0.4f}")
        color_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        angle_label = QLabel(f"Angle:")
        angle_value = QLabel(f"{info.angle:0.4f}")
        angle_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        major_axis_label = QLabel(f"Major axis:")
        major_axis_value = QLabel(f"{info.major_axis:0.4f}")
        major_axis_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        minor_axis_label = QLabel(f"Minor axis:")
        minor_axis_value = QLabel(f"{info.minor_axis:0.4f}")
        minor_axis_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(oid_label, 0, 0)
        layout.addWidget(oid_value, 0, 1)

        layout.addWidget(type_label, 1, 0)
        layout.addWidget(type_value, 1, 1)

        layout.addWidget(jmag_label, 2, 0)
        layout.addWidget(jmag_value, 2, 1)

        layout.addWidget(hmag_label, 3, 0)
        layout.addWidget(hmag_value, 3, 1)

        layout.addWidget(color_label, 4, 0)
        layout.addWidget(color_value, 4, 1)

        layout.addWidget(ra_label, 5, 0)
        layout.addWidget(ra_value, 5, 1)

        layout.addWidget(dec_label, 6, 0)
        layout.addWidget(dec_value, 6, 1)

        layout.addWidget(angle_label, 7, 0)
        layout.addWidget(angle_value, 7, 1)

        layout.addWidget(major_axis_label, 8, 0)
        layout.addWidget(major_axis_value, 8, 1)

        layout.addWidget(minor_axis_label, 9, 0)
        layout.addWidget(minor_axis_value, 9, 1)

        self.setLayout(layout)

        self.setWindowTitle('Object Info')
        self.setWindowFlag(Qt.Window, True)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        display = QApplication.desktop()

        cursor_x = display.cursor().pos().x()
        cursor_y = display.cursor().pos().y()

        self.setGeometry(cursor_x, cursor_y, 300, 500)

        self.setContentsMargins(20, 20, 20, 20)

        self.adjustSize()

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Q or event.key() == Qt.Key_Escape:
            self.close()