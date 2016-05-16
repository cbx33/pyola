from base import Modifier
from waypoint import WaypointMixin


class PolygonModifier(Modifier, WaypointMixin):
    def __init__(self, *args, **kwargs):
        super(PolygonModifier, self).__init__(*args, **kwargs)
        self.points = self.normalize_points(self.data['points'], self.manager.constants)

    def calculate(self):
        best_match = self.points[0]
        for point in self.points:
            if point[0] >= self.current_time:
                break
            else:
                best_match = point
        return best_match[1]
