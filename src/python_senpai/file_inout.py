import os
from tkinter import filedialog

import pandas as pd

from . import keypoints_proc


def open_pkl(org_pkl_path):
    init_dir = "~"
    if org_pkl_path != "":
        init_dir = os.path.dirname(org_pkl_path)

    trk_path = filedialog.askopenfilename(
        initialdir=init_dir,
        title="Select Track file",
        filetypes=[("pkl files", "*.pkl")]
    )
    if trk_path == "":
        trk_path = org_pkl_path
    return trk_path


def load_track_file(tar_path, allow_calculated_track_file=False):
    if os.path.exists(tar_path) is False:
        print("File not found: {}".format(tar_path))
        return
    src_df = pd.read_pickle(tar_path)
    if keypoints_proc.has_keypoint(src_df) is False and allow_calculated_track_file is False:
        print("No keypoint index in {}".format(tar_path))
        return
    return src_df


def overwrite_track_file(tar_path, tar_df, not_found_ok=False):
    '''
    上書きしようとしているファイルをバックアップしてから上書きする
    バックアップフォルダにバックアップを保存する
    バックアップ先にファイルがあったら上書きする
    '''
    if os.path.exists(tar_path) is False and not_found_ok is True:
        tar_df.to_pickle(tar_path)
        pkl_name = os.path.basename(tar_path)
        return pkl_name

    if os.path.exists(tar_path) is False:
        print("File not found: {}".format(tar_path))
        return
    backup_dir = os.path.join(os.path.dirname(tar_path), 'backup')
    os.makedirs(backup_dir, exist_ok=True)
    # 古いファイルをbackupに移動
    backup_path = os.path.join(backup_dir, os.path.basename(tar_path))
    # バックアップ先にファイルがあったら上書きする
    os.replace(tar_path, backup_path)
    tar_df.to_pickle(tar_path)
    pkl_name = os.path.basename(tar_path)
    return pkl_name


def save_pkl(org_pkl_path, calc_case, dst_df, proc_history=None):
    file_name = os.path.basename(org_pkl_path)
    dst_dir = os.path.join(os.path.dirname(org_pkl_path), os.pardir, 'calc', calc_case)
    os.makedirs(dst_dir, exist_ok=True)

    if proc_history is not None:
        if 'proc_history' not in dst_df.attrs.keys():
            dst_df.attrs['proc_history'] = [proc_history]
        else:
            dst_df.attrs['proc_history'].append(proc_history)
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
    print("export() done.")


def pkl_to_csv(init_dir="~"):
    '''
    pklファイルをcsvファイルに変換する
    ダイアログを開きファイルを選択させ、同じディレクトリにcsvファイルを保存する
    '''
    pkl_path = filedialog.askopenfilename(
        initialdir=init_dir,
        title="Select pkl file",
        filetypes=[("pkl files", "*.pkl")]
    )
    if pkl_path == "":
        print("pkl_to_csv() canceled.")
        return
    csv_path = os.path.splitext(pkl_path)[0] + ".csv"
    df = pd.read_pickle(pkl_path)
    df.to_csv(csv_path)
    csv_name = os.path.basename(csv_path)
    return csv_name
