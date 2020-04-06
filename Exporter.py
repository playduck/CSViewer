# ListItem.py
# by Robin Prillwitz
# 4.4.2020
#

from PyQt5 import QtGui, QtCore, QtWidgets
import pandas as pd
import numpy as np
from scipy.io import wavfile
from scipy.interpolate import interp1d
import wave
import Config

def __getFileType(export):
        if "Interpolation" in export or "Modifikation" in export:
            return "CSV Datei (*.csv);;Alle Dateinen (*)"
        elif "Wave" in export:
            return "Wave Datei (*.wav);;Alle Dateinen (*)"

def __saveDialog(filetype):
    options = QtWidgets.QFileDialog.Options()
    filename, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Export", "",
                    filetype, options=options)
    return filename

# function based on
# https://stackoverflow.com/a/41586167/12231900
def __exportWave(data, filename):
    SMPLS = 8000
    # resample values with same algorithms to match sampling rate
    xnew = np.linspace(
        data.interpData["x"].min(), # from
        data.interpData["x"].max(), # to
        int(
            np.ceil(((data.interpData["x"].max() - data.interpData["x"].min()) / Config.DIVISION) * SMPLS)
        )
    )
    spl = interp1d(data.interpData["x"], data.interpData["y"], kind=data.config["interpolation"], copy=True,
            assume_sorted=True, bounds_error=False, fill_value=0)

    # normalize values to -1.0 to 1.0
    arr = spl(xnew)
    arr = np.divide(arr, np.max(np.abs(arr)))

    # upscale values to 16 bits
    amplitude = np.iinfo(np.int16).max
    arr = np.multiply(arr, amplitude)
    # samples only go from -(2**15) to (2**15)
    # => missing one possible value at (2**15)-1

    # convert for 16 bit PCM
    data_resampled = arr.astype(np.int16)

    wavfile.write(filename, SMPLS, data_resampled)


def export(data, export):
    print(export)
    filename = __saveDialog(__getFileType(export))

    if filename:
        if "Interpolation" in export:
            pd.DataFrame(data.interpData).to_csv(filename,sep=Config.SEPERATOR, decimal=Config.DECIMAL, encoding='utf-8', index=False)
        elif "Modifikation" in export:
            pd.DataFrame(data.modData).to_csv(filename,sep=Config.SEPERATOR, decimal=Config.DECIMAL, encoding='utf-8', index=False)
        elif "Wave" in export:
            __exportWave(data, filename)
