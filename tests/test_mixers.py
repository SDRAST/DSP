"""
test_mixers.py  tests BasicMixer and its subclasses

For BasicMixer, the test is that various combinations of signal types (None,
"real", or "complex") and LO types (None, "real", or "complex") yield the
right kinds of IFs.

For the subclasses, test signals with various components are injected and the
test is that the mixer produces mixed signals at the right frequencies.
"""
import logging
import math
import numpy as NP
from scipy.fft import fft, rfft
import unittest

from DSP import  (BasicMixer, ComplexMixer, DigitalSignal, ParallelMixer,
                  rect_to_polar, SignalGenerator, SimpleMixer)
from DSP.tests import (extra_components, get_peaks,
                       signal_components)

logger = logging.getLogger(__name__)
  
class MixerTester(unittest.TestCase):
  """
  Tests BasicMixer and its subclasses SimpleMixer, ComplexMixer, ParallelMixer
  
  The IF check tests need only be run on BasicMixer.
  """
  lopars = [[1,70,0]]
  M = 256
  def setUp(self):
    """
    """
    self.logger = logging.getLogger(logger.name+".MixerTester")
    self.logger.info("setUp: for %s", self)
     
  def testBasicMixer(self):
    self.assertTrue(self.run_tests(BasicMixer, 
                                   self.IF_check_setup, self.IF_check_test))
  
  def testSimplerMixer(self):
    self.assertTrue(self.run_tests(SimpleMixer,
                                   self.peak_check_setup, self.peak_check_test))
  
  def testComplexMixer(self):
    self.assertTrue(self.run_tests(ComplexMixer,
                                   self.peak_check_setup, self.peak_check_test))
  
  def testParallelMixer(self):
    self.assertTrue(self.run_tests(ParallelMixer,
                                   self.peak_check_setup, self.peak_check_test))

  def IF_check_setup(self, cls):
    """
    initialize for testing mixing action
    
    The first key for IFtest is the signal mode. The second is the LO mode.
    Mode "real" means dtype float; mode "complex" is for dtype complex.  Mode
    None is for the default. 
    
    The IF check is for all modes. The test values in IFtest are whether the IF
    is all zeros and the IF dtype. This makes a diagonally symmetrix diagram.
    """
    IFtest = {None:      {None:      (True,  complex),
                          "real":    (True,  complex),
                          "complex": (True,  complex)},
              "real":    {None:      (True,  complex),
                          "real":    (False, float  ),
                          "complex": (False, complex)},
              "complex": {None:      (True,  complex),
                          "real":    (False, complex),
                          "complex": (False, complex)}}
    sigmodes = [None, "real", "complex"]
    lomodes = [None, "real", "complex"]
    return IFtest, sigmodes, lomodes

  def IF_check_test(self, cls, signal, LO, IFtest, sigmode, lomode, passed):
    """
    This checks the mixer output, given the input types.
    
    The IF consists of either all zeros, or something else.  This is tested as
    well as the IF dtype.
    
    Args
    ====
    cls     - (BasixMixer subclass) class being tested
    signal  - (DigitalSignal subclass) test signal
    LO      - (DigitalSignal subclass) local oscillator
    IFtest  - (dict) comparison for test result
    sigmode - (str)
    lomode  - (str)
    passed  = (bool)
    """
    mx = BasicMixer(signal, LO)
    IF = mx.IF
    if IF.any():
      self.logger.debug("run_tests: IF st.dev. is %s", IF.std())
      zeros = False
    elif issubclass(type(IF), NP.ndarray):
      zeros = True
      self.logger.debug("run_tests: IF is %d zeros", len(IF))
    else:
      self.logger.debug("run_tests: IF is %s", IF)
      zeros = False
    if IFtest[sigmode][lomode] == (zeros, IF.dtype):
      pass
    else:
      self.logger.error("IF_check_test: %s signal zeros is %s, LO is %s",
                        cls, zeros, IF,dtype)
      passed = False
    return passed
  
  def peak_check_setup(self, cls):
    """
    This specifies which modes will be tested for mixer output correctness.
    """
    IFtest = None
    if cls == SimpleMixer:
      sigmodes = ["real"]
      lomodes = ["real"]
    elif cls == ParallelMixer:
      sigmodes = ["parallel"]
      lomodes = ["real"]
    elif cls == ComplexMixer:
      sigmodes = ["real"]
      lomodes = ["real"]
    else:
      self.logger.error("peak_check_setup: invalid class %s", cls)
      sigmodes = []
      lomodes = []
    return IFtest, sigmodes, lomodes
     
  def peak_check_test(self, cls, signal, LO, IFtest, sigmode, lomode, passed):
    """
    This tests whether the spectrum has peaks at the right places.
    
    Args
    ====
    cls     - (BasixMixer subclass) class being tested
    signal  - (DigitalSignal subclass) test signal
    LO      - (DigitalSignal subclass) local oscillator
    IFtest  - list of expected IF frequencies
    sigmode - (str)
    lomode  - (str)
    passed  = (bool) not used
    """
    peak_data = {}
    mx = cls(signal, LO)
    IF = mx.IF
    if sigmode == "parallel":
      Ispectrum = rfft(IF.real)
      Qspectrum = rfft(IF.imag)
      peaks = []
      for spec in [Ispectrum, Qspectrum]:
        spec_peaks = get_peaks(self.M, spec)[0]
        spec_peaks.sort()
        self.logger.debug("peak_check_test: peaks at %s", spec_peaks)
        for peak in spec_peaks:
          ampS, phsS = rect_to_polar(spec[peak])
          peak_data[peak] = (ampS,phsS/2/math.pi)
        peaks += list(spec_peaks)
    else:
      spectrum = IF.spectrum()
      peaks, negpeaks, pospeaks, S2 = get_peaks(self.M, spectrum)
      peaks.sort()
      self.logger.debug("peak_check_test: peaks at %s", peaks)
      for peak in peaks:
        ampS, phsS = rect_to_polar(spectrum[peak])
        peak_data[peak] = (ampS,phsS/2/math.pi)
    peaks.sort()
    for key in peak_data:
      self.logger.debug("peak_check_test: at %s, amp, phase = %s",
                        key, peak_data[key])
    if list(peaks) == IFtest:
      return True
    else:
      self.logger.error("peak_check_test: %s sorted peaks: %s", cls, peaks)
      self.logger.error("peak_check_test: %s expected peaks: %s", cls, IFtest)
      return False
  
  def expected_peaks(self, cls, sigmode, components, M):
    """
    computes the IF peaks expected for the specified signal components
    """
    loamp =  self.lopars[0][0]
    lofrq =  self.lopars[0][1]
    lophs =  self.lopars[0][2]
    self.logger.debug("expected_peaks: LO amp,frq,phs: %s, %s, %s",
                      loamp, lofrq, lophs)
    peaks = []
    for component in components:
      if sigmode in ["real",  "analytic"]:
        freq = component[1]
        amp = component[0]
        phs = component[2]
      elif sigmode == "complex":
        freq = component[0]
        amp, phs = rect_to_polar(component[1]+1j*component[2])
      else:
        raise ValueError("expected_peaks: sigmode %s invalid" % sigmode)
      self.logger.debug("expected_peaks: signal amp,frq,phs: %s, %s, %s",
                        amp, freq, phs)
      # positive signal frequencies only
      fsum = abs(freq) + lofrq; fdif = abs(freq) - lofrq
      if cls in [SimpleMixer, ParallelMixer]:
        # positive IFs only
        fsum=abs(fsum); fdif = abs(fdif)
        # aliases
        if fsum >= M//2: fsum = M-fsum
        if fdif >= M//2: fdif = M-fdif
      else: # ComplexMixer
        # if the sum/diff is outside the first Nyquist zones, alias it
        if fsum > M//2: fsum = M-fsum
        if fdif >= M//2: fdif = M-fdif
        # if sum/diff is negative (1st neg. Nyq) move it to 2nd pos. Nyq
        if fsum < 0: fsum = M + fsum
        if fdif < 0: fdif = M + fdif
      peaks += [fsum, fdif]
      
    peaks.sort()
    self.logger.debug("expected_peaks: %s", peaks)
    return peaks
          
  def run_tests(self, cls, setup, test):
    """
    Returns True if the IF is the correct type for given signal and the LO
    """
    IFtest, sigmodes, lomodes = setup(cls)
    passed = True
    for sigmode in sigmodes:
      if sigmode == None:
        signal = DigitalSignal(M=self.M)
      elif sigmode == "parallel":
        # create a complex signal, then replace the imaginary part
        signal = SignalGenerator(M=self.M, mode="analytic",
                              components=signal_components("analytic")).signal()
        signal.imag = SignalGenerator(M=self.M, mode="real",
                                   components=extra_components("real")).signal()
      else:        
        signal = SignalGenerator(M=self.M, mode=sigmode,
                                 components=signal_components(sigmode)).signal()
      for lomode in lomodes:
        self.logger.debug("run_tests: for %s with signal type %s, LO type %s",
                          cls, sigmode, lomode)
        if lomode == None:
          LO = DigitalSignal(M=self.M)
        else:        
          LO = SignalGenerator(M=self.M, mode=lomode,
                               components=self.lopars).signal()
        if test == self.peak_check_test:
          if sigmode == "parallel":
            IFtest = self.expected_peaks(cls, "real",
                                         signal_components("real"), self.M)
            IFtest += self.expected_peaks(cls, "real",
                                          extra_components("real"), self.M)
          else:
            IFtest = self.expected_peaks(cls, sigmode,
                                         signal_components(sigmode), self.M)
          IFtest.sort()
          self.logger.debug("run_tests: %s expected peaks: %s", cls, IFtest)
          passed = test(cls, signal, LO, IFtest, sigmode, lomode, passed)
          if not passed:
            self.logger.error("run_tests: M=%d, signal=%s, LO=%s",
                              self.M, signal.info, LO.info)
    return passed

if __name__ == "__main__":
  unittest.main()



