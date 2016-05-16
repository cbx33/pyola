import cwiid
import threading

from base import Modifier


class WiiManager(object):
    def __init__(self):
        self.wm = None

    def run(self):
        print "Press 1+2"
        self.wm = cwiid.Wiimote()
        self.wm.rpt_mode = cwiid.RPT_ACC
        self.wm.led = cwiid.LED2_ON

    @property
    def state(self):
        if self.wm:
            return self.wm.state
        else:
            return 0


wii = WiiManager()
wii_thread = threading.Thread(target=wii.run)
wii_thread.daemon = True
wii_thread.start()


class WiiModifier(Modifier):
    def __init__(self, *args, **kwargs):
        super(WiiModifier, self).__init__(*args, **kwargs)
        self.chan = self.data.get('chan', None)

    def calculate(self):
        if self.chan == 1:
            num = wii.state['acc'][1]
            num = 255 - num - 127
            num = num / 26.0
            num = num * 255
        if self.chan == 0:
            num = wii.state['acc'][0]
            num = 255 - num - 102
            num = num / 51.0
            num = num * 255
        return num
