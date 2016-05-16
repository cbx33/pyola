from utils import get_val_from_const


class WaypointMixin(object):
        def normalize_points(self, points, consts):
            new_points = []
            for point in points:
                point_val = get_val_from_const(point[1], consts)
                new_points.append([point[0], point_val])
            return new_points
