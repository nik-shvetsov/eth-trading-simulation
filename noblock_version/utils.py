from ethereum import utils as ethereum_utils
from ethereum import tester
import numpy as np
from scipy.interpolate import spline
import matplotlib.pyplot as plt


# removes 0x prefix
def strip_0x(value):
    if value and value.startswith("0x"):
        return value[2:]
    return value


def encode_hex(value):
    return "0x" + ethereum_utils.encode_hex(value)


def buildGraph(households, datadict, ylabel, title, grid):
    for house in households:
        dataList = datadict[house.address]
        x = np.arange(0, len(dataList))
        y = dataList
        plt.plot(x, y, label=house.address)

    plt.xlabel("Time (hours)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(grid)
    name = title + ".png"
    plt.savefig(name)
    plt.legend()
    plt.show()


def buildSmoothXY(xlist, ylist):
    x = np.array(xlist)
    y = np.array(ylist)

    x_s = np.linspace(x.min(), x.max(), 300)
    y_s = spline(x, y, x_s)

    return (x_s, y_s)


def generateAdresses(number):
    number += 1
    listAdr = []
    for x in range(number):
        item = "0x" + str(x)
        listAdr.append(item)
    return listAdr
