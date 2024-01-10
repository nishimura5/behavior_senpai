import os

import pandas as pd


def concat_track_file(head_df, trk_dir, trk_prefix=''):
    '''
    nextが記録されたtrack fileを結合する
    3つ以上のtrack fileを結合するときは、この関数を繰り返し使う
    '''

    if "next" not in head_df.attrs:
        print("next is not in attrs")
        return None

    next_path = os.path.join(trk_dir, f"{trk_prefix}{head_df.attrs['next']}")
    if os.path.exists(next_path) is False:
        print(f"next_path({next_path}) is not found")
        return None

    next_df = pd.read_pickle(next_path)
    prev_max_frame = head_df.index.get_level_values("frame").max()
    next_df.index = next_df.index.set_levels(next_df.index.levels[0] + prev_max_frame + 1, level=0)

    prev_max_timestamp = head_df["timestamp"].max()
    step = head_df.loc[pd.IndexSlice[:, :, :], "timestamp"].diff().max()
    next_df["timestamp"] = next_df["timestamp"] + prev_max_timestamp + step

    tar_df = pd.concat([head_df, next_df], axis=0)
    # 新しいdfにはhead_dfのattrsが引き継がれる
    tar_df.attrs = head_df.attrs
    # nextだけはnext_dfの値が引き継がれる
    tar_df.attrs['next'] = next_df.attrs['next']

    # head_dfの総時間(msec)とnext_dfのvideo_nameが新たに記録される
    if "video_name_list" not in tar_df.attrs.keys():
        tar_df.attrs['video_name_list'] = []
        tar_df.attrs['total_msec_list'] = []
    tar_df.attrs['video_name_list'].append(next_df.attrs['video_name'])
    tar_df.attrs['total_msec_list'].append(head_df.loc[pd.IndexSlice[:, :, :], "timestamp"].max())

    return tar_df
