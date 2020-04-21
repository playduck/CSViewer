# ListItem.py
# by Robin Prillwitz
# 4.4.2020
#

from PyQt5 import QtGui, QtCore, QtWidgets, uic
import pyqtgraph as pg
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
        normalize = self.findChild(QtWidgets.QCheckBox, "normalize")
        sr.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)

        ret = self.exec_()
        if ret:
            self.__export(data, filename, normalize.isChecked(), sr.value(), bps.currentText())

    # function based on
    # https://stackoverflow.com/a/41586167/12231900
    def __export(self, data, filename, normalize, samplingRate, bitsPerSample):
        dlg = pg.ProgressDialog("Exportieren", busyCursor=True, wait=0, disable=False)

        if "8-Bit PCM" in bitsPerSample:
            dtype = np.uint8
        elif "16-Bit PCM" in bitsPerSample:
            dtype = np.int16
        elif "32-Bit floating" in bitsPerSample:
            dtype = np.int32
        else:
            print("wave ui combobox exposes unsuportetd bps setting (", bitsPerSample ,")")
            return
        dlg += 10

        # resample values with same algorithms to match sampling rate
        xnew = np.linspace(
            data.interpData["x"].min(), # from
            data.interpData["x"].max(), # to
            int(np.ceil((
                (data.interpData["x"].max() - data.interpData["x"].min())
                 / Config.DIVISION) * samplingRate)
            )
        )
        dlg += 10

        spl = interp1d(data.interpData["x"], data.interpData["y"], kind=data.config["interpolation"], copy=True,
                assume_sorted=True, bounds_error=False, fill_value=0)
        dlg += 10

        arr = spl(xnew)
        dlg += 10

        amplitude = np.iinfo(dtype).max
        if np.max(np.abs(arr)) > amplitude:
            print("wave max value exceedes bps range (", np.max(np.abs(arr)), ">", amplitude, ")" )
            return

        if normalize:
            divide = np.max(np.abs(arr)) # scale to max range
        else:
            divide = 1000 #mA
            # scale to 1A maximum as per import into ltspice

        # normalize values to -1.0 to 1.0
        arr = np.divide(arr, divide)
        dlg += 5

        if dtype == np.dtype(np.uint8).type:
            arr = np.add(arr, 1)
            amplitude = amplitude // 2

        arr = np.multiply(arr, amplitude)
        dlg += 5
        # samples only go from -(2**15) to (2**15) for 16-Bit PCM for example
        # => missing one possible value at (2**15)-1

        if dtype != np.dtype(np.float).type:
            arr = np.round(arr, 0)

        # convert to data type
        data_resampled = arr.astype(dtype)
        dlg += 10

        wavfile.write(filename, samplingRate, data_resampled)
        dlg.setValue(100)


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
