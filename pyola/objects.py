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

    def reset_values(self):
        for chan in self.chans:
            self.values[chan] = 0


class Scene(object):
    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.modifiers = []
        self.start_time = 0
        self.fixtures = {}

    def add_fixture(self, fixture, values):
        self.fixtures[fixture] = values

    def reset(self):
        self.start_time = time.time()


class TransitionScene(Scene):
    def __init__(self, name, manager, start_scene, end_scene, timeout=30):
        self.name = name
        self.manager = manager
        self.start_scene = start_scene
        self.end_scene = end_scene
        self.start_time = 0
        self.timeout = timeout


class Modifier(object):
    def __init__(self, name):
        self.name = name


class FadeScene(TransitionScene):
    @property
    def fixtures(self):
        if time.time() - self.start_time > self.timeout:
            self.manager.set_scene(self.end_scene)
        else:
            combined_fixtures = {}
            for fixture, fixture_values in self.start_scene.fixtures.iteritems():
                combined_fixtures[fixture] = fixture_values
            for fixture, fixture_values in self.end_scene.fixtures.iteritems():
                if not fixture in combined_fixtures:
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
