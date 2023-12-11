import sys
import os

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from python_senpai import keypoints_proc


trk_dir = "your/trk/dir"
head_trk = "your_trk_file.pkl"


trk_df = pd.read_pickle(os.path.join(trk_dir, head_trk))
if keypoints_proc.has_keypoint(trk_df) is True:
    print(trk_df)
else:
    print("No keypoint index in {}".format(head_trk))

print(trk_df.attrs)
