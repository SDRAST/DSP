"""
test.py - functions to support tests
"""
import logging
import numpy as NP

from .. import (DigitalSignal, QuadratureHybrid, SignalGenerator,
               is_quadrature, rect_to_polar)

logger = logging.getLogger(__name__)

class SignalProber(object):
  """
  tests various DigitalSignal objects created with SignalGenerator
  
  Attrs
  =====
    logger:   (logging.Logger)
    M:        (int) signal size
    
  """
  def __init__(self, M=256):
    """
    Args
    ====
      M:        (int) signal size
      
    """
    self.M = M
    self.logger = logging.getLogger(logger.name+".SignalProber")

  def check_signal_type(self, signal):
    """
    returns ``True`` for ``dtype`` of ``float`` or ``complex``, or False otherwise
    """
    if signal.dtype == float:
      return True
    elif signal.dtype == complex:
      return True
    else:
      logger.error("check_signal_type: %s type signal is not '%s'",
                   (signal.dtyp, sigmode))
      return False

  def empty_signal(self):
    """
    test DigitalSignal for no data (empty signal)
    """
    zeros = DigitalSignal(M=self.M)
    if zeros.any():
      self.logger.debug("empty_signal: creating empty %s signal failed",
                        zeros.dtype)
      return False
    else:
      self.logger.debug("empty_signal: created empty %s signal", zeros.dtype)
      return True
  
  def noisy_signal(self, rms=0.1):
    """
    test DigitalSignal for noisy data
    """
    noise = DigitalSignal(M=self.M, rms=rms)
    if noise.any():
      std = noise.std()
      if abs(std - rms) < 1/self.M:
        self.logger.debug("noisy_signal: created noisy %s signal %s",
                          noise.dtype, noise.std())
        return True
      else:
        self.logger.error("noisy_signal: rms is %s; should be %s", std, rms)
        return False
    else:
      self.logger.error("noisy_signal: creating noisy %s signal failed" %
                        noise.dtype)
      return False
  
  def peak_test(self, peak, ampS, phsS, ampC, phsC):
    """
    tests that component peak amplitude is what is expected
    
    Args
    ====
    
      peak: (int or float) frequency of the peak
      ampS: (float) amplitude of the peak in the signal
      phsS: (float) phase in cycles of the peak in the signal
      ampC: (float) amplitude of the injected component
      phsC: (float) phase in cycles of the injected component
      
    """
    if abs(ampS-self.M*ampC/2) < 1e-6:
      return True
    else:
      self.logger.error("peak_test: %4d: expected amp %5.2f, phase %4.2f",
                        peak, ampC, 360*phsC)
      self.logger.error("peak_test: %4d: got amp %5.2f, phase %4.2f",
                        peak, ampS, 360*phsS)
      return False

  def check_signal_peaks(self, sigmode, spectrum, components): 
    """  
    check each peak's parameters to match a component
  
    For each peak in the spectrum, checks that its properties match a component
    
    Args
    ====
    
      sigmode:    (int) signal mode ("real", "analytic", or "complex")
      spectrum:   (ndarray) voltage spectrum of the signal
      components: (list of lists) component properties
    """
    peaks, negpeaks, pospeaks, S2 =  get_peaks(self.M, spectrum)
    passed = True
    for peak in peaks:
      # get spectral feature amplitude and phase
      ampS, phsS = rect_to_polar(spectrum[peak])
      
      if sigmode == "real": # real modee test
        response = check_component(peak,components)
        if response:
          pass
        else:
          response = check_component(-peak,components)
        if response:
          # check that the feature amplitude and component amplitude agree
          ampC, phsC = response
          passed = passed and self.peak_test(peak, ampS, phsS, ampC, phsC)
        else:
          self.logger.error("check_signal_peaks: no response for peak %d", peak)
          freqs = []
          for comp in components:
            freqs.append(comp[1])
          self.logger.error("check_signal_peaks: frequencies are %s", freqs)
          passed = False
          
      elif sigmode == "analytic":
        if peak > self.M/2:
          response = check_component(peak-self.M,components)
        else:
          response = check_component(peak,components)
        if response:
          ampC, phsC = response
          passed = passed and self.peak_test(peak, ampS, phsS, ampC, phsC)
            
      elif sigmode == "complex":
        self.logger.debug("check_signal_peaks: checking %s", peak)
        if peak > self.M/2:
          response = check_component(peak-self.M, components, idx_pos=0)
        else:
          response = check_component(peak, components, idx_pos=0)
        if response:
          v = response[0]+1j*response[1]
          ampC, phsC = rect_to_polar(v)
          # the signal amplitude is twice the component amplitude because both
          # the sine term and the cosine term contribute to it
          passed = passed and self.peak_test(peak, ampS, phsS, 2*ampC, phsC)
        else:
          self.logger.error(
                         "check_signal_peaks: no response from check_component")
      else:
        self.logger.error("check_signal_peaks: invalid signal mode: %s",
                          sigmode)
        passed=False
    if not passed:
      self.logger.error("check_signal_peaks: %s mode test failed", sigmode)
    return passed
  
  def test_SG(self, sigmode):
    """
    test SignalGenerator for signals
    """
    components = signal_components(sigmode)
    signal = SignalGenerator(mode=sigmode, M=self.M, 
                             components=components).signal()
    self.check_signal_type(signal)  

    spectrum = signal.spectrum()
    passed = self.check_signal_peaks(sigmode, spectrum, components)
    self.logger.info("test_SG: signal type %s passed = %s", sigmode, passed)
    return passed, signal, spectrum

  def test_QH(self):
    """
    test QuadratureHybrid
    
    creates a real signal which is converted with a Quadrature Hybrid object
    into an analytic signal.  It then uses DSP function is_quadrature() to test
    it. It also checks that the spectrum peaks of the analytic signal match
    what is expected.
    """
    components = signal_components("real")
    signal = SignalGenerator(mode="real", M=self.M,
                             components=components).signal()
    self.logger.debug("test_QH: signal in is %s", signal.dtype)
    qh = QuadratureHybrid()
    I,Q = qh.convert(signal)
    analsignal = I + 1j*Q
    self.logger.debug("test_QH: signal out is %s", analsignal.dtype)
    if is_quadrature(analsignal):
      pass
    else:
      self.logger.error("test_QH: signal is not quadrature")
      passed = False
    spectrum = signal.spectrum()
    passed = self.check_signal_peaks("real", spectrum, components)
    self.logger.info("test_QH: passed = %s", passed)
    return passed, signal, spectrum

#################### functions useful for testing ##############################

def signal_components(sigmode):
  """
  provides three frequency components for a test signal
  
  The components can specify the components in exponential/trogonmetric form
  or complex number form.
  """
  if sigmode == "real" or sigmode == "analytic":
    components=[[0.5, -60, 0.5],
                [1,    75, 0],
                [0.25, 90, 0.25]]
  elif sigmode == "complex": # should give same signal as analytic
    #            frq   I     Q
    components=[[-60, -0.5, 0],
                [ 75,  1,   0],
                [ 90,  0,   0.25]]
  else:
    logger.error("signal_components: mode %s is invalid", sigmode)
    components = []
  return components

def extra_components(sigmode):
  """
  provides two different frequency components for a test signal
  """
  if sigmode == "real":
    components = [[1, 45, .25],
                  [1, 85, .75]]
  else:
    raise ValueError("no extra components defined for sigmode %s", sigmode)
  return components
  
  
def check_component(freq, components, idx_pos=1, sigmode=None):
  """
  returns parameters for a component given the frequency
  
  Args
  ====
  
    freq:       (int) frequency of component to be checked
    components: (list of lists)
    idx_pos:    (int) index of the frequency in the component list
    sigmode:    (str) signal mode, which determines frequency position index
  
  Notes
  =====
  For a component in complex form, it returns the cosine and sine coefficients.
  For exponential/trigometric form, it returns amplitude and phase.
  
  The sine and cosine components add in quadrature so a given frequency
  component has twice
  """
  if sigmode == "real" or sigmode == "analytic":
    idx_pos=1
  elif sigmode == "complex":
    idx_pos=0
  for comp in components:
    if idx_pos:
      if freq == comp[1]:
        return comp[0], comp[2]
      else:
        continue
    elif idx_pos == 0:
      if freq == comp[0]:
        return comp[1], comp[2]
      else:
        continue
    else:
      raise ValueError("check_component: idx_pos=%d is invalid" % idx_pos)
  return None

def get_peaks(M, spectrum):
  """
  returns the peaks in the spectrum
  
  A peak is defined as having a power > 1.  ``pospeaks`` are in the first
  Nyquist zone. ``negpeaks`` are in the second Nyquist zone, i.e. have negative
  frequencies.
  
  Args
  ====
    M -        (int) number of data samples
    spectrum - (ndarray) signal voltage spectrum
  """
  S2 = spectrum*spectrum.conjugate()
  sorted_ids = S2.argsort()[::-1]
  pk_ids = NP.where(S2[sorted_ids] > 1)
  peaks = sorted_ids[pk_ids]
  negpeaks = peaks[NP.where(peaks >= M/2)]
  pospeaks = peaks[NP.where(peaks <= M/2)]
  return peaks, negpeaks, pospeaks, S2

