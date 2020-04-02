# Optimizer.py
# by Robin Prillwitz
# 2.4.2020
#

import Config
import Process
import Cursor
import numpy as np
import pandas as pd
from PyQt5 import QtTest, QtCore, QtWidgets
from scipy.signal import find_peaks
from scipy.optimize import minimize

def __exceedesLimit(data, limit):
    return (np.where(data["y"] > limit))[0].size > 0

def __error(compound, limit):
    maximum = np.amax(compound["y"])
    error = maximum - limit
    return error

# TODO Replace all print Statements with error messages
def optimizeTime(lst):

    limitCursor = None
    compound_data = None

    for item in lst.fileList.list:
        if isinstance(item, Cursor.Cursor):
            if limitCursor == None:
                limitCursor = item
            else:
                print("Found multiple Cursors on the top-level, using the first one")
        elif isinstance(item, Process.Process):
            if compound_data == None:
                # treating all items in top-level process as datafiles to be optimized
                compound_data = item
            else:
                print("Found multiple Processes, ignoring all but the first one")
        else:
            print("Datafiles outside of processes donot interact with any plots and will be ignored")

    if limitCursor == None:
        print("Could not find limiting Cursor on top-level")
        return

    if compound_data == None:
        print("Could not find Processes")
        return

    maxLimit = limitCursor.config["yOffset"]

    print(limitCursor, maxLimit)
    print(compound_data)

    # TODO algorithm(?)/brute-force time optimization
    # maybe add a popup dialog / waiting spinner depending on runtime
    # also clean this up

    # # check if compound actually exceedes limit
    # compound_peaks, _ = find_peaks(compound_data.interpData["y"])
    # exceedes_limit = False
    # for peak in compound_peaks:
    #     print("x: ", compound_data.interpData["x"][peak], "y: ", compound_data.interpData["y"][peak])
    #     if compound_data.interpData["y"][peak] > maxLimit:
    #         exceedes_limit = True

    if __exceedesLimit(compound_data.interpData, maxLimit) == 0:
        print("Compound doesnot exceed limit at any point, no optimization needed")
        return

    iteration = 0
    s = 1
    if __error(compound_data.interpData, maxLimit) > 0:
        while __error(compound_data.interpData, maxLimit) > 0:
            compound_data.fileList.list[0].config["xOffset"] += s
            compound_data.fileList.list[0].update()
            QtTest.QTest.qWait(25)
            iteration += 1
            if iteration > 100:
                print("Iteration limit reached, aborting")
                return
    else:
        while __error(compound_data.interpData, maxLimit) < 0:
            compound_data.fileList.list[0].config["xOffset"] -= s
            compound_data.fileList.list[0].update()
            QtTest.QTest.qWait(25)
            iteration += 1
            if iteration > 100:
                print("Iteration limit reached, aborting")
                return

    print("Rough guess finished after ", iteration, "iterations")

    # function(compound_data.fileList.list[0].config["xOffset"], compound_data, maxLimit)

    # res = minimize(function, compound_data.fileList.list[0].config["xOffset"],
    #                     args=(compound_data, maxLimit), method='Nelder-Mead',
    #                     options={'disp': True}, tol=1e-6)

    # print(res)
    # print("remaining error: ", __error(compound_data.interpData, maxLimit) )

    aoi = compound_data.fileList.list[0].config["xOffset"]

    x = np.linspace(
        aoi - 1,
        aoi + 1,
        int(np.ceil(
            (2 / Config.DIVISION) * Config.PPD))
        )
    y = np.full(len(x), 0.0)

    for i, val in enumerate(x):
        compound_data.fileList.list[0].config["xOffset"] = val
        compound_data.fileList.list[0].update()
        y[i] = abs(__error(compound_data.interpData, maxLimit))

    minIdx = np.where(y == y.min())[0][0]

    compound_data.fileList.list[0].config["xOffset"] = x[minIdx]
    compound_data.fileList.list[0].update()

    # df = pd.DataFrame({"x": x, "y": y})
    # df.to_csv("./error.csv", encoding='utf-8', index=False)
