from scipy.integrate import simps
from scipy.signal import medfilt
from math import erf, sqrt
import numpy as np

from PyQt5.QtGui import QImage, QPixmap


c_AA = 2.99792458e18  # the speed of light in Angstroms per second


def div0(a, b):
    """ Computes a / b, ignoring division by zero: div0( [-1, 0, 1], 0 ) -> [0, 0, 0] """
    with np.errstate(divide='ignore', invalid='ignore'):
        c = np.true_divide(a, b)
        c[~ np.isfinite(c)] = 0  # -inf inf NaN
    return c


def mag_to_fnu(mag, zero_point):
    """
    Convert from magnitude and zero-point to F_nu.
    :param mag: an AB magnitude
    :param zero_point: The zero point used for converting the magnitude to the desired flux unit.
    :return: The flux, as F_nu, in the physical unit that corresponds with the zero-point value provided.
    """
    return pow(10, 0.4 * (zero_point - mag))


def angstrom_to_mjy(flux, wavelength):
    """
    Convert a flux value, from erg/s/cm^2/AA, at specified wavelength, to microJanskys
    :param flux: a flux (or fluxes if a NumPy array is provided) in units of erg/s/cm^2/AA.
    :param wavelength: The wavelength value (or values, if an array is provided), in units of Angstroms.
    :return: flux in units of microJanskys.
    """
    w2 = wavelength * wavelength  # Angstrom^2
    return w2 * flux / (1e-29 * c_AA)  # \mu Jy


def mjy_to_angstrom(flux, wavelength):
    """
    Convert a flux value, from microJanskys, at specified wavelength, to erg/s/cm^2/AA
    :param flux: a flux (or fluxes if a NumPy array is provided) in units of microJanskys.
    :param wavelength: The wavelength value (or values, if an array is provided), in units of Angstroms.
    :return: flux in units of erg/s/cm^2/AA.
    """
    w2 = wavelength * wavelength  # Angstrom^2
    return 1e-29 * flux * c_AA / w2  # erg/s/cm^2/A


def effective_wavelength(transmission, wavs):
    """
    Computes the effective wavelength of a filter
    :param transmission: The transmission of the filter.
    :param wavs: The wavelengths corresponding to the transmission values.
    :return: The weighted average wavelength of the filter (the effective wavelength).
    """
    weighted_wav = simps(transmission * wavs, wavs)
    total_weight = simps(transmission, wavs)
    return weighted_wav / total_weight


def interp_multiply(w1, data1, w2, data2):
    """
    Returns the vector data1 * data2 after interpolating data2 to the same wavelength
    bins as data1. The relevant wavelengths of the output vector are the wavelengths
    of the first vector (w1).
    """
    # interpolate data series 2 to find the values at the points, w1:
    data2_interp = np.interp(w1, w2, data2)
    return data2_interp * data1


def convolve_filter(wavelengths, fluxes, filter_wavs, filter_transmissions):
    """
    Integrates a filter_transmission profile against a spectrum to obtain the flux of the bandpass.
    :param wavelengths: wavelenghts of the spectrum
    :param fluxes: the flux densities of the spectrum
    :param filter_wavs:
    :param filter_transmissions:
    :return: the flux at the filter's effective wavelength.
    """
    integrand = interp_multiply(filter_wavs, filter_transmissions, wavelengths, fluxes)

    return simps(integrand, filter_wavs) / simps(filter_transmissions, filter_wavs)


def smooth_signal(signal, window_width):
    """
    Performs a smothing operation on an input signal by computing the moving average in a region of width equal
     to `window_width`.
    """
    window = np.ones(window_width)
    window = window / window.sum()

    return np.convolve(signal, window, mode='same')


def find_spikes(signal, spike_width, noise_sigma, padding):
    """
    Locates regions of a signal that exceed the local mean by 3 times teh noise level, indicated by `noise_sigma`.

    Parameters
    ----------

    signal: 1D NumPy array
        Contains the raw signal (for instance the sums of the columns of a 2D spectral cutout or a time series)

    spike_width: int
        The expected width of the spike in the signal.

    noise_sigma: float
        The expected standard deviation of the noise in the signal, in the absence of any spikes.

    padding: int
        The number of samples to the left and right of the spike that should be included

    Returns
    -------

    array-like
        A list of integer indices corresponding to the locations of spikes in the signal. This includes the
        central position of the spike as well as +/- padding samples to the left and right of the spike.
    """

    if spike_width < 1:
        raise ValueError('spike_width must be >= 1.')

    # perform median filtering to smooth the signal.

    width = 3 * spike_width

    # the kernel size for the median filter has to be odd, so:

    kernel_size = width + 1 if width % 2 == 0 else width

    smoothed_signal = medfilt(signal, kernel_size)

    # identify regions in which the signal exceeds the the smoothed signal by 3 sigma

    spike = (signal - smoothed_signal) > 3 * noise_sigma

    conv_kernel = np.ones(spike_width) / spike_width

    spike_indices = np.where(np.convolve(spike, conv_kernel, mode='same') == 1)[0]

    if len(spike_indices) == 0:
        return np.array([])

    indices = set()

    imin = spike_width + 1
    imax = len(signal) - spike_width

    for idx in spike_indices:
        ileft = max(imin, idx - padding)
        iright = min(imax, idx + padding)
        for i in range(ileft, iright):
            indices.add(i)

    return np.array(list(indices))


def cdf(x, mu, sigma):
    """
    The Gaussian cumulative distribution function.

    Computes the integral of the Gaussian distribution centered at mu and with sigma, from negative infinity to x"""
    return 0.5 * (1.0 + erf((x - mu) / (sqrt(2) * sigma)))


def prob_in_range(lower, upper, mu, sigma):
    """
    Computes the probability between x = lower and x = upper of the Gaussian, centered at x = mu.
    :param lower: The lower limit of the integral.
    :param upper: The upper limit of the integral
    :param mu: The mean (central) position of the Gaussian distribution
    :param sigma: The standard deviation of the Gaussian distribution
    :return: The integral of the Gaussian distribution between x = lower to x = upper.
    """
    return cdf(upper, mu, sigma) - cdf(lower, mu, sigma)


def gauss_kernel(canvas, center, sigma):
    """
    Computes a 2D Gaussian, centered at `center`.
    :param canvas: A square 2D NumPy array in which the 2D Gaussian kernel will be painted.
    :param center: The pixel coordinates (x, y) of the center of the kernel.
    :param sigma: The semi-major axes of the resulting elliptical Gaussian kernel.
    :return: A 2D NumPy array containing the
    """
    y_res, x_res = canvas.shape

    if y_res != y_res:
        raise ValueError("The image must be square.")

    res = x_res

    center_x, center_y = center

    center_x += 0.5
    center_y += 0.5

    semimajor_axis, semiminor_axis = sigma

    if semiminor_axis > semimajor_axis:
        raise ValueError("The semi-major axis must equal to or larger than that the semi-minor axis.")

    # compute the total mass in each row of the array

    row_sum = np.zeros(res)

    for j in range(res):
        row_sum[j] = prob_in_range(j, j + 1.0, center_y, semiminor_axis)

    # compute the 1D kernel that will be used for distributing the light along the major axis

    row_kernel = np.zeros(res)

    for i in range(res):
        row_kernel[i] = prob_in_range(i, i + 1.0, center_x, semimajor_axis)

    # compute the value of each pixel:

    for j in range(res):
        row = canvas[j]
        for i in range(res):
            row[i] = row_kernel[i] * row_sum[j]

    return canvas


def verify_2d_numpy_array(arg):
    """
    Checks whether the argument, `arg`, is a 2-dimensional NumPy array.
    :param arg: the object whose type is being inspected

    Raises: a TypeError if `arg` is not a 2-dimensional NumPy array.
    """
    if not isinstance(arg, np.ndarray) or arg.ndim != 2:
        raise TypeError(f"Expected a 2-dimensional NumPy array. Encountered type {type(arg)}.")


def bounding_indices(box1, box2):
    """
    Computes the bounding indices of the region of overlap of two boxes_visible.
    box1: A tuple of (left, bottom, width, height)
    box2: A tuple of (left, bottom, width, height)
    Returns: two tuples: (left1, bottom1, right1, top1), (left2, bottom2, right2, top2) which are the bounding
    indices of the area of overlap in the coordinate system of box1 and the coordinate system of box2, respectively.
    """

    left1, bottom1, width1, height1 = box1
    left2, bottom2, width2, height2 = box2

    # the offset between the corners of the two boxes_visible is:

    x_offset = left1 - left2
    y_offset = bottom1 - bottom2

    # the coordinates of box1's boundaries, in the coordinate system of box2 are:

    left = x_offset  # 0 + x_offset
    bottom = y_offset  # 0 + y_offset
    right = width1 + x_offset
    top = height1 + y_offset

    # clip the boundaries so that we are limited to the region within box2:

    left2 = max(0, left)
    bottom2 = max(0, bottom)
    right2 = min(width2, right)
    top2 = min(height2, top)

    # the coordinates of the region of overlap, in the coordinate system of box1:

    left1 = max(0, left2 - x_offset)
    right1 = min(width1, right2 - x_offset)
    bottom1 = max(0, bottom2 - y_offset)
    top1 = min(height1, top2 - y_offset)

    boxes_intersect = left1 < right1 and bottom1 < top1 and left2 < right2 and bottom2 < top2

    if boxes_intersect:
        return (left1, bottom1, right1, top1), (left2, bottom2, right2, top2)
    else:
        # the boxes_visible do not intersect.
        return None, None


def apply_contaminant(contaminant_flux, total_contamination):
    """
    Add the contaminant_flux due to a single contaminant to a canvas.
    total_contamination: a tuple of (offset, 2D array), where the offset is a tuple of (left, bottom) specifying the
    position of the lower-left pixel of the array within the detector and the 2D array contains the accumulated
    contaminant_flux.
    contaminant_flux: a tuple of (offset, 2D array), where the offset is a tuple of (left, bottom) specifying the
    position of the lower-left pixel of the array within the detector and the 2D array contains the model spectrum
    of a contaminant.
    """

    (contam_left, contam_bottom), contam = contaminant_flux
    (canvas_left, canvas_bottom), canvas = total_contamination

    contam_height, contam_width = contam.shape
    canvas_height, canvas_width = canvas.shape

    contam_box = (contam_left, contam_bottom, contam_width, contam_height)
    canvas_box = (canvas_left, canvas_bottom, canvas_width, canvas_height)

    contam_boundaries, canvas_boundaries = bounding_indices(contam_box, canvas_box)

    if contam_boundaries is None or canvas_boundaries is None:
        # the contaminant does not intersect the canvas
        return

    contam_left, contam_bottom, contam_right, contam_top = contam_boundaries
    can_left, can_bottom, can_right, can_top = canvas_boundaries

    canvas[can_bottom:can_top, can_left:can_right] += contam[contam_bottom:contam_top, contam_left:contam_right]


def to_bytes(im, maxval=None):
    """
    Scales the input image to fit the dynamic range between 0 and 255, inclusive. Then returns
    the array as an array of bytes (a string).
    """
    if maxval is None:
        maxval = im.max()

    data = (im - im.min()) / (maxval - im.min())
    counts, bins = np.histogram(data.flatten(), bins=300)
    scale_factor = 0.017 / bins[1 + counts.argmax()]
    scaled = 2 * 350 * scale_factor * (np.arctan(1.1e6 * data.astype(np.float32) / maxval) / np.pi)
    scaled -= np.percentile(scaled, 0.05)
    counts, bins = np.histogram(scaled.flatten(), bins=300, range=(0, 300))
    scale_factor2 = 44.0 / bins[1 + counts.argmax()]
    scaled *= scale_factor2
    #plt.hist(scaled.flatten(), bins=128, log=True, histtype='step')
    clipped = np.clip(scaled, 0, 255)
    return clipped.astype(np.uint8).flatten().tobytes()


def np_to_pixmap(array, maxval):
    height, width = array.shape
    image_bytes = to_bytes(array, maxval)
    image = QImage(image_bytes, width, height, width, QImage.Format_Grayscale8)
    return QPixmap(image)