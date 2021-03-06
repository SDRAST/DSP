"""
module DSP - demonstrates digital signal processing concepts

Provides digital simulations for devices used in analog signal processing.

Notes
=====

`Analytic` signals are complex signals in exponential notation, using Euler's
formula. Specifically they are the two signals out of a complex mixer or
quadrature hybrid, in which all the Fourier components of the imaginary or 
`sine` voltage have been delayed by a quarter cycle::

                                      +iwt
  V     = V  + i V  = V  + i V  = V  e
   anal    r      i    I      Q    0

where ``w`` is the angular frequency.
"""
import logging
import math
import numpy as NP
import scipy as SP
import scipy.fftpack, scipy.signal
import warnings

logger = logging.getLogger(__name__)


class DigitalSignal(NP.ndarray):
  """
  Signal with noise and Fourier components
  
  A signal is defined as a complex quantity::
  
    S = I + i Q
  
  which corresponds to Euler's formula::
  
        ix
    S  e    = S cos(x) + i S sin(x)
     0         0            0
  
  The Fourier components in the imaginary part of the array `Q` are delayed  by
  a quarter cycle with respect to `I`.
     
  Note that this corresponds to what is known as the inverse transform. If `x`
  is `w t`, then the forward transform is defined as converting from time space
  (`t`) to frequency space (`w`).  In this case we use frequencies `w` to create
  a signal in time `t`.
  
  This subclass of ``numpy.ndarray`` has an attribute ``info`` which is a 
  ``dict`` with properties of the signal
  """
  def __new__(subtype, M=1024, I=None, Q=None, rms=None):
    """
    initialize a digital signal
    
    With no arguments a complex array with shape (1024,) will be created.
    s = DigitalSignal(rms=1) with create 1024 Gaussian noise samples with a
    standard deviaton of 1.
    
    Args:
      M   - (int) number of samples
      I   - (ndtype=float) real (cos) part of signal
      Q   - (ndtype=float) imaginary (sin) part of signal
      rms - (float) r.m.s. noise amplitude
  
    Attrs
    =====
      info   - (dict) signal properties
      logger - (logging.Logger)
      
    Notes
    =====
    Subclassing NP.ndarray is tricky:
    https://numpy.org/doc/stable/user/basics.subclassing.html
    
    The defaults provide a complex array with 1024 zeros.
    """
    if issubclass(type(I), NP.ndarray):
      # I data are provided
      n_I = len(I)
      if issubclass(type(Q), NP.ndarray):
        # Q data are also provided
        n_Q = len(Q)
        if n_Q == n_I:
          M = n_I
        else:
          # truncate the longer array
          M = min(n_I, n_Q)
        dtype = complex
      else:
        # no Q data so this is a real (not analytic) signal
        M = n_I
        dtype = float
    # create a new ndarray object
    if issubclass(type(I), NP.ndarray) and issubclass(type(Q), NP.ndarray):
      obj = super(DigitalSignal, subtype).__new__(subtype, (M,), dtype=complex)
      obj.info = {"mode": "complex"}
    elif issubclass(type(I), NP.ndarray):
      obj = super(DigitalSignal, subtype).__new__(subtype, (M,), dtype=float)
      obj.info = {"mode": "real"}
    elif issubclass(type(Q), NP.ndarray):
      raise ValueError("DigitalSignal: cannot create signal from Q alone")
    else:
      # default
      obj = super(DigitalSignal, subtype).__new__(subtype, (M,), dtype=complex)
      obj.info = {"mode": "complex"}
    # now fill in the data
    if issubclass(type(I), NP.ndarray):
      obj.real = I
      if issubclass(type(Q), NP.ndarray):
        if issubclass(type(I), NP.ndarray) == False:
          obj.real = NP.zeros(n_Q)
        else:
          obj.imag = NP.zeros(n_I)
        obj.imag = Q
    elif M:
      obj.real = NP.zeros(M)
      obj.imag = NP.zeros(M)
    if rms:
      scale = rms/math.sqrt(2)
      obj.real += NP.random.normal(0, scale, size=M)
      obj.imag += NP.random.normal(0, scale, size=M)
    return obj
    
  def spectrum(self):
    """
    Returns the spectrum of the signal, positive frequencies only if the signal
    is only real values.
    """
    if self.info["mode"] == "real":
      return SP.fft.rfft(self.real)
    else:
      return SP.fft.fft(self)

  def __array_finalize__(self, obj):
    """
    redefine superclass method to add attribute
    """
    if obj is None: return
    self.info = getattr(obj, 'info', None)


class SignalGenerator(object):
  """
  Simulated signal generator for making test signals
  
  Method ``signal()`` returns a DigitalSignal object with the specified 
  properties.  The attribute ``S`` has a complex signal.
  
  If ``components`` are specified, it is a Fourier series.  If not, it is
  random Gaussian noise.
  
  Attrs
  =====
  
    components - (list of lists) of Fourier components
    m -          (int) data indices
    mode -       (str) "real", "analytic", or "complex"
    S -          (DigitalSignal) dtype=complex ndarray subclass
  """
  def __init__(self, mode="analytic", M=1024, components=None, rms=None):
    """
    Create a complex signal of M from the list of components
      
    If ``mode=="real"`` or ``mode=="analytic"``, each component is a list
    with::
    
      amplitude - (float)
      frequency - (float) number of cycles within data set
      phase -     (float) as a cycle fraction
    
    representing::
    
                          i (<frequency> t - <phase>)
      S(t) = <amplitude> e
      
    The created ``DigitalSignal`` object mode is ``"complex"``.
    each component is a list with::
    
      frequency -             (float) number of cycles within data set
      real coefficient -      (float) amplitude of cos() part of signal
      imaginary coefficient - (float) amplitude of sin() part of signal
    
    representing::
    
      S(t) = <real coef> cos(<frequency> t) + i <imag coef> sin(<frequency> t)
    
    Notes
    =====
    1) Note that that the imaginary coefficient is defined so that::
    
      V = re(V) + i im(V) = I + i Q
    
    in the quadrature I,Q signal convention.
      
    2) Phases define the zero crossing of sine functions by ``t = phase`` so
    the function is ``sin(t - phase)``.
    """
    self.logger = logging.getLogger(logger.name+".SignalGenerator")
    self.m = NP.arange(M)
    self.M = M
    self.mode = mode
    self.components = components
    self.S = DigitalSignal(M) # creates an empty signal
    if components:
      self.S.info["mode"] = mode.lower()
      self.logger.debug("__init__: generating '%s' signal with %d components",
                        mode, len(components))
      if mode.lower() in "real":
        warnings.filterwarnings(action="ignore", category=NP.ComplexWarning)
        self.S = self.S.astype(float) # redefine as float
        warnings.resetwarnings()
        for comp in components:
          self.S += comp[0]*NP.cos(2*NP.pi*(comp[1]*self.m/M + comp[2])) 
          idx = components.index(comp)
          self.S.info[idx] = {}
          self.S.info[idx]["ampl"] = comp[0]
          self.S.info[idx]["freq"] = comp[1]
          self.S.info[idx]["phas"] = comp[2]
      elif mode.lower() in "analytic":
        # creating a signal from frequency components is an inverse Fourier
        # transform, so the sign in the exponent is "+"
        for comp in components:
          self.S += comp[0]*NP.exp(2*NP.pi*1j*(comp[1]*self.m/M + comp[2]))/2
          idx = components.index(comp)
          self.S.info[idx] = {}
          self.S.info[idx]["ampl"] = comp[0]
          self.S.info[idx]["freq"] = comp[1]
          self.S.info[idx]["phas"] = comp[2]
      elif mode.lower() in "complex":
        s = NP.zeros(M,complex) # initialize cos and sin arrays
        for comp in components:
          s.real = NP.cos(2*NP.pi*comp[0]*self.m/M)
          s.imag = NP.sin(2*NP.pi*comp[0]*self.m/M)
          self.S += s*complex(comp[1],comp[2])
          idx = components.index(comp)
          self.S.info[idx] = {}
          self.S.info[idx]["freq"] = comp[0]
          self.S.info[idx]["ampI"] = comp[1]
          self.S.info[idx]["ampQ"] = comp[2]
      else:
        raise ValueError("%s mode is not valid" % mode)
    if rms:
      self.add_noise()
      
  def add_noise(self, fraction=1):
    """
    Adds Gaussian noise to the signal
    """
    if self.mode == "complex" or self.mode == "analytic":
      scale = fraction/math.sqrt(2)
      self.S.real += NP.random.normal(0, scale, size=self.M)
      self.S.imag += NP.random.normal(0, scale, size=self.M)
    else:
      self.S += NP.random.normal(0, fraction, size=self.M)

  def show_components(self, in_mode="analytic"):
    """
    show the signal components in the specified mode
    """
    if self.components:
      response = []
      if in_mode == self.mode:
        return self.components
      elif in_mode == "real" or in_mode == "analytic":
        # both modes use amp,freq,phase format
        if self.mode == "complex":
          for comp in self.components:
            # "complex" components are 'freq', 'real', 'imag'
            frq = comp[0]
            amp, phs = rect_to_polar(comp[1:])
            phs /= (2*math.pi)
            response.append([amp, frq, phs])
          return response
        else:
          return self.components
      elif in_mode == "complex":
        # must be either in "real" or "analytic" mode now
        response.append(comp[1], 
                        comp[0]*math.cos(2*pi*comp[2]), 
                        comp[0]*math.sin(2*pi*comp[2]))
    else:
      return None
  
  def signal(self):
    """
    """
    if self.mode == "real":
      return self.S.real
    else:
      return self.S
    
class OTFConvolver(object):
  """
  On-the-fly convolution tool
  
  If the convolver is initialized with data, those data are processed.  If not,
  the ``next()`` method will process one sample, returning None until there are
  enough samples to process.
  
  Attrs
  =====
  
    circ_buf - (list of float)
    data -     (list of float) history of all input samples
    F -        (ndarray) FIR filter
    filtered - (list of float) history of all filtered samples
    K -        (int) number of taps in F
    M -        (int) length of data (if provided)
    oldest -   (int) pointer to current data
  """
  def __init__(self, FIRfilter, data=None):
    """
    initialize a convolver
    
    Args:
      FIRfilter - (iterable of float) FIR filter responses
      data -      (iterable of float) optional samples to process
    """
    self.logger = logging.getLogger(logger.name+".OTFConvolver")
    self.F = FIRfilter
    self.K = len(FIRfilter)
    self.circ_buf = NP.zeros(self.K).astype(complex)
    self.filtered = []
    self.oldest = 0
    if data: # just process the data and return the result as `filtered`.
      self.data = data
      self.M = len(data)
      for midx in list(range(self.M)):
        self.filtered.append(self.convolution_step(sample))
    else:
      self.data = []
    
  def next(self, sample):
    """
    perform a step with the circular buffer convolver
    
    The convolver requires K samples to work on, one for each filter tap.
    """
    self.data.append(sample)
    idx = len(self.data)
    self.logger.debug("next: there are now %d data samples", idx)
    # do we have enough data in the buffer?
    if idx < self.K:
      # no; add data to buffer
      self.circ_buf[idx] = sample
      self.filtered.append(0.)
      return None
    else:
      self.filtered.append(self.convolution_step(sample))
      return self.filtered[-1]
    
  def convolution_step(self, sample):
    """
    cross-correlation with a circular buffer
    
    This inserts 'raw_data' into the position in circular buffer 'S' indicated
    by the index 'oldest' and then applies the filter 'F' to the data in 'S'.
    It returns the sum, the modified signal array, and the new index.
    
    Notes
    =====
    The FORTRAN-like version would be::
    
      sum=0
      S[oldest] = raw_data
      for n in list(range(K)):
        sum += F[n]*S[(oldest + n) % K]
      oldest=(oldest+1) % K
    
    Pointer setting: Because Python ranges are defined by current:last+1, the
    pointer must be updated before the multiplication with the filter is done.
    """
    self.logger.debug(":convolution_step: oldest sample is %d", self.oldest)
    sumprod = (self.F * NP.append(self.circ_buf[self.oldest:],
                                  self.circ_buf[:self.oldest])).sum()
    self.filtered.append(sumprod)
    self.oldest = (self.oldest+1) % self.K
    self.logger.debug(":convolution_step: oldest sample is now %d", self.oldest)
    self.circ_buf[self.oldest] = sample
    return sumprod

class BasicMixer(object):
  """
  Multiplies a signal with an LO to produce a IF
  
  Attrs
  =====
    logger - (logging.Logger)
  """
  def __init__(self, signal=None, LO=None):
    """
    Args:    
      signal - signal numpy array with shape (M,)
      LO     - local oscillator numpy array with shape (M,)
    
    If both signal and LO are provided, they are mixed, the longer truncated if
    needed.
    """
    self.logger = logging.getLogger(logger.name+".BasicMixer")
    self.logger.debug("__init__: signal is {}, LO is {}".format(
                      type(signal), type(LO)))
    if type(signal) == type(None) or type(LO) == type(None):
      self.IF = None
    else:
      self.logger.debug("__init__: {} signal, {} LO".format(
                        signal.dtype, LO.dtype))
      if issubclass(type(signal),NP.ndarray) and issubclass(type(LO),NP.ndarray):
        self.IF = BasicMixer.mixed(self,signal,LO)
      else:
        self.IF = None
    self.logger.debug("__init__: completed")
  
  def mixed(self, signal, LO):
    """
    Returns DigitialSignal product, truncating longer array if necessary
    """
    # make signal and LO the same length
    n_signal = len(signal)
    n_LO = len(LO)
    if n_signal == n_LO:
      pass
    elif n_signal > n_LO:
      self.logger.warning("mixed: signal truncated to length of LO")
      signal = signal[:n_LO]
    elif n_LO > n_signal:
      self.logger.warning("mixed: LO truncated to length of signal")
      LO = LO[:n_signal]
    self.logger.debug("mixed: signal data type is %s", signal.dtype)
    self.logger.debug("mixed: LO data type is %s", LO.dtype)
    IF = signal*LO
    self.logger.debug("mixed: IF type is %s", type(IF))
    self.logger.debug("mixed: IF data type is %s", IF.dtype)
    self.logger.debug("mixed: IF std.dev. %s", IF.std())
    if IF.dtype == float:
      self.IF = DigitalSignal(I=IF)
    elif IF.dtype == complex:
      self.IF = DigitalSignal(I=IF.real, Q=IF.imag)
    return self.IF

class SimpleMixer(BasicMixer):
  """
  Mixes a real (``float``) signal with a real LO to produce a real signal
  """
  def __init__(self, signal=None, LO=None):
    """
    If dtype of signal and LO are float, they are mixed.
    """
    mylogger = logging.getLogger(logger.name+".SimpleMixer")
    self.logger = mylogger
    if self._check_inputs(signal, LO):
      super(SimpleMixer, self).__init__(signal=signal, LO=LO)
      self.logger = mylogger # override parent's logger
    else:
      raise ValueError("signal dtype %s or LO dtype %s is wrong" %
                       (signal.dtype, LO.dtype))
  
  def _check_inputs(self, signal, LO):
    """
    checks that dtype of signal and LO are float. Nonetypes are allowed.
    """
    if issubclass(type(signal),NP.ndarray) and issubclass(type(LO),NP.ndarray):
      if signal.dtype != float:
        self.logger.error("_check_inputs: only dtype float signals allowed")
        return False
      if LO.dtype != float:
        self.logger.error("_check_inputs: only dtype float LO allowed")
        return False
      return True
      
  def mixed(self, signal, LO):
    """
    Returns IF if signal and LO are type float
    """
    #if self._check_inputs(signal, LO):
    if SimpleMixer._check_inputs(self, signal, LO):
      self.IF = BasicMixer.mixed(self, signal, LO)
      return self.IF
    else:
      return None

class ComplexMixer(BasicMixer):
  """
  Mixes a real (``float``) signal with a real LO; produces complex IF
  
  Converts the LO into an analytic signal before mixing.
  """
  def __init__(self, signal=None, LO=None):
    """
    If signal and LO data type are float, attribute IF is calculated
    """
    mylogger = logging.getLogger(logger.name+".ComplexMixer")
    self.logger = mylogger
    if self._check_inputs(signal, LO):
      super(ComplexMixer, self).__init__(signal=signal, LO=LO)
      self.logger = mylogger # override parent's logger
    else:
      raise ValueError("signal dtype %s or LO dtype %s is wrong" %
                       (signal.dtype, LO.dtype))
    # do the mixing over again with a quadrature LO
    if issubclass(type(LO),NP.ndarray) and issubclass(type(signal),NP.ndarray):
      self.IF = self.mixed(signal, LO)
    else:
      self.IF = None

  def _check_inputs(self, signal, LO):
    """
    checks that dtype of signal and LO are float.  Nonetypes allowed.
    """
    if issubclass(type(signal),NP.ndarray) and issubclass(type(LO),NP.ndarray):
      if signal.dtype != float:
        self.logger.error("_check_inputs: only dtype float signals allowed")
        return False
      if LO.dtype != float:
        self.logger.error("_check_inputs: only dtype float LO allowed")
        return False
      return True
      
  def mixed(self, signal, LO):
    """
    """
    if self._check_inputs(signal, LO):
      self.logger.info("mixed (Complex): converting LO to quadrature")
      I,Q = QuadratureHybrid().convert(LO)
      qlo = I + 1j*Q
      self.IF = BasicMixer.mixed(self, signal, qlo)
      self.IF.info["mode"] = "complex"
      return self.IF
    else:
      return None
  
class ParallelMixer(BasicMixer):
  """
  Mixes complex signal with same real (``float``) LO
  
  The I and Q parts of the signal are mixed with the same LO, as two
  ``SimpleMixer`` objects operating in parallel.  I and Q do not have to be an
  analytic signal pair.
  """
  def __init__(self, signal=None, LO=None):
    """
    IF signal and LO are correct data type, attribute IF is computed
    """
    mylogger = logging.getLogger(logger.name+".ParallelMixer")
    self.logger = mylogger
    if self._check_inputs(signal, LO):
      super(ParallelMixer, self).__init__(signal=signal, LO=LO)
    self.logger = mylogger

  def _check_inputs(self, signal, LO):
    """
    checks that dtype of signal is complex and LO is float.  Nonetypes allowed.
    """
    if issubclass(type(signal),NP.ndarray) and issubclass(type(LO),NP.ndarray):
      if signal.dtype != complex:
        self.logger.error("_check_inputs: only dtype complex signals allowed")
        return False
      if LO.dtype != float:
        self.logger.error("_check_inputs: only dtype float LO allowed")
        return False
      return True
      
  def mixed(self, signal, LO):
    """
    performs SimpleMixer mixed() on signal I and Q separately
    """
    if self._check_inputs(signal, LO):
      self.logger.debug("mixed (Parallel): signal I dtype is %s",
                         signal.real.dtype)
      self.IF = SimpleMixer.mixed(self, signal.real, LO).astype(complex)
      self.logger.debug("mixed (Parallel): IF dtype is %s", self.IF.dtype)
      self.logger.debug("mixed (Parallel): signal Q dtype is %s",
                        signal.imag.dtype)
      self.IF += 1j*SimpleMixer.mixed(self, signal.imag, LO)
      self.IF.info["mode"] = "complex"
      return self.IF
    else:
      return None


class QuadratureSplitter(object):
  """
  Copy of a real signal with an imaginary component delayed by pi/2
  
  Example::
    
    In [1]: from DSP import SignalGenerator, QuadratureSplitter, is_analytic                
    In [2]: lo = SignalGenerator(mode="real", M=1024,
                                 components=[[1,10,0]]).signal()        
    In [3]: qh = QuadratureSplitter()                                                       
    In [4]: qlo = qh.split(lo)                                                            
    In [5]: is_analytic(qlo)                                                                
    Out[5]: True
    
  """
  def __init__(self):
    pass
  
  def split(self, signal):
    """
    """
    analytic_signal = scipy.signal.hilbert(signal)/2
    return analytic_signal


class QuadratureHybrid(object):
  """
  Add components of an analytic signal with +/- pi/2 phase shift
  
  Example::
  
    In [1]: from DSP import SignalGenerator, QuadratureHybrid, is_analytic
    In [2]: signal = SignalGenerator(mode="analytic", M=256,
                                     components=[[1,10,0],[.5,-15,0]]).signal()
    In [3]: qh = QuadratureHybrid()
    In [4]: usb,lsb = qh.convert(signal)
    In [5]: from scipy.fft import rfft
    In [6]: abs(rfft(usb)).argmax(), abs(rfft(lsb)).argmax()
    Out[6]: (10, 15)
    
  """
  def __init__(self):
    pass
    
  def convert(self, signal): 
    """
    Splits the input signal with a quarter cycle phase shift.
    """
    paths = scipy.fftpack.hilbert(signal)
    return signal.real+paths.imag, signal.imag+paths.real


def sinc_filter(K, f0=0, mode="complex", factor=None, W=None, M=1024):
  """
  Creates a sinc filter of K taps at a frequency f0 with a width
  between first nulls of 1/factor.
  
  Args:
    K      - (int) number of taps
    f0     - (float) center frequency
    mode   - (str) real or complex data
    factor - (float) linear weight for tap index (or specify W and M)
    W      - (float) width of filter in frequency channels
    M      - (int) number of frequency channels
  
  Notes
  =====
  The ideal sinc filter FIR formula (from the book) is::
  
          W       /  W    \
    F  = --- sinc | --- k |
     k    M       \  M    /

  so ``factor`` is ``W/M``.
  
  Returns:
    k       - an array of tap indices centered on 0
    F       - the array of filter weights or taps
    max_tap - the maximum tap index.
    
  """
  max_tap = K/2
  k = NP.linspace(-max_tap, max_tap, K)
  if factor:
    W = factor/M
  elif W and M:
    factor = W/M
  else:
    raise RuntimeError("no filter width specified ('factor' or 'W' and 'M')")
  logger.debug("sinc_filter: W=%f, M=%d, factor=%f, freq=%f",
               W, M, factor, f0)
  # this is the sinc filter for f0 = 0
  template = factor*SP.sinc(factor*k)
  logger.debug("sinc_filter: template: %s", template)
  # shift the filter center frequency
  if mode == 'complex':
    F = template * NP.exp(-2*NP.pi*1j*f0*W*k/M)
  elif mode == 'real':
    # This factor of two is needed so that the time step and bandwidth
    # mean the same thing in both cases.
    F = 2*template * NP.cos(2*NP.pi*f0*W*k/M)
  else:
    logger.warning("Warning: sinc_filter mode '%s' returns baseband filter",
                   mode)
    F = template
  return k, F, max_tap

def interpolate(data, increase):
  """
  Interpolate data increasing the number of points by a factor of increase which
  must be a power of two.
  
  Notes
  =====
  fft() of N samples returns N spectral points. To interpolate, simply at
  ``increase-1`` times N zeros and call ``ifft()``.
  
  rfft() of N samples returns N//2+1 complex spectral points. We expect 
  N*increase new data points.  Its transform has (N*increase)//2+1 data points.
  """
  num_interp = float(increase)
  if data.dtype == complex:
    logger.debug("interpolate: %d data are complex", len(data))
    xform = SP.fft.fft(data)
    logger.debug("interpolate: transform has %d samples", len(xform))
    num_add = int((num_interp-1)*len(xform))
    extended_xform = NP.append(xform, NP.zeros(num_add, dtype=complex))
    logger.debug("interpolate: extended transform has %d samples",
                 len(extended_xform))
    interpolated = SP.fft.ifft(extended_xform)*num_interp
    x = NP.arange(len(extended_xform))/num_interp
  else:
    logger.debug("interpolate: %d data are real", len(data))
    xform = SP.fft.rfft(data)
    logger.debug("interpolate: transform has %d samples", len(xform))
    num_add = int((num_interp-1)*(len(xform)-1))
    logger.debug("interpolate: %d transform points will be added", num_add)
    extended_xform = NP.append(xform, 
                               NP.zeros(num_add, dtype=complex))
    logger.debug("interpolate: extended transform has %d samples",
                 len(extended_xform))
    interpolated = SP.fft.irfft(extended_xform)*num_interp
    x = NP.arange(2*(len(extended_xform)-1))/num_interp
    logger.debug("interpolate: %d <= x <= %d", x[0], x[-1])
  return x,interpolated

def box(x):
  """
  normalized box centered on x=0
  """
  if x < -0.5:
    return 0
  elif x == -0.5:
    return 0.5
  elif x > -0.5 and x < 0.5:
    return 1
  elif x == 0.5:
    return 0.5
  elif x > 0.5:
    return 0
  else:
    print("You can't get here")
    return

vbox = NP.vectorize(box)
def wbox(x,width):
  """
  normalized numpy compatible box of width 'w' centered on zero.
  """
  w = float(width)
  return vbox(x/w)/w

def rect_to_polar(v):
  """
  Converts complex number to exponential
  
  numpy has functions for doing this to complex arrays.
  """
  amp = math.sqrt(v.real**2+v.imag**2)
  phs = math.atan2(v.imag,v.real)
  return amp,phs

def is_quadrature(signal):
    """
    checks complex signal for quadrature
    """
    logger.debug("is_quadrature: check if signal is quadrature")
    if signal.dtype != complex:
      logger.error("is_quadrature: dtype %s signal cannot be in quadrature",
                   signal.dtype)
      return False
    else:
      if (signal*signal.conjugate()).imag.all() == 0:
        return True
      else:
        logger.error(
                     "is_quadrature: I and Q of LO are not in quadrature phase")
        return False
is_analytic = is_quadrature

if __name__ == "__main__":
  pass
