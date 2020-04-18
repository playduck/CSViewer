# ListItem.py
# by Robin Prillwitz
# 4.4.2020
#

from PyQt5 import QtGui, QtCore, QtWidgets, uic
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

class __exportWave(QtWidgets.QDialog):
    def __init__(self, data, filename):
        super().__init__()
        uic.loadUi(Config.getResource("./ui/wav_save_dialog.ui"), self)
        sr = self.findChild(QtWidgets.QSpinBox, "sample_rate")
        bps = self.findChild(QtWidgets.QComboBox, "bits_per_sample")
        sr.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)

        ret = self.exec_()
        if ret:
            self.__export(data, filename, sr.value(), bps.currentText())

    # function based on
    # https://stackoverflow.com/a/41586167/12231900
    def __export(self, data, filename, samplingRate, bitsPerSample):
        if "8-Bit PCM" in bitsPerSample:
            dtype = np.uint8
        elif "16-Bit PCM" in bitsPerSample:
            dtype = np.int16
        elif "32-Bit floating" in bitsPerSample:
            dtype = np.int32
        else:
            print("wave ui combobox exposes unsuportetd bps setting (", bitsPerSample ,")")
            return

        # resample values with same algorithms to match sampling rate
        xnew = np.linspace(
            data.interpData["x"].min(), # from
            data.interpData["x"].max(), # to
            int(np.ceil((
                (data.interpData["x"].max() - data.interpData["x"].min())
                 / Config.DIVISION) * samplingRate)
            )
        )
        spl = interp1d(data.interpData["x"], data.interpData["y"], kind=data.config["interpolation"], copy=True,
                assume_sorted=True, bounds_error=False, fill_value=0)

        # normalize values to -1.0 to 1.0
        arr = spl(xnew)
        arr = np.divide(arr, np.max(np.abs(arr)))

        amplitude = np.iinfo(dtype).max

        if dtype == np.dtype(np.uint8).type:
            arr = np.add(arr, 1)
            amplitude = amplitude // 2

        arr = np.multiply(arr, amplitude)
        # samples only go from -(2**15) to (2**15) for 16-Bit PCM for example
        # => missing one possible value at (2**15)-1

        # convert to data type
        data_resampled = arr.astype(dtype)

        wavfile.write(filename, samplingRate, data_resampled)


def export(data, export):
    filename = __saveDialog(__getFileType(export))

    if filename:
        if "Interpolation" in export:
            pd.DataFrame(data.interpData).to_csv(filename,sep=Config.SEPERATOR, decimal=Config.DECIMAL, encoding='utf-8', index=False)
        elif "Modifikation" in export:
            pd.DataFrame(data.modData).to_csv(filename,sep=Config.SEPERATOR, decimal=Config.DECIMAL, encoding='utf-8', index=False)
        elif "Wave" in export:
            exp = __exportWave(data, filename)
            del exp
