"""
===================
Signal manipulation
===================

This subpackage gives the basic tools needed to create, import and
export signals of different dimensions.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
import bisect
import operator
import abc
from numbers import Number, Real
from copy import deepcopy
from multipledispatch import dispatch

from signpy.exceptions import DimensionError
from signpy.config import (CONVOLUTION_METHOD, INTERPOLATION_METHOD,
                           CROSS_CORRELATION_METHOD, KERNEL_OOB)
from signpy import math_lib
from .handlers import handler_csv, handler_json, handler_wav


class Signal(abc.ABC):
    """Abstract class representing a signal object of arbitrary dimensions."""

    @abc.abstractmethod
    def __getitem__(self, key):
        pass

    @abc.abstractmethod
    def __add__(self, signal):
        pass

    @abc.abstractmethod
    def __sub__(self, signal):
        pass

    @abc.abstractmethod
    def __mul__(self, signal):
        pass

    @abc.abstractmethod
    def __truediv__(self, signal):
        pass

    @abc.abstractmethod
    def __eq__(self, signal):
        pass

    @abc.abstractmethod
    def __str__(self):
        pass

    @abc.abstractmethod
    def __abs__(self):
        pass

    # @abc.abstractmethod
    # def __len__(self):
    #     pass

    @abc.abstractclassmethod
    def from_function(cls, axis, func, *args, **kwargs):
        """Creates a signal from an axis and a function.

        The function is applied to each element in the axis, so
        if the function f(x) = x**2 is given as a parameter to the axis
        [1, 2, 3, 4], the values would be [1, 4, 9, 16].

        Parameters
        ----------
        axis : np.ndarray
            Axis on which the function is mapped.
        func : function
            Function to map to the axis.
        """
        pass

    @abc.abstractclassmethod
    def from_file(cls, filename: str):
        """Creates a signal from a file.

        Parameters
        ----------
        filename : str
            File to read the data from.
        """
        pass

    @abc.abstractmethod
    def interpolate(self, value, method):
        """Interpolates the current values to obtain a new value."""
        pass

    @abc.abstractmethod
    def unpack(self):
        """Unpacks the signal into arrays. If used for its intended
        purpose, should be unpacked with *.
        """
        pass

    @abc.abstractmethod
    def apply_function(self, func, *args, **kwargs):
        """Applies a function to the values of the signal.

        Parameters
        ----------
        func : function
            Function to apply to the signal.
        """
        pass

    @abc.abstractmethod
    def export_to_file(self, filename: str):
        """Exports the signal values to a file.

        Parameters
        ----------
        filename : str
            File to export the data to.
        """
        pass

    def clone(self):
        """Makes a copy of this signal."""
        return deepcopy(self)

########################################################################################################################
# |||||||||||||||||||||||||||||||||||||||||||||||| Signal1 ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||| #
########################################################################################################################


class Signal1(Signal):
    """Class representing a one dimensional signal."""
    handlers = {
        "csv": handler_csv,
        "json": handler_json,
        "wav": handler_wav,
    }

    def __init__(self, axis: np.ndarray, values: np.ndarray):
        """Creates a signal from an independent axis and a values list.

        Parameters
        ----------
        axis : array_like
            List of elements representing the independent variable
            (usually time).
        values : array_like
            List of elements representing the dependent variable for
            each axis element.

        Raises
        ------
        DimensionError
            Raises this when the dimensions of `axis` and `values`
            don't match each other.
        """
        if len(axis) != len(values):
            raise DimensionError("The dimensions of the values do not match.")
        self.axis = np.array(axis)
        self.values = np.array(values)

    def __getitem__(self, key):
        return self.values[key]

    @dispatch(slice)
    def __call__(self, key):
        # Slices the indices based on the given key, then intersects
        # them to get all the indices
        indices1 = np.where(
            key.start <= self.axis if key.start else self.axis)
        indices2 = np.where(
            self.axis <= key.stop if key.stop else self.axis)
        indices = np.intersect1d(indices1, indices2)
        return [self.values[i] for i in indices]

    @dispatch(Real)
    def __call__(self, key):
        return self.interpolate(key)[2]

    def __radd__(self, num):
        return self.__add__(num)

    @dispatch(Number)
    def __add__(self, value):
        return Signal1(self.axis, self.values + value)

    @dispatch(object)
    def __add__(self, signal):
        return Signal1(*self._do_bin_operation(signal, operator.add))

    def __rsub__(self, num):
        return num + self * -1

    @dispatch(Number)
    def __sub__(self, value):
        return Signal1(self.axis, self.values - value)

    @dispatch(object)
    def __sub__(self, signal):
        return Signal1(*self._do_bin_operation(signal, operator.sub))

    def __rmul__(self, num):
        return self.__mul__(num)

    @dispatch(Number)
    def __mul__(self, value):
        return Signal1(self.axis, self.values * value)

    @dispatch(object)
    def __mul__(self, signal):
        return Signal1(*self._do_bin_operation(signal, operator.mul))

    def __rtruediv__(self, num):
        return Signal1(self.axis, num / self.values)

    @dispatch(Number)
    def __truediv__(self, value):
        return Signal1(self.axis, self.values / value)

    @dispatch(object)
    def __truediv__(self, signal):
        return Signal1(*self._do_bin_operation(signal, operator.truediv))

    def __eq__(self, signal):
        return (
            np.array_equal(self.axis, signal.axis)
            and np.array_equal(self.values, signal.values)
        )

    def __str__(self):
        return f"{self.axis}\n{self.values}"

    def __abs__(self):
        return Signal1(self.axis, list(map(operator.abs, self.values)))

    def __len__(self):
        return len(self.axis)

    def _do_bin_operation(self, signal, operation):
        # Joins the axes of both signals
        axis_list = np.union1d(self.axis, signal.axis)
        axis_list.sort()

        new_values = np.array([])
        for t in axis_list:
            # Interpolates the values
            y1 = self(t)
            y2 = signal(t)
            # Operates using the interpolated values
            new_values = np.append(new_values, operation(y1, y2))
        return axis_list, new_values

    @classmethod
    def from_function(cls, axis: np.ndarray, func, *args, **kwargs):
        """Creates a signal from an axis list and a function.

        The function is applied to each element in the axis, so if the
        function f(x) = x**2 is given as a parameter to the axis
        [1, 2, 3, 4], the values should be [1, 4, 9, 16].

        Parameters
        ----------
        axis : array_like
            List of elements representing the independent variable
            (usually time).
        func : function
            Function to apply to each element.
        """
        return cls(axis, func(np.array(axis), *args, **kwargs))

    @classmethod
    def from_file(cls, filename: str, *args, **kwargs):
        extension = filename.split(".")[-1]
        if extension == filename:
            raise ValueError()
        cls(*Signal1.handlers[extension].import_signal1(
            filename, *args, **kwargs
        ))

    @classmethod
    def from_freq(cls, values: np.ndarray, sf=1, sp=0):
        """Creates a signal from a values list and a sampling frequency.

        Parameters
        ----------
        values : array_like
            List of elements representing the dependent variable for
            each axis element.
        sf : real number, optional
            Sampling frequency used to create the axis, by default 1.
        sp : real number, optional
            Starting point for the axis, by default 0.
        """
        samp_period = 1 / sf
        vals = np.array(values)
        axis = np.arange(len(values), samp_period) - sp
        return cls(axis, vals)

    def sampling_freq(self) -> float:
        """Calculates the sampling frequency in hertz, assuming it is constant."""
        sf = 1 / (self.axis[1] - self.axis[0])
        return sf if sf > 0 else 0

    def interpolate(self, element, method=INTERPOLATION_METHOD):
        """Interpolates the current values to obtain a new value.

        Parameters
        ----------
        element : float
            Element to apply the interpolation to.
        method : {"linear"}, optional
            Method used for the interpolation, by default INTERPOLATION_METHOD.
        Returns
        -------
        copy : Signal1
            Copy of the signal with the new value interpolated.
        index : int
            Index of the interpolated value.
        new_value : float
            Value of the interpolated value.
        """
        copy = self.clone()
        if element not in self.axis:
            # Inserts the new element into the axis
            new_index = bisect.bisect(self.axis, element)
            copy.axis = np.insert(copy.axis, new_index, element)
            copy.values = np.insert(copy.values, new_index, 0)

            if method == "linear":
                ta = copy.axis[new_index - 1]
                xa = copy.values[new_index - 1]
                try:
                    tb = copy.axis[new_index + 1]
                    xb = copy.values[new_index + 1]
                    # tb = copy.axis[new_index]
                    # xb = copy.values[new_index]
                except IndexError:
                    # This code is reached if the program tries to
                    # interpolate points out of the range. In this case,
                    # it simply interpolates using the last value. For
                    # `xb` we take the element -2 because, if this code
                    # is reached, a 0 was added in the last value
                    tb = copy.axis[-1]
                    xb = copy.values[-2]

                # Linearly interpolates
                new_value = xa + (xb - xa) * (element - ta) / (tb - ta)
                copy.values[new_index] = new_value
                return copy, new_index, new_value
        else:
            index = bisect.bisect(copy.axis, element) - 1
            return copy, index, self.values[index]

    def interpl(self, element):
        """Applies a linear interpolation to obtain a new value.

        Parameters
        ----------
        element : float
            Element to apply the interpolation to.

        Returns
        -------
        New index and value.
        """
        return self.interpolate(element, "linear")

    def unpack(self):
        """Unpacks the signal into two arrays. If used for its
        intended purpose, should be unpacked with *.
        """
        return self.axis, self.values

    def span(self) -> float:
        """Gets the span of the signal"""
        return self.axis[-1] - self.axis[0]

    def half(self, first=True):
        """Gets half of the signal"""
        return self[:self.span() / 2] * 2 if first else self[self.span() / 2:] * 2

    def rect_smooth(self, factor: int) -> Signal1:
        """Directly applies a rectangular smoothing to the signal.

        With this method the edges of the signal look a bit rough.

        Parameters
        ----------
        factor : int (odd)
            Smoothing factor.

        Returns
        -------
        Signal1
            Smooth signal.
        """
        copy = self.clone()
        if factor % 2 != 1 or factor <= 1:
            raise ValueError("The smoothing factor must be an odd number.")
        shift = int((factor - 1) / 2)
        self_len = len(copy)
        new_values = copy.values[0:1]               # Copies the first element

        # Smooths the first elements with the only possible elements
        for n in range(1, shift):
            arr = copy.values[0:2 * n + 1]
            new_values = np.append(new_values, arr.sum() / (2 * n + 1))

        # Smooths the other elements using the given factor
        for n in range(shift, self_len - shift):
            arr = copy.values[n - shift:n + shift + 1]
            new_values = np.append(new_values, arr.sum() / factor)

        # Smooths the last elements adapting the smoothing factor
        for n in range(self_len - shift, self_len):
            new_shift = self_len - n - 1
            arr = copy.values[n - new_shift:self_len]
            new_values = np.append(new_values, arr.sum() / (2 * new_shift + 1))

        assert self_len == len(
            new_values), "There was an error during the smoothing."
        copy.values = new_values
        return copy

    def apply_function(self, func, *args, **kwargs) -> Signal1:
        """Applies a function to the values of the signal.

        Parameters
        ----------
        func : function
            Function to apply to the signal.

        Returns
        -------
        Signal1
            Modified signal.
        """
        copy = self.clone()
        copy.values = np.array([func(x, *args, **kwargs) for x in copy.values])
        return copy

    def apply_function_tuple(self, func, *args, **kwargs) -> Signal1:
        """Applies a function to both the axis and values of the signal.

        Parameters
        ----------
        func : function
            Function to apply to the signal.

        Returns
        -------
        Signal1
            Modified signal.
        """
        copy = self.clone()
        copy.values = np.array([func(t, x, *args, **kwargs)
                               for t, x in zip(copy.axis, copy.values)])
        return copy

    def convolute(self, signal1: Signal1, method=CONVOLUTION_METHOD) -> Signal1:
        """Convolute this signal with another.

        Parameters
        ----------
        signal1 : Signal1
            Signal to convolute with.
        method : {"fft", "direct"}, optional
            Method utilized to calculate the convolution, by
            default CONVOLUTION_METHOD.

        Returns
        -------
        Signal1
            Convoluted signal.
        """
        return math_lib.convolution(self, signal1, method)

    def cross_correlate(self, signal1: Signal1,
                        method=CROSS_CORRELATION_METHOD) -> Signal1:
        """Cross-correlates this signal with another.

        Parameters
        ----------
        signal1 : Signal1
            Signal to cross-correlate with.
        method : {"direct"}, optional
            Method utilized to calculate the cross-correlation, by
            default CROSS_CORRELATION_METHOD.

        Returns
        -------
        Signal1
            Cross-correlated signal.
        """
        return math_lib.cross_correlation(self, signal1, method)

    def auto_correlate(self, method=CROSS_CORRELATION_METHOD) -> Signal1:
        """Auto-correlates this signal.

        Parameters
        ----------
        method : {"direct"}, optional
            Method utilized to calculate the auto-correlation, by
            default CROSS_CORRELATION_METHOD.

        Returns
        -------
        Signal1
            Auto-correlated signal.
        """
        return math_lib.cross_correlation(self, self, method)

    def shift(self, value) -> Signal1:
        """Shifts the axis by `value`."""
        copy = self.clone()
        copy.axis += value
        return copy

    def real_part(self) -> Signal1:
        """Takes the real part of the values."""
        copy = self.clone()
        copy.values = np.real(copy.values)
        return copy

    def imag_part(self) -> Signal1:
        """Takes the imaginary part of the values."""
        copy = self.clone()
        copy.values = np.imag(copy.values)
        return copy

    def conjugate(self) -> Signal1:
        """Takes the conjugate of the values."""
        copy = self.clone()
        copy.values = copy.values.conjugate()
        return copy

    def export_to_file(self, filename: str, *args, **kwargs):
        """Exports the one dimensional signal to the given file.

        Parameters
        ----------
        filename : str
            String corrresponding to the file.

        Raises
        ------
        ValueError
            If the filename is empty (e.g trying to export to the file ".csv").
        """
        extension = filename.split(".")[-1]
        if extension == filename:
            raise ValueError()
        Signal1.handlers[extension].export_signal1(
            filename, self, *args, **kwargs)

########################################################################################################################
# |||||||||||||||||||||||||||||||||||||||||||||||| Signal2 ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||| #
########################################################################################################################


class Signal2(Signal):
    """Class representing a two dimensional signal."""
    handlers = {

    }

    def __init__(self, ax1: np.ndarray, ax2: np.ndarray,
                 values: np.ndarray):
        """Creates a two dimensional signal by giving two axes and a
        matrix.

        Each axis corresponds to one of the dimensions, where
        `ax1` indexes the rows of `values`, while `ax2` indexes its
        columns.

        Parameters
        ----------
        ax1 : array_like
            First axis, which indexes the rows of `values`.
        ax2 : array_like
            Second axis, which indexes the columns of `values`.
        values : two-dimensional array_like
            Matrix that indicates the values of the signal for every
            point.

        Raises
        ------
        DimensionError
            Raises this when the shape of `values` doesn't match the
            sizes of `ax1` and `ax2`.

        Example
        -------
        Creating the following object
        >>> ax1 = [1, 2, 3]
        >>> ax2 = [2, 4, 6]
        >>> vals = [
        >>>     [1, 2, 3],
        >>>     [2, 4, 6],
        >>>     [3, 6, 9]
        >>> ]
        >>> signal = Signal2(ax1, ax2, vals)
        can be understood as the following plot
          ax2
           |
         6 |  3  6  9
           |
         4 |  2  4  6
           |
         2 |  1  2  3
           |
         0 |--------- ax1
           0  1  2  3
        """
        if np.shape(values) != (len(ax1), len(ax2)):
            raise DimensionError("The dimensions of the values do not match.")
        self.ax1 = np.array(ax1)
        self.ax2 = np.array(ax2)
        self.values = np.array(values)

    def __getitem__(self, key):
        return self.values[key]

    @dispatch(Real, Real)
    def __call__(self, key_x, key_y):
        return self.interpolate(key_x, axis=0), self.interpolate(key_y, axis=1)

    @dispatch(Real)
    def __call__(self, key):
        return self.interpolate(key)[2]

    def __radd__(self, num):
        return self.__add__(num)

    @dispatch(Number)
    def __add__(self, value):
        return Signal2(self.ax1, self.ax2, self.values + value)

    @dispatch(object)
    def __add__(self, signal):
        return Signal2(*self._do_bin_operation(signal, operator.add))

    def __rsub__(self, num):
        return num + self * -1

    @dispatch(Number)
    def __sub__(self, value):
        return Signal2(self.ax1, self.ax2, self.values - value)

    @dispatch(object)
    def __sub__(self, signal):
        return Signal2(*self._do_bin_operation(signal, operator.sub))

    def __rmul__(self, num):
        return self.__mul__(num)

    @dispatch(Number)
    def __mul__(self, value):
        return Signal2(self.ax1, self.ax2, self.values * value)

    @dispatch(object)
    def __mul__(self, signal):
        return Signal2(*self._do_bin_operation(signal, operator.mul))

    def __rtruediv__(self, num):
        return Signal2(self.ax1, self.ax2, num / self.values)

    @dispatch(Number)
    def __truediv__(self, value):
        return Signal2(self.ax1, self.ax2, self.values / value)

    @dispatch(object)
    def __truediv__(self, signal):
        return Signal2(*self._do_bin_operation(signal, operator.truediv))

    def __eq__(self, signal):
        return (
            np.array_equal(self.ax1, signal.ax1)
            and np.array_equal(self.ax2, signal.ax2)
            and np.array_equal(self.values, signal.values)
        )

    def __str__(self):
        return f"{self.ax1}\n{self.ax2}\n{self.values}"

    def __abs__(self):
        return Signal2(self.ax1, self.ax2, list(map(operator.abs, self.values)))

    # def __len__(self):
    #     return np.shape(self.values)
        # return len(self.ax1), len(self.ax2)

    def _do_bin_operation(self, signal, operation):
        # Joins the axes of both signals
        new_ax1 = np.union1d(self.ax1, signal.ax1)
        new_ax2 = np.union1d(self.ax2, signal.ax2)
        new_ax1.sort()
        new_ax2.sort()

        new_values = new_ax2.copy()
        for x in new_ax1:
            row = np.array([])
            for y in new_ax2:
                # Interpolates the values
                val1 = self(x, y)
                val2 = signal(x, y)
                # Operates using the interpolated values
                row = np.append(row, operation(val1, val2))
            new_values = np.vstack((new_values, row))
        return new_ax1, new_ax2, new_values

    @classmethod
    def from_function(cls, ax1, ax2, func, *args, **kwargs):
        """Creates a signal from two axes and a function.

        The function is applied to each element in the axis, so
        if the function `f(x, y) = x**2 + y**2` is given as a parameter to
        the axes `[1, 2, 3]` and `[-1, -2, -3]`, the values would be the
        matrix `[[2, 5, 10], [5, 8, 13], [10, 13, 18]]`.

        Parameters
        ----------
        ax1 : np.ndarray
            First on which the function is mapped.
        ax2 : np.ndarray
            Second on which the function is mapped.
        func : function
            Function to map to the axes.
        """
        values = np.array([[func(x, y, *args, **kwargs)
                          for x in ax1] for y in ax2])
        # return cls(ax1, ax2, func(np.array(ax1), np.array(ax2), *args, **kwargs))
        return cls(ax1, ax2, values)

    @classmethod
    def from_file(cls, filename: str, *args, **kwargs):
        """Creates a signal from a file. If the file is an image with
        an RGB channel, using `channel` you can specify which channel
        to read from, or the method used to handle them.

        Parameters
        ----------
        filename : str
            File to read the data from.
        """
        extension = filename.split(".")[-1]
        if extension == filename:
            raise ValueError()
        cls(*
            Signal2.handlers[extension].import_signal2(filename, *args, **kwargs))

    @classmethod
    def from_freq(cls, values: np.ndarray, sf_ax1=1, sf_ax2=1, sp_ax1=0, sp_ax2=0):
        """Creates a two dimensional signal by giving a values matrix
        and a frequency for each axis.

        Each axis corresponds to one of the dimensions, where
        `ax1` indexes the rows of `values`, while `ax2` indexes its
        columns.

        Parameters
        ----------
        values : two-dimensional array_like
            Matrix that indicates the values of the signal for every
            point.
        sf_ax1 : float, optional
            Sampling frequency of the first axis, by default 1.
        sf_ax2 : float, optional
            Sampling frequency of the second axis, by default 1.
        sp_ax1 : float, optional
            Starting point for the first axis, by default 0.
        sp_ax2 : float, optional
            Starting point for the second axis, by default 0.
        """
        ax1_samp_period = 1 / sf_ax1
        ax2_samp_period = 1 / sf_ax2
        val_shape = np.shape(values)

        vals = np.array(values)
        ax1 = np.arange(val_shape[0], ax1_samp_period) - sp_ax1
        ax2 = np.arange(val_shape[1], ax2_samp_period) - sp_ax2
        return cls(ax1, ax2, vals)

    def interpolate(self, value, method=INTERPOLATION_METHOD):
        """Interpolates the current values to obtain a new value."""
        pass

    def unpack(self):
        """Unpacks the signal into three arrays. If used for its
        intended purpose, should be unpacked with *.
        """
        return self.ax1, self.ax2, self.values

    def apply_function(self, func, *args, **kwargs):
        """Applies a function to the values of the signal.

        Parameters
        ----------
        func : function
            Function to apply to the signal.
        """
        copy = self.clone()
        copy.values = np.array([func(x, *args, **kwargs) for x in copy.values])
        return copy

    def export_to_file(self, filename: str, *args, **kwargs):
        """Exports the one dimensional signal to the given file.

        Parameters
        ----------
        filename : str
            String corrresponding to the file.

        Raises
        ------
        ValueError
            If the filename is empty (e.g trying to export to the file ".csv").
        """
        extension = filename.split(".")[-1]
        if extension == filename:
            raise ValueError()
        Signal2.handlers[extension].export_signal2(
            filename, self, *args, **kwargs)

    def shape(self):
        return np.shape(self.values)

    def ax1_sampling_freq(self) -> float:
        """Calculates the sampling frequency of `ax1` in hertz, assuming
        it is constant.
        """
        sf = 1 / (self.ax1[1] - self.ax1[0])
        return sf if sf > 0 else 0

    def ax2_sampling_freq(self) -> float:
        """Calculates the sampling frequency of `ax2` in hertz, assuming
        it is constant.
        """
        sf = 1 / (self.ax2[1] - self.ax2[0])
        return sf if sf > 0 else 0

    def ax1_span(self) -> float:
        return self.ax1[-1] - self.ax1[0]

    def ax2_span(self) -> float:
        return self.ax2[-1] - self.ax2[0]

    def convolute(self, kernel: np.ndarray, flip=False, oob=KERNEL_OOB):
        return math_lib.apply_kernel(self, kernel, flip, oob)
