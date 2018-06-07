
from astropy import wcs

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QPlainTextEdit, QGridLayout, QVBoxLayout, QApplication


type_name = {1: 'Galaxy', 2: 'Star'}


def make_label_value_pair(label_text, value, value_format):
    text_label = QLabel(f"{label_text}:")
    value_text = f"{value:{value_format}}" if value is not None else 'N/A'
    value_label = QLabel(value_text)
    value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return text_label, value_label


class ObjectInfoWindow(QWidget):
    def __init__(self, info, inspector, *args):
        super().__init__(*args)

        self._info = info
        self._inspector = inspector
        self.setParent(inspector)

        layout = QGridLayout()

        oid_label, oid_value = make_label_value_pair('Object ID', info.id, 's')

        type_label, type_value = make_label_value_pair('Object type', f"{info.type} ({type_name[info.type]})", 's')

        jmag_label, jmag_value = make_label_value_pair('J Mag', info.jmag, '0.4f')

        hmag_label, hmag_value = make_label_value_pair('H Mag', info.hmag, '0.4f')

        ra_label, ra_value = make_label_value_pair('RA', info.ra, '0.4f')

        dec_label, dec_value = make_label_value_pair('Dec', info.dec, '0.4f')

        color_label, color_value = make_label_value_pair('Color', info.color, '0.4f')

        angle_label, angle_value = make_label_value_pair('Angle', info.angle, '0.4f')

        major_axis_label, major_axis_value = make_label_value_pair('Major axis', info.major_axis, '0.4f')

        minor_axis_label, minor_axis_value = make_label_value_pair('Minor axis', info.minor_axis, '0.4f')

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

        self.setContentsMargins(30, 30, 30, 30)

        self.adjustSize()

        self.setWindowOpacity(0.8)

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Q or event.key() == Qt.Key_Escape:
            self.close()


class DetectorInfoWindow(QWidget):
    def __init__(self, inspector, *args):
        super().__init__(*args)

        self._inspector = inspector
        self._dither = None
        self._detector = None
        self.wcs = None
        self.header_string = None
        self.detector_data = None

        vlayout = QVBoxLayout()

        layout = QGridLayout()

        vlayout.addLayout(layout)

        detector_id, self.detector_id_value = make_label_value_pair('Detector ID', 'N/A', 's')
        exp_time, self.exp_time_value = make_label_value_pair('Exposure time [s]', 'N/A', 's')
        ra_aperture, self.ra_aperture_value = make_label_value_pair('Aperture RA', 'N/A', 's')
        dec_aperture, self.dec_aperture_value = make_label_value_pair('Aperture Dec', 'N/A', 's')
        image_orientation, self.image_orientation_value = make_label_value_pair('Image orientation', 'N/A', 's')
        grism_orientation, self.grism_orientation_value = make_label_value_pair('Grism orientation', 'N/A', 's')
        cursor_x, self.cursor_x_value = make_label_value_pair('x', 'N/A', 's')
        cursor_y, self.cursor_y_value = make_label_value_pair('y', 'N/A', 's')
        cursor_ra, self.cursor_ra_value = make_label_value_pair('RA', 'N/A', 's')
        cursor_dec, self.cursor_dec_value = make_label_value_pair('Dec', 'N/A', 's')
        cursor_data, self.cursor_data_value = make_label_value_pair('Pixel value', 'N/A', 's')

        layout.addWidget(detector_id, 0, 0)
        layout.addWidget(self.detector_id_value, 0, 1)
        layout.addWidget(exp_time, 1, 0)
        layout.addWidget(self.exp_time_value, 1, 1)
        layout.addWidget(ra_aperture, 2, 0)
        layout.addWidget(self.ra_aperture_value, 2, 1)
        layout.addWidget(dec_aperture, 3, 0)
        layout.addWidget(self.dec_aperture_value, 3, 1)
        layout.addWidget(image_orientation, 4, 0)
        layout.addWidget(self.image_orientation_value, 4, 1)
        layout.addWidget(grism_orientation, 5, 0)
        layout.addWidget(self.grism_orientation_value, 5, 1)
        layout.addWidget(cursor_x, 6, 0)
        layout.addWidget(self.cursor_x_value, 6, 1)
        layout.addWidget(cursor_y, 7, 0)
        layout.addWidget(self.cursor_y_value, 7, 1)
        layout.addWidget(cursor_ra, 8, 0)
        layout.addWidget(self.cursor_ra_value, 8, 1)
        layout.addWidget(cursor_dec, 9, 0)
        layout.addWidget(self.cursor_dec_value, 9, 1)
        layout.addWidget(cursor_data, 10, 0)
        layout.addWidget(self.cursor_data_value, 10, 1)

        self.header_button = QPushButton('Show Header')
        self.header_button.pressed.connect(self.show_header)
        self.header_button.setFixedWidth(130)

        layout.addWidget(self.header_button, 11, 0)

        self.setLayout(vlayout)

        self.setWindowTitle('Detector Info')
        self.setWindowFlag(Qt.Window, True)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.header_display = None

        # state something about the header data in the FITS file for this detector exposure

        # if there is WCS header info, display the values for the pixel under the cursor

        # show pixel coordinates of pixel under cursor

        # show value of pixel under cursor

        display = QApplication.desktop()

        cursor_x = display.cursor().pos().x()
        cursor_y = display.cursor().pos().y()

        self.setGeometry(cursor_x, cursor_y, 300, 500)

        self.setContentsMargins(30, 30, 30, 30)

        self.adjustSize()

        self.setWindowOpacity(0.8)

    def fetch_header_info(self, dither, detector):
        fits_header = self._inspector.exposures[dither][detector].header
        self.header_string = '\n'.join(str(fits_header.tostring).split('\n')[1:])[:-1]
        self.wcs = wcs.WCS(fits_header)
        self.detector_id_value.setText(fits_header['DET_ID'])
        self.ra_aperture_value.setText(f"{fits_header['RA_APER']:0.5f}")
        self.dec_aperture_value.setText(f"{fits_header['DEC_APER']:0.5f}")
        self.exp_time_value.setText(f"{fits_header['exptime']:0.5f}")
        self.image_orientation_value.setText(f"{fits_header['ORIENTAT']:0.5f}")
        self.grism_orientation_value.setText(f"{fits_header['GORIENT']:0.5f}")

    def update_detector(self, dither, detector):
        self._dither = dither
        self._detector = detector
        self.fetch_header_info(dither, detector)
        self.detector_data = self._inspector.exposures[dither][detector].data
        if self.header_display is not None:
            self.header_display.setPlainText(self.header_string)

    def update_cursor_position(self, position):
        if self.detector_data is None or self.wcs is None or self._detector is None:
            return
        x = position.x()
        y = position.y()
        ra, dec = self.wcs.wcs_pix2world([(x - 0.5, y - 0.5)], 0)[0]

        j = int(y)
        i = int(x)
        jmax, imax = self.detector_data.shape
        in_image = imax > j >= 0 and imax > i >= 0

        self.cursor_x_value.setText(f'{x - 0.5:0.2f}')
        self.cursor_y_value.setText(f'{y - 0.5:0.2f}')
        self.cursor_ra_value.setText(f'{ra:0.6f}')
        self.cursor_dec_value.setText(f'{dec:0.6f}')
        self.cursor_data_value.setText(f'{self.detector_data[j, i] if in_image else 0.0:0.6f}')

    def show_header(self):

        if self.header_display is None:
            self.header_display = QPlainTextEdit(self.header_string)
            self.header_display.setReadOnly(True)
            self.layout().addWidget(self.header_display)
        else:
            self.header_display.setPlainText(self.header_string)

        self.header_display.setMinimumSize(600, 300)
        self.header_display.show()
        self.adjustSize()
        self.header_button.setText('Hide header')
        self.header_button.pressed.connect(self.hide_header)

    def hide_header(self):
        self.setMinimumSize(0, 0)
        self.header_display.hide()
        self.adjustSize()
        self.header_button.setText('Show header')
        self.header_button.pressed.connect(self.show_header)


