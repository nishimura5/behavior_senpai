import sys
import os

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from python_senpai import time_format
from python_senpai import file_inout


def concat_track_file(head_df, next_path):
    """
    2つのTrack fileを結合する
    """
    if "next" in head_df.attrs:
        next_df = pd.read_pickle(next_path)

        prev_max_frame = head_df.index.get_level_values("frame").max()
        next_df.index = next_df.index.set_levels(next_df.index.levels[0] + prev_max_frame + 1, level=0)

        prev_max_timestamp = head_df["timestamp"].max()
        step = head_df.loc[pd.IndexSlice[:, :, :], "timestamp"].diff().max()
        next_df["timestamp"] = next_df["timestamp"] + prev_max_timestamp + step

        tar_df = pd.concat([head_df, next_df], axis=0)
    else:
        tar_df = head_df

    tar_df.attrs = head_df.attrs
    tar_df.attrs['second_video'] = next_df.attrs['video_name']
    tar_df.attrs['first_total_msec'] = head_df.loc[pd.IndexSlice[:, :, :], "timestamp"].max()
    return tar_df
