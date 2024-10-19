from __future__ import print_function
import qwiic_icm20948
import sys
import math
import numpy as np

class HeadingSensor:

    def __init__(self, K = 0.30, mag_min = np.array([-719, -427, -60]), mag_max = np.array([-70, 271, 669])):
        self.IMU = qwiic_icm20948.QwiicIcm20948()

        if self.IMU.connected == False:
            print("The Qwiic ICM20948 device isn't connected to the system. Please check your connection", \
                file=sys.stderr)
            return

        self.K = K

        self.mag_avg = np.zeros(3)
        self.acc_avg = np.zeros(3)
        
        self.heading = 0
        self.sensor_offset = math.pi

        self.calibration_offset = (mag_max + mag_min) / 2

        avg_deltas = (mag_max - mag_min) / 2
        avg_delta = np.sum(avg_deltas) / 3

        self.calibration_scale = avg_delta / avg_deltas

        self.IMU.begin()

    def _correct_mag_reading(self, mag):
        return (mag - self.calibration_offset) * self.calibration_scale

    def step(self):
        if self.IMU.dataReady():
            self.IMU.getAgmt()
            mag = np.array([self.IMU.mxRaw, self.IMU.myRaw, self.IMU.mzRaw])
            mag = self._correct_mag_reading(mag)

            acc = np.array([self.IMU.axRaw, self.IMU.ayRaw, self.IMU.azRaw])

            K = self.K
            self.mag_avg = K * self.mag_avg + (1 - K) * mag
            self.acc_avg = K * self.acc_avg + (1 - K) * acc

            accMag = np.linalg.norm(self.acc_avg)
            accXnorm = self.acc_avg[0] / accMag
            accYnorm = self.acc_avg[1] / accMag

            pitch = math.asin(accXnorm)
            roll = -math.asin(accYnorm / math.cos(pitch))

            [mag_x, mag_y, mag_z] = self.mag_avg
            magXcomp = mag_x * math.cos(pitch) + mag_z * math.sin(pitch)
            magYcomp = mag_x * math.sin(roll) * math.sin(pitch) + mag_y * math.cos(roll) - mag_z * math.sin(roll) * math.cos(pitch)

            declination = 0.2784
            heading = math.atan2(magYcomp, magXcomp) + declination + math.pi
            #heading = heading + self.sensor_offset
            
            full_circle = 2 * math.pi
            if heading < 0:
                heading = heading + full_circle

            if heading > full_circle:
                heading = heading - full_circle
                
            self.heading = heading