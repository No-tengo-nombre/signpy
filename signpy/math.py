from signpy.sgn import signal

import numpy as np


def convolute(x: signal.Signal1, y: signal.Signal1) -> signal.Signal1:
    copy = x.clone()
    return copy.apply_function(_conv_helper, y)

def _conv_helper(self, a, sign):
    sum = 0
    for k in sign.time:
        sum += a * sign[k]
    return sum

def cross_correlation(x: signal.Signal1, y: signal.Signal1) -> signal.Signal1:
    copy = x.clone()
