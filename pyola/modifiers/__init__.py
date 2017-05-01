from cos import CosineModifier
from polygon import PolygonModifier
from sin import SineModifier
from spline import SplineModifier
from rand import RandomModifier
from wave import WaveModifier
from wiimote import WiiModifier


mod_map = {
    'sin': SineModifier,
    'cos': CosineModifier,
    'spline': SplineModifier,
    'polygon': PolygonModifier,
    'random': RandomModifier,
    'wave': WaveModifier,
    'wii': WiiModifier
}
