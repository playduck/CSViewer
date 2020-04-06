# ListItem.py
# by Robin Prillwitz
# 4.4.2020
#

from PyQt5 import QtGui, QtCore, QtWidgets
import pandas as pd
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample
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
    # normalize values to -1.0 to 1.0
    arr = np.array(data.interpData["y"])
    arr = np.divide(arr, np.max(np.abs(data.interpData["y"])))

    # upscale values to 16 bits
    amplitude = np.iinfo(np.int16).max
    arr = np.multiply(arr, amplitude)
    # samples only go from -(2**15) to (2**15)
    # => missing one possible value at (2**15)-1

    # resample values, otherwise length wont match (?)
    data_resampled = resample( arr, len(data.interpData["y"]) )
    # convert for 16 bit PCM
    data_resampled = data_resampled.astype(np.int16)

    wavfile.write(filename, 44100, data_resampled)


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
