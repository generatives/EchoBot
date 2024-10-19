import qwiic_scmd
import time
import sys
import math

R_MTR = 1
L_MTR = 0
L_FWD = 1
R_FWD = 0

min_motor_value = 60

def bound(value, low, high):
    return max(low, min(high, value))

def period_print(string):
    timestamp = int(time.time())
    if timestamp % 2 == 0:
        print(string)

class MotorController:
    def __init__(self):
        self.motor_control = qwiic_scmd.QwiicScmd()
        
        print("Motor Begin.")
        if self.motor_control.connected == False:
            print("Motor Driver not connected. Check connections.", file=sys.stderr)
            return
        self.motor_control.begin()
        print("Motor Initialized.")
        time.sleep(.250)

        # Zero Motor Speeds
        self.motor_control.set_drive(0,0,0)
        self.motor_control.set_drive(1,0,0)

        self.motor_control.enable()
        print("Motor Enabled")
        time.sleep(.250)

    def step(self, current_heading, goal_heading, speed, turn_strength = 1):

        rotation = self._goal_rotation(current_heading, goal_heading)
        
        rotation_max = (1 / 8) * (2 * math.pi)
        rotation_scaler = bound(rotation, -rotation_max, rotation_max) / rotation_max
        max_rotation_speed = 120 * turn_strength
        min_rotation_speed = 0
        if abs(rotation_scaler) < 0.03:
            rotation_speed = 0
        else:
            sign = 1 if rotation_scaler >= 0 else -1
            val = abs(rotation_scaler)
            speed_range = max_rotation_speed - min_rotation_speed
            rotation_speed = sign * (speed_range * val + min_rotation_speed)

        right_speed = bound(int(speed + rotation_speed), -255, 255)
        right_motor_val = self._speed_to_motor_value(right_speed)
        self.motor_control.set_drive(R_MTR, R_FWD, right_motor_val)

        left_speed = bound(int(speed - rotation_speed), -255, 255)
        left_motor_val = self._speed_to_motor_value(left_speed)
        self.motor_control.set_drive(L_MTR, L_FWD, left_motor_val)

        #period_print(f"G: {rotation_speed}, R: {right_motor_val}, L: {left_motor_val}")

    def _speed_to_motor_value(self, speed):
        return 0


        if speed > 0:
            return min_motor_value + speed
        elif speed < 0:
            return -min_motor_value + speed
        else:
            return 0

    def _goal_rotation(self, current_heading, goal_heading):
        diff = goal_heading - current_heading

        if diff > math.pi:
            return diff - (2 * math.pi)

        if diff < -math.pi:
            return diff - (-2 * math.pi)

        return diff

    def shutdown(self):
        self.motor_control.disable()