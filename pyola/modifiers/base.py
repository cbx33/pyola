import time

from utils import get_val_from_const, cap


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
