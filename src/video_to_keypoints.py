import os

import cv2

from yolo_detector import YoloDetector
from mediapipe_detector import MediaPipeDetector

model_name = "YOLOv8 x-pose-p6"
#model_name = "MediaPipe Holistic"

video_path = "taiso.mp4"
file_name = os.path.splitext(os.path.basename(video_path))[0]
pkl_path = f"{file_name}.pkl"

cap = cv2.VideoCapture(video_path)

if model_name == "YOLOv8 x-pose-p6":
    detector = YoloDetector(cap)
elif model_name == "MediaPipe Holistic":
    detector = MediaPipeDetector(cap)

detector.detect()
result_df = detector.get_result()

result_df.attrs["model"] = model_name

result_df.to_pickle(pkl_path)
