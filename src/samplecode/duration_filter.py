import os
import sys

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from behavior_senpai import file_inout, time_format

DURATION_MSEC_THRESHOLD = 1000 * 60

# macは/Users/username
video_dir = "%USERPROFILE%/Videos"
trk_path = file_inout.open_pkl(video_dir)

trk_df = pd.read_pickle(trk_path)

print("member, start, end, duration")
groups = trk_df.groupby("member")
for name, group in groups:
    duration = group["timestamp"].max() - group["timestamp"].min()
    # 写っている時間がDURATION_MSEC_THRESHOLDより短いものは除外
    if duration < DURATION_MSEC_THRESHOLD:
        continue
    time_min = time_format.msec_to_timestr_with_fff(group["timestamp"].min())
    time_max = time_format.msec_to_timestr_with_fff(group["timestamp"].max())
    duration_str = time_format.msec_to_timestr_with_fff(duration)
    print(f"{name}, {time_min}, {time_max}, {duration_str}")
