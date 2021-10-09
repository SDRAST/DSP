"""
test_signals
"""
import logging
import unittest

from DSP.tests import SignalProber

logger = logging.getLogger(__name__)

class SignalTester(unittest.TestCase):
  """
  """
  def setUp(self):
    """
    """
    self.logger = logging.getLogger(logger.name+".MixerTester")
    self.tester = SignalProber()

  def test_empty_signal(self):
    """
    """
    self.assertTrue(self.tester.empty_signal())
  
  def test_noisy_signal(self):
    """
    """
    self.assertTrue(self.tester.noisy_signal())

  def test_real_signal(self):
    """
    """
    self.assertTrue(self.tester.test_SG("real")[0])
  
  def test_analytic_signal(self):
    """
    """
    self.assertTrue(self.tester.test_SG("analytic")[0])
  
  def test_complex_signal(self):
    """
    """
    self.assertTrue(self.tester.test_SG("complex")[0])
  
  def test_quad_hybrid(self):
    """
    """
    self.assertTrue(self.tester.test_QH()[0])
  
if __name__ == "__main__":
  unittest.main()
  
