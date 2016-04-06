from conf import load_fixtures, load_scenes
from objects import FadeScene
import array
import time
from ola.ClientWrapper import ClientWrapper

wrapper = ClientWrapper()


def DmxSent(state):
    if not state.Succeeded():
        wrapper.Stop()


class Manager(object):
    def __init__(self):
        self.fixtures = load_fixtures()
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
            for fixture_name, fixture in self.current_scene.fixtures.iteritems():
                for chan, value in fixture.iteritems():
                    self.fixtures[fixture_name].values[chan - 1] = value

            for fixture_name, fixture in self.fixtures.iteritems():
                for i, value in enumerate(fixture.values):
                    rdata[fixture.start_address + i - 1] = value
            wrapper.Client().SendDmx(1, rdata, DmxSent)
            time.sleep(.1)

if __name__ == "__main__":
    manager = Manager()
    trans_scene = FadeScene("fade", manager, manager.scenes['scene1'], manager.scenes['scene2'], 3)
    manager.set_scene(trans_scene)
    manager.run()
