import time
import math
import scipy.interpolate


def cap(value):
    val = abs(value)
    if val > 255:
        val = 255
    return int(val)


class FixtureType(object):
    def __init__(self, name, address_length, chans):
        self.name = name
        self.address_length = address_length
        self.chans = chans


class Fixture(object):
    def __init__(self, name, start_address, address_length, chans):
        self.name = name
        self.start_address = start_address
        self.address_length = address_length
        self.chans = chans
        self.values = {}
        self.reset_values()

    def reset_values(self):
        for chan in self.chans:
            self.values[chan] = 0


class Scene(object):
    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.modifiers = []
        self.start_time = 0
        self.base_fixtures = {}

    def add_fixture(self, fixture, values):
        self.fixtures[fixture] = values

    def reset(self):
        self.start_time = time.time()
        if hasattr(self, 'modifiers'):
            for modifier in self.modifiers:
                modifier.start_time = self.start_time
        if hasattr(self, 'base_fixtures'):
            for fixture, values in self.base_fixtures.iteritems():
                for chan, value in values.iteritems():
                    if not isinstance(value, int):
                        value.start_time = self.start_time

    @property
    def fixtures(self):
        if not self.modifiers:
            return self.base_fixtures
        else:
            fixtures = {}
            for fixture, values in self.base_fixtures.iteritems():
                fixtures[fixture] = {}
                for chan, value in values.copy().iteritems():
                    if isinstance(value, int):
                        fixtures[fixture][chan] = value
                    else:
                        fixtures[fixture][chan] = value.calc_value()
            for fixture, values in fixtures.iteritems():
                for chan, value in values.copy().iteritems():
                    for modifier in self.modifiers:
                        if fixture.name in modifier.fixtures:
                            for channel in modifier.fixtures[fixture.name]:
                                if channel == chan:
                                    fixtures[fixture][chan] = modifier.calc_value(value)
            return fixtures


class TransitionScene(Scene):
    def __init__(self, name, manager, start_scene, end_scene, timeout=30):
        self.name = name
        self.manager = manager
        self.start_scene = start_scene
        self.end_scene = end_scene
        self.end_scene.reset()
        self.start_time = 0
        self.timeout = timeout


class Modifier(object):
    def __init__(self, name, scene, data, mode="local"):
        self.start_time = 0
        self.name = name
        self.scene = scene
        self.data = data
        self.mode = mode
        self.timeout = data.get('timeout', None)
        self.initial = data.get('initial', None)
        if self.mode == "global":
            self.fixtures = data['fixtures']

    def calc_value(self, value=0):
        if self.timeout:
            if time.time() - self.start_time > self.timeout:
                self.start_time = time.time()
        if self.initial:
            value = self.initial
        nval = self.calculate()
        return cap(value + nval)


class SineModifier(Modifier):
    def __init__(self, *args, **kwargs):
        super(SineModifier, self).__init__(*args, **kwargs)
        self.amp = self.data['amp']
        self.freq = self.data['freq']

    def calculate(self):
        return self.amp * math.sin(self.freq * (time.time() - self.start_time))


class CosineModifier(Modifier):
    def __init__(self, *args, **kwargs):
        super(CosineModifier, self).__init__(*args, **kwargs)
        self.amp = self.data['amp']
        self.freq = self.data['freq']

    def calculate(self):
        return self.amp * math.cos(self.freq * (time.time() - self.start_time))


class WaypointModifier(Modifier):
    def __init__(self, *args, **kwargs):
        super(WaypointModifier, self).__init__(*args, **kwargs)
        self.points = self.data['points']
        self.x = [p[0] for p in self.points]
        self.y = [p[1] for p in self.points]
        self.rep = scipy.interpolate.splrep(self.x, self.y, s=0)

    def calculate(self):
        return scipy.interpolate.splev([time.time() - self.start_time], self.rep, der=0)[0]


class FadeScene(TransitionScene):
    @property
    def fixtures(self):
        if time.time() - self.start_time > self.timeout:
            self.manager.set_scene(self.end_scene, reset=False)
        else:
            combined_fixtures = {}
            for fixture, fixture_values in self.start_scene.fixtures.iteritems():
                combined_fixtures[fixture] = fixture_values.copy()
            for fixture, fixture_values in self.end_scene.fixtures.iteritems():
                if fixture not in combined_fixtures:
                    combined_fixtures[fixture] = {}
                if fixture in self.start_scene.fixtures:
                    for chan, value in fixture_values.iteritems():
                        y0 = self.start_scene.fixtures[fixture].get(
                            chan,
                            fixture.values[chan]
                        )
                        y1 = self.end_scene.fixtures[fixture].get(
                            chan,
                            fixture.values[chan])
                        x = time.time()
                        x0 = self.start_time
                        x1 = self.start_time + self.timeout
                        y = y0 + ((y1 - y0) * ((x - x0) / (x1 - x0)))
                        combined_fixtures[fixture][chan] = int(y)
                if fixture in self.end_scene.fixtures:
                    for chan, value in fixture_values.iteritems():
                        y0 = self.start_scene.fixtures[fixture].get(
                            chan,
                            fixture.values[chan])
                        y1 = self.end_scene.fixtures[fixture].get(
                            chan,
                            fixture.values[chan])
                        x = time.time()
                        x0 = self.start_time
                        x1 = self.start_time + self.timeout
                        y = y0 + ((y1 - y0) * ((x - x0) / (x1 - x0)))
                        combined_fixtures[fixture][chan] = int(y)
            return combined_fixtures
        return self.end_scene.fixtures

mod_map = {
    'sin': SineModifier,
    'cos': CosineModifier,
    'waypoint': WaypointModifier
}
