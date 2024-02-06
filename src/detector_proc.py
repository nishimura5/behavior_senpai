import os

from yolo_detector import YoloDetector
from mediapipe_detector import MediaPipeDetector
from rtmpose_detector import RTMPoseDetector


def exec(rcap, model_name, video_path, use_roi=False):
    # 動画の読み込み
    rcap.open_file(video_path)

    if use_roi is True:
        rcap.click_roi()

    file_name = os.path.splitext(os.path.basename(video_path))[0]
    trk_dir = os.path.join(os.path.dirname(video_path), "trk")
    os.makedirs(trk_dir, exist_ok=True)
    pkl_path = os.path.join(trk_dir, f"{file_name}.pkl")

    # モデルの初期化
    if model_name == "YOLOv8 x-pose-p6":
        model = YoloDetector()
    elif model_name == "MediaPipe Holistic":
        model = MediaPipeDetector()
    elif model_name == "MMPose RTMPose-x":
        model = RTMPoseDetector()

    model.set_cap(rcap)
    model.detect(roi=use_roi)
    result_df = model.get_result()

    # attrsを埋め込み
    result_df.attrs["model"] = model_name
    result_df.attrs["frame_size"] = (rcap.width, rcap.height)
    result_df.attrs["video_name"] = os.path.basename(video_path)
    result_df.attrs["roi_left_top"] = rcap.get_left_top()

    result_df.to_pickle(pkl_path)
    rcap.release()
