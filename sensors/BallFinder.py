import threading
import cv2 as cv
import numpy as np

class BallFinder:

    def __init__(self):
        self.should_run = True
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        self.video_cap = cv.VideoCapture(0)
        if not self.video_cap.isOpened():
            print("Cannot open camera")

        while self.should_run:
            self.ball_bb = self.find_ball()

        self.video_cap.release()


    def find_ball(self):
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
            return (x / frame_width, y / frame_width, w / frame_width, h / frame_width)
        else:
            return None

    def shutdown(self):
        self.should_run = False
        self.thread.join()