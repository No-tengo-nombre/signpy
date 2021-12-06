import numpy as np
from scipy import signal

from signpy.sgn import Signal1
from signpy.transforms import Transform1
from signpy.transforms.fourier import Fourier1, InverseFourier1
from signpy.config import HILBERT_METHOD


class Hilbert(Transform1):
    def __init__(self, target: Signal1, method=HILBERT_METHOD):
        self.methods = {
            "conv": self.calculate_conv,
            "fft": self.calculate_fft,
            "prod": self.calculate_prod,
            "scipy": self.calculate_scipy,
        }
        super().__init__(target)
        self.axis, self.values = self.calculate(method).unpack()

    def _char_function(self, t) -> float:
        return 1 / (np.pi * t)

    def calculate(self, method=HILBERT_METHOD) -> Signal1:
        return self.methods[method]()

    def calculate_conv(self) -> Signal1:
        output = self.signal.clone()
        signal2 = Signal1.from_function(output.axis, self._char_function)
        return output.convolute(signal2)

    def calculate_fft(self) -> Signal1:
        output = self.signal.clone()
        signal2 = Signal1.from_function(output.axis, self._char_function)
        self_fourier = Fourier1(output)
        t_fourier = Fourier1(signal2)
        return InverseFourier1(self_fourier * t_fourier)

    def calculate_prod(self) -> Signal1:
        output = self.signal.clone()
        self_fourier = Fourier1(output)
        # self_fourier = Fourier1(output).freq_shift()
        axis_len = len(output.axis)
        if axis_len % 2 == 0:
            h_values = 2 * np.ones(axis_len // 2 - 1)
        else:
            h_values = 2 * np.ones(axis_len // 2)
        h_values[0] = 1
        h_values[-1] = 1
        h_values = np.append(h_values, np.zeros(axis_len // 2 + 1))
        assert len(h_values) == axis_len
        # output.values = h_values
        # return InverseFourier1(output * self_fourier)
        output.values = output.values * self_fourier.values
        return InverseFourier1(output)

    def calculate_scipy(self) -> Signal1:
        output = self.signal.clone()
        output.values = signal.hilbert(output.values)
        return output.imag_part()
