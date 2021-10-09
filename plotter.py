"""
plotting support for module DSP

  plot_data      - plots multiple data sets in one pair of axes.

  mixing_plot    - plots signal in the upper panel, spectrum of the signal and
                   LO in the middle panel, and the mixed spectrum in the lower
                   panel.
              
  signal_summary - plots a signal in the top panel, its spectrum in the middle
                   panel, and the power spectrum in the lower panel
                   
"""
import logging
import numpy as NP
from pylab import subplots

from . import interpolate

logger = logging.getLogger(__name__)


def plot_data(ax, data, interp=0,
              plot_title='',x_lbl='',y_lbl='',x_lim=(), y_lim=(),
              gridding=False, leg_loc='best'):
  """
  Plot data, which is a list of sublists, [[x,y,f,l],[x,y,f,l],...,[x,y,f,l]]
  
  Args
  ====
  
    ax -         (AxesSubplot) axis where the data will be plotted
    data -       (list of lists) with x,y,f(ormat),l(abel)
    plot_title - (str)
    x_lbl -      (str)
    y_lbl -      (str)
    x_lim -      (tuple) minimum and maximum X
    y_lim -      (tuple) minimum and maximum Y
    gridding -   (bool) whether to draw a grid
    leg_loc -    (int or str) legend location
    
  Each sublist contains::
  
    x - the independent variable array
    y - the dependent variable array
    f - format for plot line or markers
    l - the label string for this data set
    
  """
  have_legend = False
  # data must be a list of lists
  if type(data[0]) == list:
    pass
  else:
    data = [data]
  for [x,y,format,l] in data:
    if type(x) == list or type(x) == NP.ndarray:
      pass
    elif x == None:
      x = list(range(len(y)))
    else:
      logger.warning("plot_data: 'x' is type %s", type(x))
    if l == '':
      line=ax.plot(x,y,format)
    else:
      have_legend = True
      line=ax.plot(x,y,format,label=l)
    if interp > 0:
      l,interpolated = interpolate(y,interp)
      #logger.debug("plot_data: interpolated: %s", interpolated)
      c = line[-1].get_color()
      logger.debug("plot_data: line color is %s", c)
      ax.plot(x,y,'.',color=c)
      ax.plot(l,interpolated, linestyle=':', color=c)
  if plot_title != '':
    ax.set_title(plot_title)
  if x_lbl != '':
    ax.set_xlabel(x_lbl)
  if y_lbl != '':
    ax.set_ylabel(y_lbl)
  if len(x_lim) == 2:
    ax.set_xlim(x_lim)
  if len(y_lim) == 2:
    ax.set_ylim(y_lim)
  if have_legend:
    #ax.legend(loc=leg_loc, numpoints=1, bbox_to_anchor=(1.0, 0.5, 0.3,0.6))
    #elif have_legend:
    ax.legend(loc=leg_loc, numpoints=1)
  if gridding:
    ax.grid(True)
  return

def mixing_plot(signal, lo, mx, modecode, show=False):
  """
  plots the results of mixing tests
  """
  modes = {"a": "analytic", "c": "complex", "r": "real", "s": "simple"}
  
  fig,ax = subplots(nrows=3, ncols=1, figsize=(8,8))
  # upper panel for input signal
  ax[0].plot(signal.real, label="real")
  ax[0].plot(signal.imag, label="imag")
  ax[0].set_title(modes[modecode[0]]+" Signal")
  ax[0].grid(True)
  ax[0].legend()
  # middle panel for signal and LO spectra
  ax[1].plot(signal.spectrum().real+1, label="signal real")
  ax[1].plot(signal.spectrum().imag-1, label="signal imag")
  ax[1].plot(lo.spectrum().real+2, label="LO real")
  ax[1].plot(lo.spectrum().imag-2, label="LO imag")
  ax[1].set_title("Signal and LO Spectrum")
  ax[1].grid(True)
  ax[1].legend()
  # lower panel for mixed signal
  ax[2].plot(mx.spectrum().real+1, label="real")
  ax[2].plot(mx.spectrum().imag-1, label="imag")
  ax[2].set_title(modes[modecode[1]]+" Mixer Mode IF Spectrum")
  ax[2].grid(True)
  ax[2].legend()
  fig.suptitle("{} signal mode, {} LO mode, {} mixer mode".format(
       modes[modecode[0]], modes[modecode[1]], modes[modecode[2]]))
  if show:
    fig.show()
    figname = "mix_test-"+modecode+".png"
    fig.savefig(figname)
    print("figure %s saved: %s" % (fig.number, figname))

def signal_summary(signal, spectrum, gridding=True):
  """
  Plots a real or analytic signal, its spectrum, and its power spectrum
  
  Each is in a separate panel, which are arranged vertically.
  """
  fig,ax = subplots(nrows=3, ncols=1, figsize=(8,8))
  plot_data(ax[0], [[None, signal.real, '-', "real"]],
            plot_title="Signal", gridding=True)
  sigmode = signal.info['mode']
  if sigmode != "real":
    plot_data(ax[0], [[None, signal.imag, '-', "imag"]])
  plot_data(ax[1], [[None, spectrum.real+20, '-', "real"],
                    [None, spectrum.imag-20, '-', "imag"]],
            plot_title="Spectrum", gridding=True)
  plot_data(ax[2], [[None, spectrum*spectrum.conjugate(), '-', "Power"]],
            plot_title="Power Spectrum", gridding=True)

  fig.suptitle("signal mode {}".format(sigmode))
  fig.show()
plot_signal_summary = signal_summary

def display_signals(sig_spec_pairs):
  """
  display rows of signals in three columns with signal, spectrum, and phase
  """
  nrows=len(sig_spec_pairs)
  fig1, ax1 = subplots(nrows=nrows, ncols=3, figsize=(9,nrows*3))
  for idx in list(range(nrows)):
    x, signal, spec = sig_spec_pairs[idx]
    xbase = x.max()-x.min()
    # left panel: signal
    if signal.dtype == float:
      plot_data(ax1[idx,0], [[x, signal, "b-", "V"]],
                plot_title="signal ("+str(len(x))+" samples)", gridding=True)
    elif signal.dtype == complex:
      I = signal.real
      Q = signal.imag
      plot_data(ax1[idx,0], [[x, I, "r--", "I"],
                             [x, Q, "g--", "Q"]],
                plot_title="Analytic signal", gridding=True, x_lbl="time")
    # center panel: spectrum
    f = NP.arange(len(spec))/xbase
    plot_data(ax1[idx,1], 
              [[f, spec.real, "r-", r"$\Re(\mathcal{V})$"],
               [f, spec.imag, "g-", r"$\Im(\mathcal{V})$"],
               [f, abs(spec), "k:", r"$|\mathcal{V}|$"]],
              plot_title="spectrum", gridding=True)
    # right panel: phases
    if idx == nrows-1:
      # bottom row
      plot_data(ax1[idx,2], [[None, NP.angle(spec)/2/NP.pi, ".", ""]],
                x_lbl="frequency", y_lbl="cycles", gridding=True, 
                leg_loc="lower left")
    else:
      plot_data(ax1[idx,2], [[None, NP.angle(spec)/2/NP.pi, ".", ""]],
                plot_title="phase", gridding=True, y_lbl="cycles")
    ax1[idx,2].yaxis.set_label_position("right")
  fig1.show()
  return fig1


