import time
import math


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

    @property
    def fixtures(self):
        if not self.modifiers:
            return self.base_fixtures
        else:
            fixtures = {}
            for fixture, values in self.base_fixtures.iteritems():
                fixtures[fixture] = {}
                for chan, value in values.copy().iteritems():
                    fixtures[fixture][chan] = value
            for fixture, values in fixtures.iteritems():
                for chan, value in values.copy().iteritems():
                    for modifier in self.modifiers:
                        if fixture.name in modifier.fixtures:
                            for channel in modifier.fixtures[fixture.name]:
                                if channel == chan:
                                    fixtures[fixture][chan] = modifier.calc_value(value)
                                    #re calc value
            return fixtures

class TransitionScene(Scene):
    def __init__(self, name, manager, start_scene, end_scene, timeout=30):
        self.name = name
        self.manager = manager
        self.start_scene = start_scene
        self.end_scene = end_scene
        self.start_time = 0
        self.timeout = timeout


class Modifier(object):
    def __init__(self, name, scene):
        self.name = name
        self.scene = scene


class SineModifier(Modifier):
    def __init__(self, name, scene, data):
        self.name = name
        self.scene = scene
        self.amp = data['amp']
        self.freq = data['freq']
        self.fixtures = data['fixtures']

    def calc_value(self, value):
        new_value = self.amp * math.sin(self.freq * (time.time() - self.scene.start_time))
        return cap(value + new_value)

class CosineModifier(Modifier):
    def __init__(self, name, scene, data):
        self.name = name
        self.scene = scene
        self.amp = data['amp']
        self.freq = data['freq']
        self.fixtures = data['fixtures']

    def calc_value(self, value):
        new_value = self.amp * math.cos(self.freq * (time.time() - self.scene.start_time))
        return cap(value + new_value)


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
    'cos': CosineModifier
}
