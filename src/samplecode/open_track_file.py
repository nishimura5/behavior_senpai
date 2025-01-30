import inspect
import os
import sys
from tkinter import filedialog

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from behavior_senpai import keypoints_proc, windows_and_mac


def load_pkl(tar_path):
    """Return the loaded DataFrame."""
    if os.path.exists(tar_path) is False:
        print(f"File not found: {tar_path}")
        return
    src_df = pd.read_pickle(tar_path)
    frame_num = src_df.index.get_level_values(0).nunique()
    member_num = src_df.index.get_level_values(1).nunique()
    called_in = os.path.basename(inspect.stack()[1].filename)
    print(f"{called_in} < {os.path.basename(trk_path)}: shape={src_df.shape[0]:,}x{src_df.shape[1]} frames={frame_num:,} members={member_num}")
    return src_df


# macは/Users/username
video_dir = "%USERPROFILE%/Videos"

filetypes = [("Track files", "*.pkl")]
filetypes = windows_and_mac.file_types(filetypes)
trk_path = filedialog.askopenfilename(initialdir=video_dir, title="Select Pickle file", filetypes=filetypes)
if trk_path == "":
    print("No file selected.")
    sys.exit()
trk_df = load_pkl(trk_path)

print("[Head]")
if keypoints_proc.has_keypoint(trk_df) is True:
    print(trk_df.head())
else:
    print("No keypoint index in {}".format(trk_path))
    print(trk_df.head())

print("[attrs]")
for key, value in trk_df.attrs.items():
    if isinstance(value, dict):
        print(f"{key}:")
        for key2, value2 in value.items():
            print(f"  {key2}: {value2}")
    elif key == "proc_history" and isinstance(value, list):
        for i, value2 in enumerate(value):
            print(f"{key}[{i}]:")
            if isinstance(value2, dict):
                for key3, value3 in value2.items():
                    print(f"  {key3}: {value3}")
            else:
                print(f"  {value2}")
    else:
        print(f"{key}: {value}")

# frameとmemberの個数を表示
print("[index]")
print("frame :", trk_df.index.get_level_values("frame").unique().size)
print("member:", trk_df.index.get_level_values("member").unique().size)
if keypoints_proc.has_keypoint(trk_df) is True:
    print("keypoint:", trk_df.index.get_level_values("keypoint").unique().size)
