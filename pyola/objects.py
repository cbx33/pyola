# Add Phase offset
import time


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
        self.override = {}
        self.sliders = {}
        for chan in self.chans:
            self.override[chan] = None

    def reset_values(self):
        for chan in self.chans:
            self.values[chan] = 0


class Scene(object):
    def __init__(self, name, manager, data):
        self.name = name
        self.data = manager
        self.raw_data = data
        self.modifiers = []
        self.start_time = 0
        self.base_fixtures = {}
        self.timeout = self.raw_data.get('timeout', None)
        self.auto_advance = self.raw_data.get('auto_advance', {})
        self.default_trans = None

    def add_fixture(self, fixture, values):
        self.base_fixtures[fixture] = values

    def stop(self):
        if hasattr(self, 'base_fixtures'):
            for fixture, values in self.base_fixtures.iteritems():
                for chan, value in values.iteritems():
                    if not isinstance(value, int):
                        value.stop()

    def reset(self):
        print "RESETTING"
        self.start_time = time.time()
        if hasattr(self, 'modifiers'):
            for modifier in self.modifiers:
                modifier.start_time = self.start_time
        if hasattr(self, 'base_fixtures'):
            for fixture, values in self.base_fixtures.iteritems():
                for chan, value in values.iteritems():
                    if not isinstance(value, int):
                        value.start_time = self.start_time
                        value.play()

    @property
    def fixtures(self):
        if self.timeout:
            if time.time() - self.start_time > self.timeout:
                self.reset()
        fixtures = self.base_fixtures.copy()
        for fixture, values in self.base_fixtures.iteritems():
            fixtures[fixture] = {}
            for chan, value in values.copy().iteritems():
                if isinstance(value, int):
                    fixtures[fixture][chan] = value
                else:
                    fixtures[fixture][chan] = value.calc_value()
        if self.modifiers:
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
        self.auto_advance = {}
        self.name = name
        self.manager = manager
        self.start_scene = start_scene
        self.end_scene = end_scene
        self.end_scene.reset()
        self.start_time = 0
        self.timeout = timeout


class FadeScene(TransitionScene):
    @property
    def fixtures(self):
        if time.time() - self.start_time > self.timeout:
            self.manager.set_scene(self.end_scene, reset=False)
            self.start_scene.stop()
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
                        if fixture not in self.start_scene.fixtures:
                            continue
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
