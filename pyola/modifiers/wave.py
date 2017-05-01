from scipy.io import wavfile
from base import Modifier
from utils import get_val_from_const

MAX = 32768.0

filedata = {}

from gi.repository import Gst
Gst.init(None)


class WaveModifier(Modifier):
    def __init__(self, *args, **kwargs):
        super(WaveModifier, self).__init__(*args, **kwargs)
        self.master = self.data.get('master', False)
        self.filename = self.data.get('filename', None)
        self.amp = get_val_from_const(self.data.get('amp', None), self.manager.constants)
        self.name = self.data.get('name', None)
        if self.name not in filedata:
            filedata[self.name] = wavfile.read(self.filename)
        self.toggle = False

    def play(self):
        if self.master:
            self.pl = Gst.ElementFactory.make("playbin", "player")
            # copy a track to /tmp directory, just for testing
            self.pl.set_property('uri', 'file://{}'.format(self.filename))
            # setting the volume property for the playbin element, as an example
            self.pl.set_property('volume', 0.2)

            # running the playbin
            self.pl.set_state(Gst.State.PLAYING)

    def stop(self):
        if self.master:
            self.pl.set_state(Gst.State.PAUSED)

    def calculate(self):
        idx = int(self.current_time * filedata[self.name][0])
        if idx > len(filedata[self.name][1]):
            return 0
        return abs(filedata[self.name][1][idx][0] / MAX) * 255
