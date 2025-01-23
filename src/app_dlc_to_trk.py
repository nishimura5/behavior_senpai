import os
from tkinter import filedialog, ttk

import gui_parts
from behavior_senpai import deeplabcut_hdf


class App(ttk.Frame):
    def __init__(self, master, h5_path):
        super().__init__(master)
        master.title("Deeplabcut to track file")
        self.pack(padx=10, pady=10)

        self.trk_path = ""
        self.h5_path = h5_path
        print(f"Loaded {h5_path}")
        video_file_btn = ttk.Button(self, text="Select video file", command=self.select_video)
        video_file_btn.pack()
        self.video_file_label = ttk.Label(self, text="No video file loaded")
        self.video_file_label.pack()

        self.width_entry = gui_parts.IntEntry(self, "Width:", "1980")
        self.width_entry.pack_horizontal()
        self.height_entry = gui_parts.IntEntry(self, "Height:", "1080")
        self.height_entry.pack_horizontal()

        fps_label = ttk.Label(self, text="FPS:")
        fps_label.pack()
        self.fps_entry = ttk.Entry(self)
        self.fps_entry.pack()

        convert_btn = ttk.Button(self, text="Convert to track file", command=self.convert)
        convert_btn.pack()

    def convert(self):
        df = deeplabcut_hdf.read_h5(self.h5_path)
        fps = self.fps_entry.get()
        kps, df = deeplabcut_hdf.transform_df(df, float(fps))
        # 最終的な仕様は下記
        # pklをhdf5に変更, 拡張子は.trkにする予定(しないかも)
        # 拡張子がh5なら
        #  HDF5を開いた後、group名(df_with_missing)でDLCか否かを判断して分岐
        #  group名が違う場合は読み込まない
        #  DLCの場合はmp4のファイル名等の情報を入力するためのダイアログを表示

        # source information
        #  mp4 file name
        #  h5 file name
        #  fps
        #  frame size(w,h)
        video_name = os.path.basename(self.video_path)
        df.attrs["video_name"] = video_name
        df.attrs["model"] = "DeepLabCut"
        width = self.width_entry.get()
        height = self.height_entry.get()
        df.attrs["frame_size"] = (width, height)
        deeplabcut_hdf.generate_toml(kps)

        # make directory for track file
        trk_dir = os.path.join(os.path.dirname(self.video_path), "trk")
        os.makedirs(trk_dir, exist_ok=True)

        # save track file
        trk_path = os.path.join(trk_dir, os.path.splitext(video_name)[0] + "_dlc.pkl")
        df.to_pickle(trk_path)
        self.trk_path = trk_path
        print(f"Track file saved to {trk_path}")
        self.master.destroy()

    def select_video(self):
        self.video_path = filedialog.askopenfilename(initialdir="~")
        self.video_file_label["text"] = self.video_path
