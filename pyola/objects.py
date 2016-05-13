# Add Phase offset
import time
import math
import scipy.interpolate
import random
import cwiid
import threading


def cap(value):
    if value > 255:
        value = 255
    if value < 0:
        value = 0
    return int(value)


def get_val_from_const(value, constants, chan=None):
    if value is None:
        return None
    elif isinstance(value, basestring):
        if chan and isinstance(constants[value], dict) and chan in constants[value]:
            return constants[value][chan]
        else:
            return constants[value]
    else:
        return value


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

    def add_fixture(self, fixture, values):
        self.base_fixtures[fixture] = values

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
        self.name = name
        self.manager = manager
        self.start_scene = start_scene
        self.end_scene = end_scene
        self.end_scene.reset()
        self.start_time = 0
        self.timeout = timeout


class Modifier(object):
    def __init__(self, name, scene, data, manager, mode="local"):
        self.start_time = 0
        self.name = name
        self.scene = scene
        self.data = data
        self.manager = manager
        self.mode = mode
        self.timeout = self.data.get('timeout', None)
        self.initial = get_val_from_const(self.data.get('initial', None), self.manager.constants)
        if self.mode == "global":
            self.fixtures = data['fixtures']

#    @property
#    def initial(self):
#        base_data = self.data.get('initial', None)
#        if isinstance(base_data, basestring):
#            return self.manager.constants[base_data]
#        else:
#            return base_data

    @property
    def current_time(self):
        return time.time() - self.start_time

    def calc_value(self, value=0):
        if self.timeout:
            if time.time() - self.start_time > self.timeout:
                self.start_time = time.time()
        if self.initial:
            value = self.initial
        nval = self.calculate()
        return cap(value + nval)


class FlashingModifier(Modifier):
    def __init__(self, *args, **kwargs):
        super(FlashingModifier, self).__init__(*args, **kwargs)
        self.flash_start = None
        {'type': 'flasher', 'prob': .5, 'duration': .1, 'initial': 0, max: 255}
        self.prob = get_val_from_const(self.data.get('prob', None), self.manager.constants)
        self.duration = get_val_from_const(self.data.get('duration', None), self.manager.constants)
        self.max = get_val_from_const(self.data.get('max', None), self.manager.constants)

    def calculate(self):
        if self.flash_start:
            if time.time() - self.flash_start >= self.duration:
                self.flash_start = None
                val = 0
            else:
                val = self.max
        else:
            if random.random() < self.prob:
                self.flash_start = time.time()
                val = self.max
            else:
                val = 0
        return val


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


class SineModifier(Modifier):
    def __init__(self, *args, **kwargs):
        super(SineModifier, self).__init__(*args, **kwargs)
        self.amp = get_val_from_const(self.data.get('amp', None), self.manager.constants)
        self.freq = get_val_from_const(self.data.get('freq', None), self.manager.constants)

    def calculate(self):
        return self.amp * math.sin(self.freq * (self.current_time))


class CosineModifier(Modifier):
    def __init__(self, *args, **kwargs):
        super(CosineModifier, self).__init__(*args, **kwargs)
        self.amp = get_val_from_const(self.data.get('amp', None), self.manager.constants)
        self.freq = get_val_from_const(self.data.get('freq', None), self.manager.constants)

    def calculate(self):
        return self.amp * math.cos(self.freq * (self.current_time))


class WaypointMixin(object):
        def normalize_points(self, points, consts):
            new_points = []
            for point in points:
                point_val = get_val_from_const(point[1], consts)
                new_points.append([point[0], point_val])
            return new_points


class WaypointModifier(Modifier, WaypointMixin):
    def __init__(self, *args, **kwargs):
        super(WaypointModifier, self).__init__(*args, **kwargs)
        self.points = self.normalize_points(self.data['points'], self.manager.constants)
        print self.points
        self.x = [p[0] for p in self.points]
        self.y = [p[1] for p in self.points]
        self.rep = scipy.interpolate.splrep(self.x, self.y, s=0)

    def calculate(self):
        print scipy.interpolate.splev([self.current_time], self.rep, der=0)[0]
        return cap(scipy.interpolate.splev([self.current_time], self.rep, der=0)[0])


class FlatWaypointModifier(Modifier, WaypointMixin):
    def __init__(self, *args, **kwargs):
        super(FlatWaypointModifier, self).__init__(*args, **kwargs)
        self.points = self.normalize_points(self.data['points'], self.manager.constants)

    def calculate(self):
        best_match = self.points[0]
        for point in self.points:
            if point[0] >= self.current_time:
                break
            else:
                best_match = point
        return best_match[1]


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

mod_map = {
    'sin': SineModifier,
    'cos': CosineModifier,
    'waypoint': WaypointModifier,
    'immediate': FlatWaypointModifier,
    'flasher': FlashingModifier,
    'wii': WiiModifier
}
