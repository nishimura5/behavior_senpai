import inspect
import os
from tkinter import filedialog

import pandas as pd

from . import deeplabcut_hdf, hdf_df, keypoints_proc, windows_and_mac


def open_pkl(init_dir, org_path=None, filetypes=[("pkl files", "*.pkl")]):
    if init_dir == "":
        init_dir = "~"

    tar_path = filedialog.askopenfilename(initialdir=init_dir, title="Select track file", filetypes=filetypes)
    if tar_path == "":
        print("open_pkl() canceled.")
        return org_path
    print(f"open_pkl() done. {tar_path}")

    return tar_path


def load_track_file(tar_path, allow_calculated_track_file=False):
    if os.path.exists(tar_path) is False:
        print(f"File not found: {tar_path}")
        return
    # 最終的な仕様は下記
    # pklをhdf5に変更, 拡張子は.trkにする予定(featの拡張子は最終的には.featに変更する予定)
    # 拡張子がh5なら
    #  HDF5を開いた後、group名(df_with_missing)でDLCか否かを判断して分岐
    #  group名が違う場合は読み込まない
    #  DLCの場合はmp4のファイル名等の情報を入力するためのダイアログを表示
    if tar_path.endswith(".h5"):
        src_df = load_dlc_h5(tar_path)
    else:
        src_df = pd.read_pickle(tar_path)
    if keypoints_proc.has_keypoint(src_df) is False and allow_calculated_track_file is False:
        print(f"No keypoint index in {tar_path}")
        return
    return src_df


def load_dlc_h5(tar_path):
    df = deeplabcut_hdf.read_h5(tar_path)
    kps, df = deeplabcut_hdf.transform_df(df, 29.98)

    # source information
    #  mp4 file name
    #  h5 file name
    #  fps
    #  frame size(w,h)
    df.attrs["video_name"] = "desk_2min_a.mp4"
    df.attrs["model"] = "DeepLabCut"
    df.attrs["frame_size"] = (3840, 2160)
    deeplabcut_hdf.generate_toml(kps)
    print(kps)
    return df


class PickleLoader:
    def __init__(self, init_dir=None, pkl_type="track", org_path=None):
        if init_dir is None or init_dir == "" or os.path.exists(init_dir) is False:
            self.init_dir = "~"
        else:
            self.init_dir = init_dir

        if pkl_type == "track":
            self.filetypes = [("pkl files", "*.pkl"), ("trk-pkl files", "*.trk.pkl"), ("HDF5 files", "*.h5")]
        elif pkl_type in ["feature", "behavioral_coding"]:
            self.filetypes = [("HDF5 files", "*.h5")]
        self.filetypes = windows_and_mac.file_types(self.filetypes)

        self.tar_path = org_path
        self.calc_case = None

    def join_calc_case(self, calc_case):
        new_init_dir = os.path.join(self.init_dir, calc_case)
        if os.path.exists(new_init_dir) is False:
            print(f"calc_case not found: {new_init_dir}")
            return
        self.init_dir = new_init_dir

    def show_open_dialog(self):
        """
        Update self.tar_path with the selected file path.
        Return bool value whether the file is selected or not.
        """
        tar_path = filedialog.askopenfilename(initialdir=self.init_dir, title="Select Pickle file", filetypes=self.filetypes)
        if tar_path == "":
            print("show_open_dialog() canceled.")
            return False
        self.tar_path = tar_path
        return True

    def load_pkl(self):
        """Return the loaded DataFrame."""
        if os.path.exists(self.tar_path) is False:
            print(f"File not found: {self.tar_path}")
            return
        src_df = pd.read_pickle(self.tar_path)
        frame_num = src_df.index.get_level_values(0).nunique()
        member_num = src_df.index.get_level_values(1).nunique()
        called_in = os.path.basename(inspect.stack()[1].filename)
        print(
            f"{called_in} < {os.path.basename(self.tar_path)}: shape={src_df.shape[0]:,}x{src_df.shape[1]} frames={frame_num:,} members={member_num}"
        )
        return src_df

    def load_dlc_h5(self):
        df = deeplabcut_hdf.read_h5(self.tar_path)
        kps, df = deeplabcut_hdf.transform_df(df, 29.98)

        df.attrs["video_name"] = "desk_2min_a.mp4"
        df.attrs["model"] = "DeepLabCut"
        df.attrs["frame_size"] = (3840, 2160)
        deeplabcut_hdf.generate_toml(kps)
        print(kps)
        return df

    def get_tar_path(self):
        return self.tar_path

    def get_tar_parent(self):
        return os.path.basename(os.path.dirname(self.tar_path))

    def set_tar_path(self, path):
        self.tar_path = path


def overwrite_track_file(tar_path, tar_df, not_found_ok=False):
    """
    上書きしようとしているファイルをバックアップしてから上書きする
    バックアップフォルダにバックアップを保存する
    バックアップ先にファイルがあったら上書きする
    """
    if os.path.exists(tar_path) is False and not_found_ok is True:
        tar_df.to_pickle(tar_path)
        pkl_name = os.path.basename(tar_path)
        return pkl_name

    if os.path.exists(tar_path) is False:
        print("File not found: {}".format(tar_path))
        return
    backup_dir = os.path.join(os.path.dirname(tar_path), "backup")
    os.makedirs(backup_dir, exist_ok=True)
    # 古いファイルをbackupに移動
    backup_path = os.path.join(backup_dir, os.path.basename(tar_path))
    # バックアップ先にファイルがあったら上書きする
    os.replace(tar_path, backup_path)
    tar_df.to_pickle(tar_path)
    pkl_name = os.path.basename(tar_path)
    return pkl_name


def save_pkl(org_pkl_path, dst_df, proc_history=None):
    file_name = os.path.basename(org_pkl_path)
    dst_dir = os.path.dirname(org_pkl_path)
    os.makedirs(dst_dir, exist_ok=True)

    if proc_history is not None:
        if "proc_history" not in dst_df.attrs.keys():
            dst_df.attrs["proc_history"] = [proc_history]
        else:
            dst_df.attrs["proc_history"].append(proc_history)
    file_name = filedialog.asksaveasfilename(
        title="Save as",
        filetypes=[("pickle", ".pkl")],
        initialdir=dst_dir,
        initialfile=file_name,
        defaultextension="pkl",
    )
    if file_name == "":
        print("export() canceled.")
        return
    dst_df.to_pickle(file_name)
    called_in = os.path.basename(inspect.stack()[1].filename)
    print(f"{called_in} > {os.path.basename(os.path.basename(file_name))}")


def save_h5(org_pkl_path, dst_df, df_type, proc_history=None):
    file_name = os.path.basename(org_pkl_path)
    dst_dir = os.path.dirname(org_pkl_path)
    os.makedirs(dst_dir, exist_ok=True)

    if proc_history is not None:
        if "proc_history" not in dst_df.attrs.keys():
            dst_df.attrs["proc_history"] = [proc_history]
        else:
            dst_df.attrs["proc_history"].append(proc_history)
    file_name = filedialog.asksaveasfilename(
        title="Save as",
        filetypes=[("HDf5 files", ".h5")],
        initialdir=dst_dir,
        initialfile=file_name,
        defaultextension="h5",
    )
    if file_name == "":
        print("export() canceled.")
        return

    hdf = hdf_df.DataFrameStorage(file_name)
    hdf.save_df(df_type, dst_df)

    #    dst_df.to_pickle(file_name)
    called_in = os.path.basename(inspect.stack()[1].filename)
    print(f"{called_in} > {os.path.basename(os.path.basename(file_name))}")


def pkl_to_csv(init_dir="~"):
    """
    pklファイルをcsvファイルに変換する
    ダイアログを開きファイルを選択させ、同じディレクトリにcsvファイルを保存する
    """
    pkl_path = open_pkl(init_dir)
    if pkl_path == "" or pkl_path is None:
        print("pkl_to_csv() canceled.")
        return
    csv_path = os.path.splitext(pkl_path)[0] + ".csv"
    df = load_track_file(pkl_path, allow_calculated_track_file=True)
    if df is None:
        return
    df.to_csv(csv_path)
    csv_name = os.path.basename(csv_path)
    return csv_name
