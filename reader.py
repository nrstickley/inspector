import os
import h5py
import json

import numpy as np

from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import QEventLoop

import utils


DITHER_LABEL = 'Dither'
GRISM_POSITION_LABEL = 'Grism Position'
EXPOSURE_ID_LABEL = 'Exposure ID'
FIELD_ID_LABEL = 'Field ID'


NISP_DETECTOR_MAP = {1: '11',
                     2: '21',
                     3: '31',
                     4: '41',
                     5: '12',
                     6: '22',
                     7: '32',
                     8: '42',
                     9: '13',
                     10: '23',
                     11: '33',
                     12: '43',
                     13: '14',
                     14: '24',
                     15: '34',
                     16: '44'}

DETECTOR_ID = {val: key for key, val in NISP_DETECTOR_MAP.items()}


class DecontaminatedSpectrum:
    """
    A struct-like class for storing the decontamination products for a single spectrum.
    """
    __slots__ = ['_id',             # [str] the ID of the object.
                 '_science',        # [NumPy ndarray] The decontaminated science layer.
                 '_variance',       # [NumPy ndarray] Variance of the decontaminated science layer.
                 '_mask',           # [NumPy ndarray] Mask layer, containing decontamination flags
                 '_contamination',  # [NumPy ndarray] The total contamination for this spectrum.
                 '_contaminants',   # [NumPy ndarray] A table listing contaminants (id, order).
                 '_x_offset',       # [int] x-coordinate of the lower-left pixel of the cutout
                 '_y_offset']       # [int] y-coordinate of the lower-left pixel of the cutout

    def __init__(self):
        """
        Creates a DecontaminatedSpectrum object from a SpectrumCutout object.
        :param spectrum_cutout: a SpectrumCutout object.
        """
        self._id = None
        self._science = None
        self._variance = None
        self._mask = None
        self._contamination = None
        self._contaminants = None
        self._x_offset = None
        self._y_offset = None

    @property
    def id(self):
        """
        The ID of the object [str].
        """
        return self._id

    @id.setter
    def id(self, object_id):
        if isinstance(object_id, (int, np.int, np.uint64, np.uint64)):
            self._id = str(object_id)
        elif isinstance(object_id, str):
            self._id = object_id
        else:
            raise TypeError("Expected a string or an integer.")

    @property
    def science(self):
        """
        The decontaminated science layer [NumPy ndarray, float32].
        """
        return self._science

    @science.setter
    def science(self, sci):
        utils.verify_2d_numpy_array(sci)
        self._science = sci

    @property
    def variance(self):
        """
        Variance of the decontaminated science layer [NumPy ndarray, float32].
        """
        return self._variance

    @variance.setter
    def variance(self, var):
        utils.verify_2d_numpy_array(var)
        self._variance = var

    @property
    def mask(self):
        """
        The mask layer, containing the decontamination flags as well as the flags that were present in the original
        image [NumPy ndarray, uint32].
        """
        return self._mask

    @mask.setter
    def mask(self, mask):
        utils.verify_2d_numpy_array(mask)
        self._mask = mask

    @property
    def contamination(self):
        """
        The total contamination for this spectrum (the combined model spectra of all spectra that overlap with this
        spectrum) [NumPy ndarray, float32].
        """
        return self._contamination

    @contamination.setter
    def contamination(self, contam):
        utils.verify_2d_numpy_array(contam)
        self._contamination = contam

    @property
    def contaminants(self):
        """
        A table listing contaminants, with the columns (id, order) [NumPy ndarray, (uint64, uint8)].
        """
        return self._contaminants

    @contaminants.setter
    def contaminants(self, contams):
        self._contaminants = contams

    @property
    def x_offset(self):
        """
        The x-coordinate of the lower-left pixel of the spectral cutout [int].
        """
        return self._x_offset

    @x_offset.setter
    def x_offset(self, xoff):
        if isinstance(xoff, int):
            self._x_offset = xoff
        elif isinstance(xoff, (np.int, np.uint32, np.int32, np.uint64, np.uint64)):
            self._x_offset = int(xoff)
        else:
            raise TypeError('Expected an integer.')

    @property
    def y_offset(self):
        """
        The y-coordinate of the lower-left pixel of the spectral cutout [int].
        """
        return self._y_offset

    @y_offset.setter
    def y_offset(self, yoff):
        if isinstance(yoff, int):
            self._y_offset = yoff
        elif isinstance(yoff, (np.int, np.uint32, np.int32, np.uint64, np.uint64)):
            self._y_offset = int(yoff)
        else:
            raise TypeError('Expected an integer.')


class ModelSpectrum:
    """
    A struct-like class for storing a single model spectrum.
    """
    __slots__ = ['_id',        # [str] the ID of the object.
                 '_order',     # [int] the spectral order (1 or 2).
                 '_pixels',    # [NumPy ndarray, float32] The 2D model spectrum of the object.
                 '_x_offset',  # [int] x-coordinate of the lower-left pixel of the cutout.
                 '_y_offset']  # [int] y-coordinate of the lower-left pixel of the cutout.

    def __init__(self):
        """
        Creates a ModelSpectrum object from a SpectrumCutout object.

        Args
        ----

        spectrum_cutout: SpectrumCutout
            The spectral cutout containing the model speectrum that will be stored in this object.
        """
        self._id = None
        self._order = None
        self._pixels = None
        self._x_offset = None
        self._y_offset = None

    @property
    def id(self):
        """
        The ID of the object [str].
        """
        return self._id

    @id.setter
    def id(self, object_id):
        if isinstance(object_id, (int, np.int, np.uint64, np.uint64)):
            self._id = str(object_id)
        elif isinstance(object_id, str):
            self._id = object_id
        else:
            raise TypeError("Expected a string or an integer.")

    @property
    def order(self):
        """
        The spectral order of the model (1 or 2) [int].
        """
        return self._order

    @order.setter
    def order(self, order):
        if order not in (1, 2):
            raise ValueError("The order must be either 1 or 2.")
        self._order = order

    @property
    def pixels(self):
        """
        The 2D model spectrum of the object [NumPy ndarray, float32].
        """
        return self._pixels

    @pixels.setter
    def pixels(self, pixels):
        utils.verify_2d_numpy_array(pixels)
        self._pixels = pixels

    @property
    def x_offset(self):
        """
        The x-coordinate of the lower-left pixel of the spectral cutout [int].
        """
        return self._x_offset

    @x_offset.setter
    def x_offset(self, xoff):
        if isinstance(xoff, int):
            self._x_offset = xoff
        elif isinstance(xoff, (np.int, np.uint32, np.int32, np.uint64, np.uint64)):
            self._x_offset = int(xoff)
        else:
            raise TypeError('Expected an integer.')

    @property
    def y_offset(self):
        """
        The y-coordinate of the lower-left pixel of the spectral cutout [int].
        """
        return self._y_offset

    @y_offset.setter
    def y_offset(self, yoff):
        if isinstance(yoff, int):
            self._y_offset = yoff
        elif isinstance(yoff, (np.int, np.uint32, np.int32, np.uint64, np.uint64)):
            self._y_offset = int(yoff)
        else:
            raise TypeError('Expected an integer.')


class DecontaminatedSpectraCollection:
    """Manages a set of decontaminated spectra and models of their contaminants."""

    FILE_FORMAT_NAME = 'DecontaminatedSpectraCollection'

    DECONTAMINATED_SPECTRA_LABEL = 'Decontaminated Spectra'

    MODEL_SPECTRA_LABEL = 'Model Spectra'

    VALID_EXTENSIONS = ('h5', 'hde', 'hdf', 'hdf5', 'he5', 'json')

    def __init__(self, filename=None, parent=None):
        """
        Construct the object.

        Parameters
        ----------

        filename: str (optional)
           The full (absolute) pathname of the file that will be loaded.
        """

        self._parent = parent

        self._field_id = None

        self._exposure_time = {}  # {dither: exposure time in seconds}

        self._exposure_id = {}  # {dither: exposure ID}

        self._exposure_grism_position = {}  # {dither: grism position}

        # if the object loads one or more HDF5 files from disk, then the decontaminated spectra are stored here:
        self._hdf5_spectra = {}

        # if the object loads one or more HDF5 files from disk, then the spectral models are stored here:
        self._hdf5_models = {}

        if filename is not None:
            self.load(filename)

    @property
    def field_id(self):
        """
        The Field ID associated with the contents of this DecontaminatedSpectrum Collection
        """
        return self._field_id

    def get_dithers(self):
        """
        Lists the dithers present in this DecontaminatedSpectraCollection

        Returns:
            An iterable container of the dithers contained in the collection, as integers, 1, 2, 3, 4.
        """
        return tuple(self._hdf5_spectra.keys())

    def get_detectors(self, dither):
        """
        Lists the available detectors of the specified dither.

        Args:

            dither: an integer (1, 2, 3, 4) associated with the exposure within the dither sequence.

        Returns:

            An iterable container of the detectors of the specified dither that are present within the collection.
        """
        return tuple(self._hdf5_spectra[dither].keys())

    def get_object_ids(self, dither, detector):
        """
        Gets the IDs of the objects whose spectra appear in the specified detector of the specified dither.

        Args:

            dither: an integer (1, 2, 3, 4) associated with the exposure withing the dither sequence.

            detector: The detector of interest within the specified dither (1, ..., 16).

        Returns:

            An iterable container of IDs of objects whose decontaminated spectra located on the specified detector
        """
        return tuple(self._hdf5_spectra[dither][detector].keys())

    def get_exposure_id(self, dither):
        """
        Finds the exposure ID associated with the dither index.
        :param dither: the dither index, an integer (1, 2, 3, 4)
        :return: The exposure ID associated with the dither.
        """
        return self._exposure_id[dither]

    def get_exposure_time(self, dither):
        """
        Finds the exposure ID associated with the dither index
        :param dither: the dither index, an integer (1, 2, 3, 4)
        :return: The exposure time associated with the dither.
        """
        return self._exposure_time[dither]

    def get_grism_position(self, dither):
        """
        Finds the position of the grism for the specified dither.
        :param dither: the dither index, an integer (1, 2, 3, 4)
        :return: The grism position for the specified dither.
        """
        return self._exposure_grism_position[dither]

    def get_spectrum(self, dither, detector, object_id):
        """
        Get the DecontaminatedSpectrum object corresponding to the object with the specified ID on the specified dither
        and the specified detector.
        :param dither: The dither (exposure) in which the spectrum of interest is located (1, 2, 3, 4).
        :param detector: The detector on which the spectrum of interest is located (1, ..., 16).
        :param object_id: The ID of the object whose spectrum will be returned.
        :return: The DecontaminatedSpectrum object associated with the specified object in the specified detector of the
        specified dither (exposure) within the dither pattern.
        """
        try:
            spec = self._hdf5_spectra[dither][detector][str(object_id)]
        except KeyError:
            spec = None

        if spec is not None:
            self._compute_total_contamination(dither, detector, spec)

        return spec

    def get_spectra(self, dither, detector):
        """
        Get all of the DecontaminatedSpectrum objects cooresponding with the specified dither and detector.
        :param dither: The dither (exposure) in which the spectrum of interest is located (1, 2, 3, 4).
        :param detector: The detector on which the spectrum of interest is located (1, ..., 16).
        :return: A generator that can be iterated to obtain a DecontaminatedSpectrum object for each spectrum falling
        in the specified detector of the specified exposure.
        """
        for object_id in self.get_object_ids(dither, detector):
            yield self.get_spectrum(dither, detector, str(object_id))

    def get_model(self, dither, detector, object_id, order):
        """
        Get the model spectrum of the object in the specified detector of the specified dither with ID = object_id.
        :param dither: he dither (exposure) in which the spectrum of interest is located (1, 2, 3, 4).
        :param detector: The detector on which the spectrum of interest is located (1, ..., 16).
        :param object_id: The ID of the object whose model spectrum will be returned.
        :param order: the spectral order of the model in question.
        :return: A ModelSpectrum object containing the requested model.
        """
        if order == 0:
            raise ValueError("Models are not created for zeroth-order spectra.")
        try:
            model = self._hdf5_models[dither][detector][str(object_id)][order]
        except KeyError:
            model = None

        return model

    def load(self, filename):
        """
        Loads a DecontaminatedSpectraCollection HDF5 file or a list of files.
        :param filename: The name of the file containing the DecontaminatedSpectraCollection (if the extension is
        'h5', 'hde', 'hdf', 'hdf5', or 'he5'). If the file extension is `json`, then all files listed in the JSON file
        are loaded.
        """
        filename_extension = filename.split('.')[-1]

        self._check_filename_extension(filename_extension)

        if filename_extension == 'json':
            self._load_json(filename)
        else:
            self._load_hdf5(filename)

    def _compute_total_contamination(self, dither, detector, decontaminated_spectrum):
        """
        Compute the total contamination for a spectrum, given a DecontaminatedSpectrum object containing a list of
        contaminants.
        :param decontaminated_spectrum: A DecontaminatedSpectrum object with all fields populated except for the
        `contamination` field.
        :return: The sum of all of the contaminants of the specified spectrum.
        """
        contaminants = decontaminated_spectrum.contaminants

        x_offset = decontaminated_spectrum.x_offset

        y_offset = decontaminated_spectrum.y_offset

        total_contamination = (x_offset, y_offset), decontaminated_spectrum.contamination

        for contaminant in contaminants:
            model_id = contaminant['id']
            model_order = contaminant['order']

            if model_order != 0:  # we do not attempt to model the zeroth-order spectra
                contam = self.get_model(dither, detector, model_id, model_order)
                contaminant_flux = (contam.x_offset, contam.y_offset), contam.pixels
                utils.apply_contaminant(contaminant_flux, total_contamination)

    def _load_json(self, filename):
        """
        Loads all of the HDF5 files listed in the input JSON file.

        Args:

            filename: the fully-qualified name of a JSON file containing the names of HDF5 files produced by a
            DecontaminatedSpectraCollection.
        """
        if not os.path.isabs(filename):
            raise ValueError("The filename must include the full (absolute) path.")

        dir_name = os.path.dirname(filename)

        with open(filename) as f:
            decontaminated_spectra_collection_filenames = json.load(f)

        for f in decontaminated_spectra_collection_filenames:
            full_name = os.path.join(dir_name, 'data', f)
            if not h5py.is_hdf5(full_name):
                raise TypeError(f'{f} is not a valid HDF5 file.')

        n_files = len(decontaminated_spectra_collection_filenames)

        loop = QEventLoop()

        progress = QProgressDialog("Loading decontaminated spectra collections", None, 0, n_files, self._parent)
        plural = 'files' if n_files > 1 else 'file'
        progress.setWindowTitle(f"Loading {n_files} decontaminated spectra {plural}")
        progress.setModal(True)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()

        loop.processEvents()

        for i, decontaminated_spectra_filename in enumerate(decontaminated_spectra_collection_filenames):
            status_message = f'loading {decontaminated_spectra_filename}'
            progress.setLabelText(status_message)
            progress.setValue(i)
            loop.processEvents()
            full_name = os.path.join(dir_name, 'data', decontaminated_spectra_filename)

            self._load_hdf5(full_name)

            progress.setValue(i + 1)
            loop.processEvents()

        progress.close()

    def _load_hdf5(self, filename):
        """
        Loads the contents of a single HDF5 file into this DecontaminatedSpectraCollection object.

        Args:

            filename: The fully-qualified name of an HDF5 file containing a DecontaminatedSpectraCollection for one
            NISP detector.
        """

        if not h5py.is_hdf5(filename):
            raise ValueError(f"{filename} is not a valid DecontaminatedSpectrumCollection file.")

        h5_file = h5py.File(filename, 'r')

        # a few sanity checks:

        if h5_file.attrs['file_format'] != DecontaminatedSpectraCollection.FILE_FORMAT_NAME:
            raise ValueError(f"{filename} is not a valid DecontaminatedSpectrumCollection file.")

        dither = h5_file.attrs[DITHER_LABEL]

        if dither < 1 or dither > 4:
            raise ValueError(f'The value, dither={dither}, is unexpected')

        detector = h5_file.attrs['Detector']

        if detector < 1 or detector > 16:
            raise ValueError(f'The detector value, {detector}, is out of the expected range.')

        exposure_time = h5_file.attrs['exp_time']

        if exposure_time <= 0.0:
            raise ValueError(f'The exposure time must be > 0.0 seconds.')

        self._exposure_time[dither] = exposure_time

        self._exposure_grism_position[dither] = h5_file.attrs[GRISM_POSITION_LABEL]

        self._exposure_id[dither] = h5_file.attrs[EXPOSURE_ID_LABEL]

        field_id = h5_file.attrs[FIELD_ID_LABEL]

        if self._field_id is not None:
            if self._field_id != field_id:
                raise ValueError("Encountered a new field ID; The DecontaminatedSpectraCollection can only "
                                 "contain spectra from a single field.")
        else:
            self._field_id = field_id

        self._load_spectra_from_hdf5(h5_file)
        self._load_models_from_hdf5(h5_file)

    def _load_spectra_from_hdf5(self, hdf5_file):
        dither = hdf5_file.attrs[DITHER_LABEL]
        detector = hdf5_file.attrs['Detector']

        spectra = hdf5_file[DecontaminatedSpectraCollection.DECONTAMINATED_SPECTRA_LABEL]

        for object_id in spectra:
            spectrum = spectra[object_id]
            self._load_spectrum_from_hdf5_group(spectrum, dither, detector)

    def _load_models_from_hdf5(self, hdf5_file):
        dither = hdf5_file.attrs[DITHER_LABEL]
        detector = hdf5_file.attrs['Detector']

        models = hdf5_file[DecontaminatedSpectraCollection.MODEL_SPECTRA_LABEL]

        for object_id in models:
            object_models = models[object_id]
            for order in object_models:
                model = object_models[order]
            self._load_model_from_hdf5_dataset(model, dither, detector, object_id)

    def _load_spectrum_from_hdf5_group(self, group, dither, detector):
        """Adds decontaminated spectra, loaded from an HDF5 file, to the appropriate container."""
        if dither not in self._hdf5_spectra:
            self._hdf5_spectra[dither] = {}

        if detector not in self._hdf5_spectra[dither]:
            self._hdf5_spectra[dither][detector] = {}

        object_id = group.attrs['object_id']

        # now create the LocationSpectrum and DecontaminatedSpectrum objects, filling in the attributes, making
        # sure to convert to the correct data type.

        spec = DecontaminatedSpectrum()

        spec.id = object_id
        spec.x_offset = int(group.attrs['x_offset'])
        spec.y_offset = int(group.attrs['y_offset'])
        spec.science = np.array(group['science'])
        spec.variance = np.array(group['variance'])
        spec.mask = np.array(group['mask'])
        spec.contaminants = np.array(group['contaminants'])
        spec.contamination = np.zeros_like(spec.science)

        self._hdf5_spectra[dither][detector][object_id] = spec

    def _load_model_from_hdf5_dataset(self, dataset, dither, detector, object_id):
        """Adds a single model, loaded from the HDF5 file, to the appropriate container."""
        if dither not in self._hdf5_models:
            self._hdf5_models[dither] = {}

        if detector not in self._hdf5_models[dither]:
            self._hdf5_models[dither][detector] = {}

        if object_id not in self._hdf5_models[dither][detector]:
            self._hdf5_models[dither][detector][object_id] = {}

        order = dataset.attrs['order']

        spec = ModelSpectrum()

        spec.id = object_id
        spec.order = order
        spec.pixels = np.array(dataset)
        spec._x_offset = dataset.attrs['x_offset']
        spec._y_offset = dataset.attrs['y_offset']

        self._hdf5_models[dither][detector][object_id][order] = spec

    @staticmethod
    def _check_filename_extension(filename_extension):
        """
        Checks that the filename extension (suffix) is among the allowed extensions. If it is not, then a ValueError
        exception is raised.
        """
        if filename_extension not in DecontaminatedSpectraCollection.VALID_EXTENSIONS:
            raise ValueError("The file extension (suffix) must be one of "
                             f"{DecontaminatedSpectraCollection.VALID_EXTENSIONS}.")


class ObjectInfo:
    __slots__ = ['id',
                 'ra',
                 'dec',
                 'jmag',
                 'hmag',
                 'color',
                 'angle',
                 'type',
                 'major_axis',
                 'minor_axis']

    def __init__(self):
        self.id = None
        self.ra = None
        self.dec = None
        self.jmag = None
        self.hmag = None
        self.color = None
        self.angle = None
        self.type = None
        self.major_axis = None
        self.minor_axis = None


class LocationTable:
    """
    A class for loading data stored in location tables that is not stored in the DecontaminatedSpectraCollection class.
    """
    def __init__(self, filename=None, parent=None):

        self._location_tables = []

        self._info = {}  # {id: object_info}

        self._parent = parent

        if isinstance(filename, str):
            self.load_json(filename)
        elif isinstance(filename, list):
            self.load_hdf5_files(filename)
        else:
            raise TypeError('Expected a JSON filename or a list of HDF5 filenames.')

    def load_json(self, filename):
        if not os.path.isabs(filename):
            raise ValueError("The filename must include the full (absolute) path.")

        dir_name = os.path.dirname(filename)

        with open(filename) as f:
            location_tables = json.load(f)

        filenames = [os.path.join(dir_name, 'data', f) for f in location_tables]

        self.load_hdf5_files(filenames)

    def load_hdf5_files(self, filenames):
        n_files = len(filenames)

        for f in filenames:
            if not h5py.is_hdf5(f):
                raise TypeError(f'{f} is not a valid HDF5 file.')

        loop = QEventLoop()

        progress = QProgressDialog("Loading location tables", None, 0, n_files, self._parent)
        plural = 'files' if n_files > 1 else 'file'
        progress.setWindowTitle(f"Loading {n_files} location table {plural}")
        progress.setModal(True)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()

        loop.processEvents()

        for i, filename in enumerate(filenames):
            status_message = f'loading {filename}'
            progress.setLabelText(status_message)
            progress.setValue(i)
            loop.processEvents()

            self.load_hdf5(filename)

            progress.setValue(i + 1)
            loop.processEvents()

        progress.close()

    def load_hdf5(self, filename):

        f = h5py.File(filename)

        self._location_tables.append(f)

        for object_id in f['Location Objects']:

            info = f[f'Location Objects/{object_id}/Astronomical Object']

            metadata = info.attrs

            object_info = ObjectInfo()

            if 'Magnitudes' in info:
                mags = np.array(info['Magnitudes'])

                for entry in mags:
                    band = entry['Band']
                    mag = entry['Value']
                    if band == b'H' or band == 'H':
                        object_info.hmag = mag
                    elif band == b'J' or band == 'J':
                        object_info.jmag = mag

            object_info.id = object_id
            object_info.color = metadata['Color'] if 'Color' in metadata else None
            object_info.angle = metadata['Angle'] if 'Angle' in metadata else None
            object_info.type = metadata['Type'] if 'Type' in metadata else None
            object_info.ra = metadata['RA'] if 'RA' in metadata else None
            object_info.dec = metadata['Dec'] if 'Dec' in metadata else None
            object_info.major_axis = metadata['Major axis'] if 'Major axis' in metadata else None
            object_info.minor_axis = metadata['Minor axis'] if 'Minor axis' in metadata else None

            self._info[object_id] = object_info

    def get_info(self, object_id):
        return self._info[object_id]



