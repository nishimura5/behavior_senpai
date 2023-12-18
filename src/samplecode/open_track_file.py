import sys
import os

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from python_senpai import keypoints_proc
from python_senpai import file_inout


# macは/Users/username
video_dir = "%USERPROFILE%/Videos"
trk_path = file_inout.open_pkl(video_dir)

trk_df = pd.read_pickle(trk_path)
print("[Head]")
if keypoints_proc.has_keypoint(trk_df) is True:
    print(trk_df.head())
else:
    print("No keypoint index in {}".format(trk_path))
    print(trk_df.head())

print("[attrs]")
print(trk_df.attrs)

# frameとmemberの個数を表示
print("[index]")
print("frame :", trk_df.index.get_level_values("frame").unique().size)
print("member:", trk_df.index.get_level_values("member").unique().size)
if keypoints_proc.has_keypoint(trk_df) is True:
    print("keypoint:", trk_df.index.get_level_values("keypoint").unique().size)
