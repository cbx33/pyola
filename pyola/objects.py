import time


class Fixture(object):
    def __init__(self, name, start_address, address_length):
        self.name = name
        self.start_address = start_address
        self.address_length = address_length
        self.values = []
        self.reset_values()

    def reset_values(self):
        for i in range(self.address_length):
            self.values.append(0)


class Scene(object):
    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.modifiers = []
        self.start_time = 0
        self.fixtures = {}

    def add_fixture(self, fixture_name, values):
        self.fixtures[fixture_name] = values

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
            for fixture_name, fixture_values in self.start_scene.fixtures.iteritems():
                combined_fixtures[fixture_name] = fixture_values
            for fixture_name, fixture_values in self.end_scene.fixtures.iteritems():
                if not fixture_name in combined_fixtures:
                    combined_fixtures[fixture_name] = {}
                if fixture_name in self.start_scene.fixtures:
                    for chan, value in fixture_values.iteritems():
                        y0 = self.start_scene.fixtures[fixture_name].get(chan, self.manager.fixtures[fixture_name].values[chan - 1])
                        y1 = self.end_scene.fixtures[fixture_name].get(chan, self.manager.fixtures[fixture_name].values[chan - 1])
                        x = time.time()
                        x0 = self.start_time
                        x1 = self.start_time + self.timeout
                        y = y0 + ((y1 - y0) * ((x - x0) / (x1 - x0)))
                        combined_fixtures[fixture_name][chan] = int(y)
                if fixture_name in self.end_scene.fixtures:
                    for chan, value in fixture_values.iteritems():
                        y0 = self.start_scene.fixtures[fixture_name].get(chan, self.manager.fixtures[fixture_name].values[chan - 1])
                        y1 = self.end_scene.fixtures[fixture_name].get(chan, self.manager.fixtures[fixture_name].values[chan - 1])
                        x = time.time()
                        x0 = self.start_time
                        x1 = self.start_time + self.timeout
                        y = y0 + ((y1 - y0) * ((x - x0) / (x1 - x0)))
                        combined_fixtures[fixture_name][chan] = int(y)
            return combined_fixtures
        return self.end_scene.fixtures
