# InSpector

InSpector is a GUI tool for inspecting the output of the SIR Spectra Decontamination module.

## Requirements

InSpector is written in Python 3.6. In addition to Python 3.6, it requires:

* NumPy
* MatPlotLib
* H5Py
* PyQt5

Once Python 3.6 is installed, you simply need to use `pip` (which may be named `pip3` or `pip3.6`)
to install the dependencies:

```
$ sudo pip3 install numpy matplotlib h5py pyqt5
```

## Usage

1. start the program
2. use the `File` menu to load the images and the decontaminated spectra collections.
3. Right click in the viewer to see what options are avalable in the context menu. The rest should be fairly self-explanatory.
