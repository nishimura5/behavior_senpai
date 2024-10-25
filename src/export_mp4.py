import os
from tkinter import messagebox

import cv2
import pandas as pd

from behavior_senpai import mediapipe_drawer, rtmpose_drawer, yolo_drawer
from gui_parts import TempFile


class MakeMp4:
    def __init__(self):
        self.out = cv2.VideoWriter()

    def load(self, args):
        self.src_df = args["src_df"]
        self.cap = args["cap"]
        self.src_attrs = self.src_df.attrs
        self.time_min = None
        self.time_max = None
        self.pkl_dir = args["pkl_dir"]
        self.track_name = args["trk_pkl_name"]

    def set_time_range(self, time_min, time_max):
        self.time_min = time_min
        self.time_max = time_max

    def export(self):
        tar_df = self.src_df
        idx = tar_df.index
        tar_df.index = tar_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])

        if self.cap.isOpened() is True:
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.cap.set_frame_pos(self.time_min)
        else:
            fps = 29.97

        tmp = TempFile()
        scale = tmp.get_mp4_setting()

        file_name = os.path.splitext(self.track_name)[0]
        if self.src_attrs["model"] in ["YOLOv8 x-pose-p6", "YOLO11 x-pose"]:
            anno = yolo_drawer.Annotate()
            suffix = "yolov8"
        elif self.src_attrs["model"] == "MediaPipe Holistic":
            anno = mediapipe_drawer.Annotate()
            suffix = "mediapipe"
        elif self.src_attrs["model"] == "MMPose RTMPose-x":
            anno = rtmpose_drawer.Annotate()
            suffix = "rtmpose"

        dst_dir = os.path.join(self.pkl_dir, os.pardir, "mp4")
        os.makedirs(dst_dir, exist_ok=True)
        out_file_path = os.path.join(dst_dir, f"{file_name}_{suffix}.mp4")
        fourcc = cv2.VideoWriter_fourcc("m", "p", "4", "v")
        size = self.src_attrs["frame_size"]
        size = (int(size[0] * scale), int(size[1] * scale))
        self.out.open(out_file_path, fourcc, fps, size, params=[cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY])

        out_df = tar_df
        if self.time_min is None or self.time_max is None:
            min_frame_num = out_df.index.unique(level="frame").min()
            max_frame_num = out_df.index.unique(level="frame").max() + 1
        else:
            min_frame_num = out_df[out_df["timestamp"] >= self.time_min].index.unique(level="frame").min()
            max_frame_num = out_df[out_df["timestamp"] <= self.time_max].index.unique(level="frame").max() + 1

        out_indexes = out_df.sort_index().index
        frames = out_indexes.get_level_values("frame").unique()
        for i in range(min_frame_num, max_frame_num):
            frame = self.cap.read_anyway()
            frame = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
            anno.set_img(frame)
            if i in frames:
                frame_df = out_df.loc[pd.IndexSlice[i, :, :], :]
                indexes = frame_df.sort_index().index
                for member in indexes.get_level_values("member").unique():
                    dst_img = self._draw(out_df, i, member, indexes, anno, scale)
            else:
                dst_img = frame
            cv2.imshow("dst", dst_img)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("x"):
                break
            self.out.write(dst_img)
        cv2.destroyAllWindows()
        self.out.release()
        mp4_name = os.path.basename(out_file_path)
        messagebox.showinfo("Export MP4", f"Export finished.\nfile name: {mp4_name}")
        return mp4_name

    def extract(self):
        tar_df = self.src_df
        idx = tar_df.index
        tar_df.index = tar_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])

        if self.cap.isOpened() is True:
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.cap.set_frame_pos(self.time_min)
        else:
            fps = 29.97

        file_name = os.path.splitext(self.track_name)[0]
        dst_dir = os.path.join(self.pkl_dir, os.pardir, "mp4")
        os.makedirs(dst_dir, exist_ok=True)
        out_file_path = os.path.join(dst_dir, f"{file_name}_extracted.mp4")
        fourcc = cv2.VideoWriter_fourcc("m", "p", "4", "v")
        size = self.src_attrs["frame_size"]
        self.out.open(out_file_path, fourcc, fps, size, params=[cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY])

        out_df = tar_df
        if self.time_min is None or self.time_max is None:
            min_frame_num = out_df.index.unique(level="frame").min()
            max_frame_num = out_df.index.unique(level="frame").max() + 1
        else:
            # between time_min and time_max ["timestamp"]column
            min_frame_num = out_df[out_df["timestamp"] >= self.time_min].index.unique(level="frame").min()
            max_frame_num = out_df[out_df["timestamp"] <= self.time_max].index.unique(level="frame").max() + 1

        for i in range(min_frame_num, max_frame_num):
            frame = self.cap.read_anyway()
            cv2.imshow("dst", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("x"):
                break
            self.out.write(frame)
        cv2.destroyAllWindows()
        self.out.release()
        mp4_name = os.path.basename(out_file_path)
        messagebox.showinfo("Export MP4", f"Export finished.\nfile name: {mp4_name}")
        return mp4_name

    def _draw(self, out_df, frame_num, member, all_indexes, anno, scale):
        if (frame_num, member) not in all_indexes.droplevel(2):
            return anno.dst_img
        keypoints = out_df.loc[pd.IndexSlice[frame_num, member, :], :].copy()
        if "x" in keypoints.columns:
            keypoints.loc[:, ["x", "y"]] *= scale
        kps = keypoints.to_numpy()
        anno.set_pose(kps)
        anno.set_track(member)
        # anno.mosaic(240*scale)
        dst_img = anno.draw()
        return dst_img
