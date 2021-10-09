"""
SG_test.py  tests Signal Generator

Creates signals in modes "real", "analytic", and "complex" and then checks the
locations of the spectral peaks.
"""
import logging
from math import degrees
import numpy as NP
from scipy.fft import fft, rfft

from DSP.tests import SignalProber
  
logger = logging.getLogger()
logger.setLevel(logging.INFO)

plotting = True
if plotting:
  from pylab import * 
  from DSP.plotter import plot_data

tester = SignalProber()
tester.empty_signal()
tester.noisy_signal()

for sigmode in ["real", "analytic", "complex"]:
  passed, signal, spectrum = tester.test_SG(sigmode)
  if plotting and not passed:
    plot_signal_summary(signal, spectrum)

passed, signal, spectrum = tester.test_QH()
if plotting and not passed:
  plot_signal_summary(signal, spectrum)

