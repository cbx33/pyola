import scipy.interpolate

from base import Modifier
from utils import cap
from waypoint import WaypointMixin


class SplineModifier(Modifier, WaypointMixin):
    def __init__(self, *args, **kwargs):
        super(SplineModifier, self).__init__(*args, **kwargs)
        self.points = self.normalize_points(self.data['points'], self.manager.constants)
        print self.points
        self.x = [p[0] for p in self.points]
        self.y = [p[1] for p in self.points]
        self.rep = scipy.interpolate.splrep(self.x, self.y, s=0)

    def calculate(self):
        return cap(scipy.interpolate.splev([self.current_time], self.rep, der=0)[0])
