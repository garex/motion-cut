#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import imutils
import cv2
import sys

parser = argparse.ArgumentParser(description='Extract motion from video with mask.', prog="garex/motion-cut-detect")
parser.add_argument('--video', required=True)
parser.add_argument('--mask', required=True)
parser.add_argument('--process-width', type=int, default = 900)
parser.add_argument('--frame-threshold', type=int, default = 1)

args = parser.parse_args()

camera = cv2.VideoCapture(args.video)

fgbg = cv2.createBackgroundSubtractorMOG2()

frame_counter = 0
frameWidth = args.process_width

def contours_area(contours):
    total = 0
    for c in contours:
        total = total + cv2.contourArea(c)
    return total

mask = imutils.resize(cv2.imread(args.mask, cv2.IMREAD_GRAYSCALE), width=frameWidth)
(image, contours, _) = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
maskArea = contours_area(contours)

while True:
    (grabbed, frame) = camera.read()

    if not grabbed:
        break

    frame = imutils.resize(frame, width=frameWidth)

    frame_counter = frame_counter + 1

    if frame_counter % args.frame_threshold == 0:
        fgmask = fgbg.apply(frame)
        fgmask = cv2.bitwise_and(fgmask, mask)
        fgmask = cv2.GaussianBlur(fgmask, (19, 19), 0)
        fgmask = cv2.threshold(fgmask, 180, 255, cv2.THRESH_BINARY)[1]

        (image, contours, _) = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            continue
        area = contours_area(contours)
        if not area:
            continue
        print(frame_counter, len(contours), "{0:.7f}".format(area / maskArea))
        sys.stdout.flush()

camera.release()
