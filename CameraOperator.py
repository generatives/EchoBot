import math
import cv2 as cv
import numpy as np
from distributed.Actor import Actor

camera_h_fov = (54 / 360) * (2 * math.pi)

class CameraOperator(Actor):

    def __init__(self, ctx):
        super().__init__(ctx, { "Role": "CameraOperator" }, ["BallPositionFeed"])

    def starting(self):
        self.target = None
        self.video_cap = cv.VideoCapture(0)
        if not self.video_cap.isOpened():
            print("Cannot open camera")

    def stopping(self):
        self.video_cap.release()

    def peer_joined(self, peer, group_name):
        self.target = peer

    def poll(self):
        ret, frame = self.video_cap.read()
        if not ret:
            print("Can't receive frame (stream end?)")
            return None

        blurred = cv.GaussianBlur(frame, (11, 11), 0)
        hsv = cv.cvtColor(blurred, cv.COLOR_BGR2HSV)
        mask = cv.inRange(hsv, np.array((0,150,180)), np.array((10,200,255)))
        mask = cv.erode(mask, None, iterations = 2)
        mask = cv.dilate(mask, None, iterations = 2)

        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            max_contour = contours[0]
            max_contour_area = 0
            for contour in contours:
                contour_area = cv.contourArea(contour)
                if contour_area > max_contour_area:
                    max_contour = contour
                    max_contour_area = contour_area

            approx = cv.approxPolyDP(max_contour, 0.01 * cv.arcLength(max_contour, True), True)
            x,y,w,h = cv.boundingRect(approx)

            frame_width = frame.shape[1]
            (x, y, w, h) = (x / frame_width, y / frame_width, w / frame_width, h / frame_width)
            ball_center = x + (w / 2)
            self.ball_relative_heading = -(ball_center - 0.5) * (camera_h_fov / 2)
        else:
            self.ball_relative_heading = None

        self.last_frame = frame

        if self.target:
            self.target.whisper(str(self.ball_relative_heading).encode("UTF-8"))
        #self.shout("BallPostionFeed", str(self.ball_relative_heading).encode("UTF-8"))

    def shutdown(self):
        self.should_run = False
        self.thread.join()