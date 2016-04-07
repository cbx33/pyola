from conf import load_fixtures, load_scenes, load_fixture_types
from objects import FadeScene
import array
import time
from ola.ClientWrapper import ClientWrapper
from Tkinter import *

wrapper = ClientWrapper()


def DmxSent(state):
    if not state.Succeeded():
        wrapper.Stop()


class Manager(object):
    def __init__(self):
        self.fixture_types = load_fixture_types()
        self.fixtures = load_fixtures(self.fixture_types)
        self.scenes = load_scenes(self)
        self.current_scene = None

    def set_scene(self, scene):
        self.current_scene = scene
        self.current_scene.reset()

    def run(self):
        while True:
            rdata = array.array('B')
            for i in range(0, 512):
                rdata.append(0)

            # Use the scene to set the fixtures values
            for fixture, values in self.current_scene.fixtures.iteritems():
                for chan, value in values.iteritems():
                    #chan_value = self.fixtures[fixture.name].chans[chan]
                    self.fixtures[fixture.name].values[chan] = value


            for fixture_name, fixture in self.fixtures.iteritems():
                print fixture.values
                for chan, value in fixture.values.iteritems():
                    chan_value = self.fixtures[fixture.name].chans[chan]
                    rdata[fixture.start_address + chan_value - 2] = value
            wrapper.Client().SendDmx(1, rdata, DmxSent)
            time.sleep(.01)

if __name__ == "__main__":
    Tk()
    manager = Manager()
    trans_scene = FadeScene("fade", manager, manager.scenes['scene1'], manager.scenes['scene2'], 5)
    manager.set_scene(trans_scene)
    manager.run()
