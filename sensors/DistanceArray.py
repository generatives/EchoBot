from gpiozero import DistanceSensor
import numpy as np

class DistanceArray:
    def __init__(self):
        self.sensors = []
        self.sensors.append(DistanceSensor(25, 26, max_distance=1))

    def get_distances(self):
        return np.array([sensor.distance for sensor in self.sensors])