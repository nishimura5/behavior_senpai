import importlib.util
import os
import time

from behavior_senpai import file_inout, mediapipe_detector


def is_module_available(module_name):
    spec = importlib.util.find_spec(module_name)
    return spec is not None


# CUDAが使えない環境ではrye sync時にultralyticsとmmposeをインストールしていない
if is_module_available("ultralytics"):
    from behavior_senpai import yolo_detector

    YOLOV8_AVAILABLE = True
else:
    YOLOV8_AVAILABLE = False
if is_module_available("mmpose"):
    from behavior_senpai import rtmpose_detector

    MMPOSE_AVAILABLE = True
else:
    MMPOSE_AVAILABLE = False


def check_gpu():
    return YOLOV8_AVAILABLE, MMPOSE_AVAILABLE


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
    if model_name == "YOLO11 x-pose":
        model = yolo_detector.YoloDetector()
    elif model_name == "MediaPipe Holistic":
        model = mediapipe_detector.MediaPipeDetector()
    elif model_name == "RTMPose-x Halpe26":
        model = rtmpose_detector.RTMPoseDetector()
    elif model_name == "RTMPose-x WholeBody133":
        model = rtmpose_detector.RTMPoseDetector(whole_body=True)

    model.set_cap(rcap)
    model.detect(roi=use_roi)
    result_df = model.get_result()

    # attrsを埋め込み
    result_df.attrs["model"] = model_name
    result_df.attrs["frame_size"] = (rcap.width, rcap.height)
    result_df.attrs["video_name"] = os.path.basename(video_path)
    result_df.attrs["roi_left_top"] = rcap.get_left_top()
    result_df.attrs["created"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    file_inout.overwrite_track_file(pkl_path, result_df, not_found_ok=True)
    rcap.release()
