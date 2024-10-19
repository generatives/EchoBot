import logging
from readline import set_completer_delims
from distributed.Node import Node
from control.MotorController import MotorController
from sensors.HeadingSensor import HeadingSensor
from sensors.DistanceArray import DistanceArray
from CameraOperator import CameraOperator
from enum import Enum
from utils.geometry import heading_diff
import numpy as np
import random
import math
import time
import zmq

class RobotState(Enum):
    PICKING_WANDER_HEADING = 1
    FOLLOWING_WANDER_HEADING = 2
    FOLLOWING_BALL = 3
    LOST_BALL = 4
    BACKING_UP = 5

wander_heading_threshold = (5 / 360) * (2 * math.pi)
follow_wander_heading_clearance = 0.8
wall_clearance = 0.30
speed = 0

def period_print(string):
    timestamp = int(time.time())
    if timestamp % 2 == 0:
        print(string)

def wrap(num, min, max):
    if max <= min:
        raise Exception(f"max must be greater than min")

    if num > max:
        return min + num - max
    elif num < min:
        return max + num - min
    else:
        return num

class Robot:
    def __init__(self, ctx):
        self.motor_controller = MotorController()
        self.heading_sensor = HeadingSensor()
        self.distance_array = DistanceArray()

        self.node = Node(ctx, headers={"Role": "Robot"}, groups=["BallPositionFeed"])
        self.node.whisper_recieved += self.whisper_recieved
        self.node.start()

        self.state = RobotState.PICKING_WANDER_HEADING
        self.wander_heading = None
        self.no_ball_timestamp = None
        self.ball_relative_heading = None
        self.ball_last_relative_heading = None

        self.state_lookup = {}
        self.state_lookup[RobotState.PICKING_WANDER_HEADING] = self._picking_wander_heading
        self.state_lookup[RobotState.FOLLOWING_WANDER_HEADING] = self._following_wander_heading
        self.state_lookup[RobotState.FOLLOWING_BALL] = self._following_ball
        self.state_lookup[RobotState.BACKING_UP] = self._backing_up

    def whisper_recieved(self, peer, cmds):
        print(f"Rec position: {cmds}")
        msg = cmds.pop(0).decode("UTF-8")
        self.ball_relative_heading = None if msg == 'None' else float(msg)

    def _set_state(self, state):
        print(f"Transition from {self.state} to {state}")
        self.state = state

    def _obstructed(self, distances):
        return np.any(np.less(distances, wall_clearance))

    def _picking_wander_heading(self, distances, current_heading):
        if self.ball_relative_heading is not None:
            self._set_state(RobotState.FOLLOWING_BALL)
            self.wander_heading = None
            return

        if self.wander_heading is None:
            opposite_heading = current_heading + math.pi
            wander_heading = opposite_heading + random.uniform(-0.5 * math.pi, 0.5 * math.pi)
            if wander_heading > 2 * math.pi:
                wander_heading = wander_heading - 2 * math.pi
            self.wander_heading = wander_heading
            print(f"Set Wander Heading {self.wander_heading}")

        self.motor_controller.step(current_heading, self.wander_heading, 0, turn_strength=0.3)

        if abs(heading_diff(current_heading, self.wander_heading)) < wander_heading_threshold:
            if np.any(np.less(distances, follow_wander_heading_clearance)):
                self.wander_heading = None
                self.motor_controller.step(current_heading, current_heading, 0)
            else:
                self._set_state(RobotState.FOLLOWING_WANDER_HEADING)

    def _following_wander_heading(self, distances, current_heading):
        if self.ball_relative_heading is not None:
            self._set_state(RobotState.FOLLOWING_BALL)
            self.wander_heading = None
            return

        if self._obstructed(distances):
            self._set_state(RobotState.BACKING_UP)
            self.wander_heading = None
            self.motor_controller.step(current_heading, current_heading, 0)
            return

        self.motor_controller.step(current_heading, self.wander_heading, speed, turn_strength=0.5)

    def _following_ball(self, distances, current_heading):

        if self._obstructed(distances):
            self._set_state(RobotState.BACKING_UP)
            self.wander_heading = None
            self.motor_controller.step(current_heading, current_heading, 0)
            return

        if self.ball_relative_heading is None:
            if self.no_ball_timestamp is None:
                print("Lost ball")
                self.no_ball_timestamp = time.time()

            time_since = time.time() - self.no_ball_timestamp
            
            if time_since > 10:
                self._set_state(RobotState.PICKING_WANDER_HEADING)
                self.wander_heading = None
                self.no_ball_timestamp = None
                self.ball_last_relative_heading = None
                self.motor_controller.step(current_heading, current_heading, 0)
            
            if self.ball_last_relative_heading is not None:
                relative_heading = self.ball_last_relative_heading
                follow_speed = speed if time_since <= 2 else 0
        else:
            if self.no_ball_timestamp is not None:
                self.no_ball_timestamp = None
                print("Found ball")
                
            relative_heading = self.ball_relative_heading
            follow_speed = speed

        goal_heading = current_heading + relative_heading
        if goal_heading > 2 * math.pi:
            goal_heading = goal_heading - 2 * math.pi

        self.motor_controller.step(current_heading, goal_heading, follow_speed)

    def _backing_up(self, distances, current_heading):
        if self._obstructed(distances):
            self.motor_controller.step(current_heading, current_heading, -speed)
        else:
            self._set_state(RobotState.PICKING_WANDER_HEADING)
            self.wander_heading = None
            self.motor_controller.step(current_heading, current_heading, 0)

    def step(self):
        self.node.poll()
        self.heading_sensor.step()

        distances = self.distance_array.get_distances()
        #period_print(f"state: {self.state}, distances: {np.array2string(distances)}")
        current_heading = self.heading_sensor.heading
        
        self.state_lookup[self.state](distances, current_heading)
    
    def shutdown(self):
        self.motor_controller.shutdown()
        self.node.stop()

if __name__ == '__main__':

    #logger = logging.getLogger("pyre")
    #logger.setLevel(logging.ERROR)

    ctx = zmq.Context()
    cameraOperator = CameraOperator(ctx)
    robot = Robot(ctx)

    cameraOperator.start()

    try:
        while True:
            #now = time.time()
            robot.step()
            #print(f"Step: {time.time() - now}")
    finally:
        robot.shutdown()
        cameraOperator.stop()