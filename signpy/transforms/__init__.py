from __future__ import annotations
from typing import TYPE_CHECKING
import abc

from signpy import sgn


class Transform(sgn.Signal, abc.ABC):
    """Abstract class for an integral transform (Fourier, Laplace, etc.)."""
    # def __init__(self, target: sgn.Signal):
    #     """Creates an instance of this transform.

    #     Parameters
    #     ----------
    #     target : sgn.Signal
    #         Signal to apply the transform to.
    #     """
    #     self.signal = target
    #     self.methods = {}
    #     super().__init__(*self.calculate().unpack())
    #     target_axis = target.axis
    #     super().__init__(target_axis, 0 * target_axis)

    @abc.abstractmethod
    def calculate(self):
        """Applies the transform to the target signal.

        Returns
        -------
        Result of the transform.
        """
        pass

class Transform1(Transform, sgn.Signal1):
    def __init__(self, target : sgn.Signal1):
        self.signal = target
        super().__init__(*target.unpack())
