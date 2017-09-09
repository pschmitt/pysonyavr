pysonyavr
=========

These Python bindings are intended to interact with modern Sony speakers.

**NOTE** This library has only been tested with a Sony SRS-ZR7. It may not work
reliably with other Sony speakers. Feel free to open an issue if your are having
trouble with your device.


Code sample
-----------

.. code:: python

  from pysonyavr import SonyAvr
  s = SonyAvr('10.0.0.18')
  s.turn_on()
  # Switch to AUX input
  s.set_input('audio in')
  s.raise_volume()
  s.mute()
  s.unmute()
  s.turn_off()
