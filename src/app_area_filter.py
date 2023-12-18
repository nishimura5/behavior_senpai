import os
import tkinter as tk
from tkinter import ttk

import pandas as pd
from PIL import Image, ImageTk
import cv2

from gui_parts import PklSelector, TimeSpanEntry, TempFile
from python_senpai import time_format
from python_senpai import keypoints_proc
from python_senpai import vcap
from python_senpai import file_inout


class App(ttk.Frame):
    """
    指定した四角形の中にkeypointが入っているかを判定するためのGUIです。
    以下の機能を有します
        - Trackファイルを選択して読み込む機能
        - 計算対象の時間帯の指定を行う機能
        - 四角形の位置を指定する機能
        - 以上の処理で得られたデータをpklに保存する機能
    """
    def __init__(self, master):
        super().__init__(master)
        master.title("Area Filter")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, self.height, dpi = temp.get_window_size()

        load_frame = ttk.Frame(self)
        load_frame.pack(pady=5, anchor=tk.W)
        self.pkl_selector = PklSelector(load_frame)
        self.pkl_selector.set_command(cmd=self.load_pkl)
        self.time_span_entry = TimeSpanEntry(load_frame)
        self.time_span_entry.pack(side=tk.LEFT, padx=(0, 5))

        setting_frame = ttk.Frame(self)
        setting_frame.pack(pady=5)
        self.keypoint_combo = ttk.Combobox(setting_frame, state='readonly', width=12)
        self.keypoint_combo.pack(side=tk.LEFT, padx=5)

        area_name_label = ttk.Label(setting_frame, text="Area name:")
        area_name_label.pack(side=tk.LEFT, padx=(10, 0))
        self.area_name_entry = ttk.Entry(setting_frame, width=14)
        self.area_name_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.area_dict = {}

        calc_button = ttk.Button(setting_frame, text="Calc In/Out", command=self.calc_in_out)
        calc_button.pack(side=tk.LEFT)

        export_frame = ttk.Frame(self)
        export_frame.pack(pady=5)
        result_label = ttk.Label(export_frame, text="Columns:")
        result_label.pack(side=tk.LEFT, padx=(10, 0))
        self.result_combo = ttk.Combobox(export_frame, state='readonly')
        self.result_combo.pack(side=tk.LEFT)
        self.result_list = []

        clear_btn = ttk.Button(export_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT, padx=(10, 0))

        export_btn = ttk.Button(export_frame, text="Export", command=self.export)
        export_btn.pack(side=tk.LEFT, padx=(10, 0))

        self.canvas = tk.Canvas(self, width=600, height=400)
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.select)
        self.canvas.bind("<Button1-Motion>", self.motion)

        self.cap = vcap.VideoCap()
        self.img_on_canvas = None
        self.load_pkl()

        self.anchor_points = [
            {'point': (100, 100)},
            {'point': (100, 200)},
            {'point': (200, 200)},
            {'point': (200, 100)},
            ]
        self.selected_id = None
        poly_points = sum([list(p['point']) for p in self.anchor_points], [])
        self.poly_id = self.canvas.create_polygon(*poly_points, fill="", outline="black")
        for point in self.anchor_points:
            x = point['point'][0]
            y = point['point'][1]
            point['id'] = self.canvas.create_rectangle(x-2, y-2, x+2, y+2, fill="white")

    def load_pkl(self):
        # ファイルのロード
        self.pkl_path = self.pkl_selector.get_trk_path()
        self.src_df = file_inout.load_track_file(self.pkl_path)
        pkl_dir = os.path.dirname(self.pkl_path)
        self.cap.set_frame_size(self.src_df.attrs["frame_size"])
        self.cap.open_file(os.path.join(pkl_dir, os.pardir, self.src_df.attrs["video_name"]))

        # UIの更新
        self.keypoint_combo["values"] = self.src_df.index.get_level_values("keypoint").unique().tolist()
        self.keypoint_combo.current(0)
        self.time_span_entry.update_entry(
            time_format.msec_to_timestr_with_fff(self.src_df["timestamp"].min()),
            time_format.msec_to_timestr_with_fff(self.src_df["timestamp"].max())
        )
        self.pkl_selector.set_prev_next(self.src_df.attrs)

        ratio = self.src_df.attrs["frame_size"][0] / self.src_df.attrs["frame_size"][1]
        width = int(self.height * ratio)
        self.scale = width / self.src_df.attrs["frame_size"][0]
        self.canvas.config(width=width, height=self.height)

        ok, image_rgb = self.cap.read_at(10, rgb=True)
        if ok is False:
            return
        image_rgb = cv2.resize(image_rgb, None, fx=self.scale, fy=self.scale)
        image_pil = Image.fromarray(image_rgb)
        self.image_tk = ImageTk.PhotoImage(image_pil)
        if self.img_on_canvas is None:
            self.img_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)
        else:
            self.canvas.itemconfig(self.img_on_canvas, image=self.image_tk)
        self.clear()
        print('load_pkl() done.')

    def calc_in_out(self):
        current_keypoint = self.keypoint_combo.get()
        tar_df = self.src_df.copy()

        # timestampの範囲を抽出
        time_min, time_max = self.time_span_entry.get_start_end()
        time_min_msec = self._timedelta_to_msec(time_min)
        time_max_msec = self._timedelta_to_msec(time_max)
        tar_df = keypoints_proc.filter_by_timerange(tar_df, time_min_msec, time_max_msec)

        idx = tar_df.index
        tar_df.index = tar_df.index.set_levels([idx.levels[0], idx.levels[1], idx.levels[2].astype(str)])

        poly_points = [p['point'] for p in self.anchor_points]
        area_name = self.area_name_entry.get()
        isin_df = keypoints_proc.is_in_poly(tar_df, current_keypoint, poly_points, area_name, self.scale)
        new_col_name = isin_df.columns[0]
        if new_col_name not in self.dst_df.columns:
            self.dst_df = pd.concat([self.dst_df, isin_df], axis=1)

        self.area_dict[area_name] = poly_points

        # UI表示用
        frame_true_cnt = isin_df.droplevel(1).sum()
        in_percent = int(sum(frame_true_cnt) / len(isin_df) * 100)
        self.result_list.append(f"{new_col_name}: {in_percent}%")
        self.result_combo["values"] = self.result_list

    def clear(self):
        self.area_name_entry.delete(0, tk.END)
        self.area_dict = {}
        self.result_list = []
        self.result_combo["values"] = ""
        self.dst_df = pd.DataFrame()

    def export(self):
        if len(self.dst_df) == 0:
            print("No data to export.")
            return
        timestamp_df = self.src_df.loc[:, 'timestamp'].droplevel(2).to_frame()
        timestamp_df = timestamp_df.reset_index().drop_duplicates(subset=['frame', 'member'], keep='last').set_index(['frame', 'member'])
        self.dst_df = self.dst_df.reset_index().drop_duplicates(subset=['frame', 'member'], keep='last').set_index(['frame', 'member'])
        export_df = pd.concat([self.dst_df, timestamp_df], axis=1)
        export_df.attrs = self.src_df.attrs
        export_df.attrs['area_filters'] = self.area_dict

        file_inout.save_pkl(self.pkl_path, export_df, proc_history="area_filter")

    def select(self, event):
        for point in self.anchor_points:
            x = point['point'][0]
            y = point['point'][1]
            if x-10 < event.x < x+10 and y-10 < event.y < y+10:
                self.selected_id = point['id']
                break
            else:
                self.selected_id = None
        self.area_name_entry.delete(0, tk.END)

    def motion(self, event):
        if self.selected_id is None:
            return
        for point in self.anchor_points:
            if point['id'] == self.selected_id:
                point['point'] = (event.x, event.y)
                break
        poly_points = sum([list(p['point']) for p in self.anchor_points], [])
        self.canvas.coords(self.selected_id, event.x-2, event.y-2, event.x+2, event.y+2)
        self.canvas.coords(self.poly_id, *poly_points)

    def _timedelta_to_msec(self, timedelta):
        # strをtimedeltaに変換
        timedelta = pd.to_timedelta(timedelta)
        sec = timedelta.total_seconds()
        return sec * 1000


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
