import math

from base import Modifier
from utils import get_val_from_const


class CosineModifier(Modifier):
    def __init__(self, *args, **kwargs):
        super(CosineModifier, self).__init__(*args, **kwargs)
        self.amp = get_val_from_const(self.data.get('amp', None), self.manager.constants)
        self.freq = get_val_from_const(self.data.get('freq', None), self.manager.constants)
        self.offset = get_val_from_const(self.data.get('offset', 0), self.manager.constants)

    def calculate(self):
        return self.amp * math.cos((self.freq * self.current_time) + self.offset)
