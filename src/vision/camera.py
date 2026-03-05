# This module should provide a Camera class with read_frame() and release() methods.
from ultralytics import YOLO
import cv2 as cv

model = YOLO("yolo26n.pt")

cap = cv.VideoCapture(0)
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Detect phones only (COCO class 67)
    results = model(frame, classes=[67])

    # Draw bounding boxes on the frame
    annotated = results[0].plot()

    cv.imshow("Phone Detection", annotated)
    if cv.waitKey(1) == ord("q"):
        break

cap.release()
cv.destroyAllWindows()