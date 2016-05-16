import time
import random

from base import Modifier
from utils import get_val_from_const


class RandomModifier(Modifier):
    def __init__(self, *args, **kwargs):
        super(RandomModifier, self).__init__(*args, **kwargs)
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
