from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
from tqdm import tqdm

from signpy.config import S1_METHOD, S2_METHOD
if TYPE_CHECKING:
    from signpy.sgn import Signal1, Signal2

########################################################################################################################
# |||||||||||||||||||||||||||||||||||||||||||||||| Signal1 ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||| #
########################################################################################################################


def s1(signal1: Signal1, method=S1_METHOD) -> Signal1:
    output = S1_METHODS[method](signal1)
    output.axis *= output.sampling_freq() / output.span()
    return output


def _calculate_i_1(signal1: Signal1) -> Signal1:
    output = signal1.clone()
    signal_len = len(output)
    new_values = np.zeros(signal_len)
    for k in tqdm(range(signal_len), "Calculating DCT-I"):
        temp = 0
        for n, x in enumerate(output.values[1:-1]):
            temp += x * np.sin(np.pi * (n + 1) * (k + 1) / (signal_len + 1))
        new_values[k] = temp
    output.values = new_values * np.sqrt(2 / (signal_len + 1))
    return output


def _calculate_ii_1(signal1: Signal1) -> Signal1:
    output = signal1.clone()
    signal_len = len(output)
    new_values = np.zeros(signal_len)
    for k in tqdm(range(signal_len), "Calculating DCT-II"):
        temp = 0
        for n, x in enumerate(output.values):
            temp += x * np.sin((np.pi * (k + 1) / signal_len) * (n + 0.5))
        new_values[k] = temp
    new_values[-1] *= np.sqrt(0.5)
    output.values = new_values * np.sqrt(2 / signal_len)
    return output


def _calculate_iii_1(signal1: Signal1) -> Signal1:
    output = signal1.clone()
    signal_len = len(output)
    new_values = np.zeros(signal_len)
    for k in tqdm(range(signal_len), "Calculating DCT-III"):
        temp = 0
        for n, x in enumerate(output.values[:-1]):
            temp += x * np.sin((np.pi * (n + 1) / signal_len) * (k + 0.5))
        new_values[k] = temp + 0.5 * (-1 ** k) * output.values[-1]
    new_values[-1] *= np.sqrt(2)
    output.values = new_values * np.sqrt(2 / signal_len)
    return output


def _calculate_iv_1(signal1: Signal1) -> Signal1:
    output = signal1.clone()
    signal_len = len(output)
    new_values = np.zeros(signal_len)
    for k in tqdm(range(signal_len), "Calculating DCT-IV"):
        temp = 0
        for n, x in enumerate(output.values):
            temp += x * np.sin((np.pi / signal_len) * (n + 0.5) * (k + 0.5))
        new_values[k] = temp
    output.values = new_values * np.sqrt(2 / signal_len)
    return output


S1_METHODS = {
    1: _calculate_i_1,
    2: _calculate_ii_1,
    3: _calculate_iii_1,
    4: _calculate_iv_1,
    "i": _calculate_i_1,
    "ii": _calculate_ii_1,
    "iii": _calculate_iii_1,
    "iv": _calculate_iv_1,
}

########################################################################################################################
# |||||||||||||||||||||||||||||||||||||||||||||||| Signal2 ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||| #
########################################################################################################################


def s2(signal2: Signal2, method=S2_METHOD) -> Signal2:
    output = S2_METHODS[method](signal2)
    output.ax1 *= output.ax1_sampling_freq() / output.ax1_span()
    output.ax2 *= output.ax2_sampling_freq() / output.ax2_span()
    return output


def _calculate_ii_2(signal2: Signal2) -> Signal2:
    output = signal2.clone()
    signal_shape = output.shape()
    N, M = signal_shape
    new_values = np.zeros(signal_shape)
    for k in tqdm(range(N), "Calculating 2D DCT-II"):
        for l in range(M):
            temp = 0
            for n in range(N):
                for m in range(M):
                    temp += output[n, m] * np.cos(np.pi * (m + 0.5)
                                                  * l / M) * np.cos(np.pi * (n + 0.5) * k / N)
            new_values[k, l] = temp
    output.values = new_values
    return output


def _calculate_iv_2(signal2: Signal2) -> Signal2:
    output = signal2.clone()
    signal_shape = output.shape()
    N, M = signal_shape
    new_values = np.zeros(signal_shape)
    for k in tqdm(range(N), "Calculating 2D DCT-IV"):
        for l in range(M):
            temp = 0
            for n in range(N):
                for m in range(M):
                    temp += output[n, m] * np.cos(np.pi * (2 * m + 1) * (2 * k + 1) / (
                        4 * N)) * np.cos(np.pi * (2 * n + 1) * (2 * l + 1) / (4 * M))
            new_values[k, l] = temp
    output.values = new_values
    return output


S2_METHODS = {
    2: _calculate_ii_2,
    4: _calculate_iv_2,
    "ii": _calculate_ii_2,
    "iv": _calculate_iv_2,
}
