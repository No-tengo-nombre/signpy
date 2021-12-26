import numpy as np

from signpy.sgn import Signal1


def w_rectangular(samp_time):
    epsilon = 0.01
    axis = [-samp_time / 2 - epsilon, -samp_time / 2, samp_time + epsilon]
    values = [0, 1, 1, 0]
    return Signal1(axis, values)


def w_gaussian(samp_time, resolution=100):
    axis = np.linspace(-samp_time / 2, samp_time / 2, resolution)
    values = np.exp(-(axis ** 2) / (2 * samp_time ** 2)) / \
        np.sqrt(2 * np.pi * samp_time ** 2)
    return Signal1(axis, values)
