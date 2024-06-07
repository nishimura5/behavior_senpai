import os
import sys

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from python_senpai import file_inout, keypoints_proc

# macは/Users/username
video_dir = "%USERPROFILE%/Videos"
pl = file_inout.PickleLoader(init_dir=video_dir)
is_file_selected = pl.show_open_dialog()
if is_file_selected is False:
    print("No file selected.")
    sys.exit()
trk_path = pl.tar_path
trk_df = pl.load_pkl()

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
    else:
        print(f"{key}: {value}")

# frameとmemberの個数を表示
print("[index]")
print("frame :", trk_df.index.get_level_values("frame").unique().size)
print("member:", trk_df.index.get_level_values("member").unique().size)
if keypoints_proc.has_keypoint(trk_df) is True:
    print("keypoint:", trk_df.index.get_level_values("keypoint").unique().size)
