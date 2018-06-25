# InSpector

InSpector is a GUI tool for inspecting the output of the SIR Spectra Decontamination module.

## Requirements

InSpector is written in Python 3.6. In addition to Python 3.6, it requires:

* NumPy
* MatPlotLib
* SciPy
* AstroPy
* H5Py
* PyQt5

Once Python 3.6 is installed, you simply need to use `pip` (which may be named `pip3` or `pip3.6`)
to install the dependencies:

```
$ sudo pip3 install numpy matplotlib scipy astropy h5py pyqt5
```

## Usage

1. start the program
2. use the `File` menu to load the images and the decontaminated spectra collections.
3. Right click in the viewer to see what options are avalable in the context menu. The rest should be fairly self-explanatory.

A brief overview, in video form, can be found here: https://youtu.be/t2A8dfkF6oQ


## Brief Code Overview

The code is currently organized into the following files:

* `inspector.py` is the executable file. It also contains the main class, `Inspector`.
* `view_tab.py` contains the `ViewTab` class, which is responsible for creating the detector view tabs.
  - `spec_box.py` contains the `SpecBox` class, which creates the rectangular spectra selection boxes in the detector view tab.
  - `spec_table.py` contains the `SpecTable` class, which is used to display the table of contaminating spectra.
* `object_tab.py` contains the `ObjectTab` class and a few supporting classes. This code is responsible for creating the object info tabs.
  - `detector_selector.py` contains the `MultiDitherDetectorSelector` class and associated classes, which create the detector selection
     region in the left side of the object info tab. 
* `plot_window.py` contains the `PlotWindow` class, which is esentially a wrapper around a MatPlotLib figure, with added features.
  - `syntax.py` contains the Python syntax highlighting code, used by the code box that appears within the `PlotWindow`.
* `info_window.py` contains the `ObjectInfoWindow` and `DetectorInfoWindow` classes that are used to diplay information.
* `reader.py` contains the classes that are needed in order to read the `DecontaminatedSpectraCollections` and the `LocationTable`s.
* `utils.py` contains an assortment of miscellaneous helper functions for converting units, performing common operations.

