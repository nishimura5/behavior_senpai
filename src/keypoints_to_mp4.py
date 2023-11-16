import os
import tkinter as tk
from tkinter import ttk

import pandas as pd
import numpy as np
import cv2

from gui_parts import PklSelector, MemberKeypointComboboxes
import yolo_drawer
import mediapipe_drawer


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Keypoints to MP4")
        self.pack(padx=10, pady=10)

        load_frame = tk.Frame(self)
        self.pkl_selector = PklSelector(load_frame)
        load_frame.pack(pady=5)
        self.pkl_selector.set_command(cmd=self.load_pkl)

        setting_frame = tk.Frame(self)
        setting_frame.pack(pady=5)
        # allのチェックボックス
        self.draw_all_chk_val = tk.BooleanVar()
        self.draw_all_chk_val.set(False)
        all_check = ttk.Checkbutton(setting_frame, text="draw all", variable=self.draw_all_chk_val)
        all_check.pack(side=tk.LEFT)

        self.member_keypoints_combos = MemberKeypointComboboxes(setting_frame)

        draw_btn = ttk.Button(setting_frame, text="Export", command=self.export)
        draw_btn.pack(side=tk.LEFT)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)

        self.load_pkl()

    def load_pkl(self):
        pkl_path = self.pkl_selector.get_trk_path()
        self.src_df = pd.read_pickle(pkl_path)

        self.member_keypoints_combos.set_df(self.src_df)

        # PKLが置かれているフォルダのパスを取得
        self.pkl_dir = os.path.dirname(pkl_path)

    def export(self):
        current_member, current_keypoint = self.member_keypoints_combos.get_selected()

        out_df = self.src_df
        # memberとkeypointのインデックス値を文字列に変換
        idx = out_df.index
        out_df.index = out_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])

        # VideoCapture
        video_path = os.path.join(self.pkl_dir, os.pardir, self.src_df.attrs['video_name'])
        if os.path.exists(video_path) is True:
            cap = cv2.VideoCapture(
                video_path,
                apiPreference=cv2.CAP_ANY,
                params=[cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY])
            fps = cap.get(cv2.CAP_PROP_FPS)
        else:
            cap = None
            fps = 30

        scale = 0.5

        # VideoWriter
        file_name = os.path.splitext(self.src_df.attrs['video_name'])[0]
        if self.draw_all_chk_val.get() is True:
            suffix = "all"
        else:
            suffix = f"{current_member}_{current_keypoint}"
        out_file_path = os.path.join(self.pkl_dir, f'{file_name}_{suffix}.mp4')
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        size = self.src_df.attrs['frame_size']
        size = (int(size[0] * scale), int(size[1] * scale))
        out = cv2.VideoWriter(out_file_path, fourcc, fps, size, params=[cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY])

        if self.src_df.attrs['model'] == "YOLOv8 x-pose-p6":
            anno = yolo_drawer.Annotate()
        elif self.src_df.attrs['model'] == "MediaPipe Holistic":
            anno = mediapipe_drawer.Annotate()

        total_frame_num = out_df.index.unique(level='frame').max() + 1
        indexes = out_df.sort_index().index
        for i in range(total_frame_num):
            if cap is not None:
                ret, frame = cap.read()
            if cap is None or ret is False:
                frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
            frame = cv2.resize(frame, size)
            anno.set_img(frame)
            # draw_allなら全員の姿勢を描画
            if self.draw_all_chk_val.get() is True:
                for member in indexes.levels[1]:
                    dst_img = self._draw(i, member, current_keypoint, indexes, anno, scale)
                if dst_img is None:
                    dst_img = frame
            # out_dfにi, current_member, current_keypointの組み合わせがない場合はスキップ
            elif (i, current_member, current_keypoint) in indexes:
                dst_img = self._draw(i, current_member, current_keypoint, indexes, anno, scale)
            else:
                dst_img = frame
            cv2.imshow("dst", dst_img)
            cv2.waitKey(1)
            out.write(frame)
        cv2.destroyAllWindows()
        out.release()

    def _draw(self, frame, member, keypoint, all_indexes, anno, scale):
        if (frame, member, keypoint) not in all_indexes:
            return None
        keypoints = self.src_df.loc[pd.IndexSlice[frame, member, :], :] * scale
        kps = keypoints.to_numpy()
        anno.set_pose(kps)
        anno.set_track(member)
        dst_img = anno.draw()
        return dst_img


def quit(root):
    root.quit()
    root.destroy()


def main():
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", lambda: quit(root))
    app.mainloop()


if __name__ == "__main__":
    main()
