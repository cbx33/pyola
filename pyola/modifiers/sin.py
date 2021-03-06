import math

from base import Modifier
from utils import get_val_from_const


class SineModifier(Modifier):
    def __init__(self, *args, **kwargs):
        super(SineModifier, self).__init__(*args, **kwargs)
        self.amp = get_val_from_const(self.data.get('amp', None), self.manager.constants)
        self.freq = get_val_from_const(self.data.get('freq', None), self.manager.constants)

    def calculate(self):
        return self.amp * math.sin(self.freq * (self.current_time))
