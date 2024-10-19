from geometer import Point
from geometer.transformation import rotation, translation
import math
   
class Pose:
    def __init__(self, position, rotation):
        self.position = position
        self.rotation = rotation
        
    def __init__(self, x, y, rotation):
        self.position = Point(x, y)
        self.rotation = rotation

    def get_local_to_world(self):
        return translation(self.position) * rotation(self.rotation)

def chain_pose(point, pose, *addition_poses):
    point = pose.get_local_to_world() * point
    for pose in addition_poses:
        point = pose.get_local_to_world() * point
        
    return point

def heading_diff(current_heading, goal_heading):
    diff = goal_heading - current_heading

    if diff > math.pi:
        return diff - (2 * math.pi)

    if diff < -math.pi:
        return diff - (-2 * math.pi)

    return diff