#!/usr/bin/env python3
import cv2
import dlib
import math
from math import hypot
from math import pi, pow
import numpy as np
import autopy


detector  = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')

class Eye_base:
    def __init__(self, side,points,thresh ):
        self.side   = side
        self.points = points
        self.thresh = thresh

    def blink(self, frame):
        hor_line_length = hypot((self.left_point[0] - self.right_point[0]),   (self.left_point[1] - self.right_point[1])) 
        ver_line_length = hypot((self.center_top[0] - self.center_bottom[0]), (self.center_top[1] - self.center_bottom[1]))

        ratio = hor_line_length / ver_line_length

        return ratio;

class Main:
    def __init__(self, detector , predictor):
        self.detector   = detector
        self.predictor  = predictor
        self.cap        = cv2.VideoCapture(-1)
        self.width_cam  = 640
        self.height_cam = 480
        self.width_screen  = autopy.screen.size()[0]
        self.height_screen = autopy.screen.size()[1]

    def main(self):


        while True:
            _, self.frame = self.cap.read()
            self.frame = cv2.flip(self.frame,1)

            thresh   = self.frame.copy()
            gray     = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            rects    = detector(gray)

            for rect in rects:
                shape = self.shape_to_np(predictor(gray,rect))

                mid = (shape[42][0] + shape[39][0]) // 2
                
                left_eye  = Eye_base("left",  [36, 37, 38, 40, 41], thresh[:, 0:mid])
                right_eye = Eye_base("right", [42, 43, 44, 46, 47], thresh[:,  mid:])
                mask      = np.zeros(self.frame.shape[:2], dtype=np.uint8)

                mask  = self.cal_mask(shape,mask,left_eye.points,right_eye.points)

                eyes = cv2.bitwise_and(self.frame, self.frame , mask=mask)

                mask = (eyes == [0,0,0]).all(axis=2)
                eyes[mask] = [255 ,255,255]

                eyes_gray = cv2.cvtColor(eyes, cv2.COLOR_BGR2GRAY)

                _, thresh = cv2.threshold(eyes_gray  , 170, 255 , cv2.THRESH_BINARY)
                thresh = self.thresh_processing(thresh)

                self.contouring(thresh[:, 0:mid],mid, self.frame,left_eye.side)
                self.contouring(thresh[:,  mid:],mid, self.frame,right_eye.side)

            cv2.imshow("eyes"  , self.frame)
            cv2.imshow("thresh", thresh)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.close(self.cap)
    
    def shape_to_np(self,shape, dtype="int"):
        coords = np.zeros((68,2), dtype=dtype)
        for i in range(0,68):
            coords[i] = (shape.part(i).x , shape.part(i).y)
        return coords;

    def cal_mask(self,shape,mask,left,right):
        mask = self.cal_eye_on_mask(shape,mask, left) 
        mask = self.cal_eye_on_mask(shape,mask, right)

        return mask;

    def cal_eye_on_mask(self,shape,mask,side):
        points = [shape[i] for i in side]
        points = np.array(points, dtype=np.int32)
        mask = cv2.fillConvexPoly(mask, points, 255)


        return mask;

    def thresh_processing(self,thresh):
        thresh = cv2.erode(thresh,None,iterations=8)
        thresh = cv2.dilate(thresh,None,iterations=5)
        thresh = cv2.medianBlur(thresh,3)
        thresh = cv2.bitwise_not(thresh)

        return thresh;

    def contouring(self,thresh ,mid , frame , side):
        cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
        cnt = max(cnts, key = cv2.contourArea)
        M = cv2.moments(cnt)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])
        if side == "right":
            cx += mid
        cv2.circle(frame, (cx, cy), 4, (0,0,255), 2)
        print(cx , cy)

    def close(self,cap):
        cap.release()
        cv2.destroyAllWindows()




program = Main(detector, predictor)
                
program.main()
