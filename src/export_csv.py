import os
from tkinter import messagebox


def save_dataframe(src_df, pkl_dir, file_name, index=True):
    """Save a DataFrame in the project's csv directory."""
    dst_dir = os.path.join(pkl_dir, os.pardir, "csv")
    os.makedirs(dst_dir, exist_ok=True)

    dst_path = os.path.join(dst_dir, file_name)
    src_df.to_csv(dst_path, index=index)
    messagebox.showinfo("Export CSV", f"Export finished.\nfile name: {file_name}")
    return dst_path


def export(start_msec, end_msec, member, src_df, pkl_dir):
    # extract dataframe by time range
    # dataframe is below format:
    # index: MultiIndex(levels=[frame, member, keypoint]
    # columns: x, y, timestamp(ms)
    timestamp_range = (src_df["timestamp"] >= start_msec) & (src_df["timestamp"] <= end_msec)
    out_df = src_df[timestamp_range]
    # member filter
    out_df = out_df.loc[out_df.index.get_level_values(1) == member]
    file_name = f"export_{start_msec}_{end_msec}_{member}.csv"
    return save_dataframe(out_df, pkl_dir, file_name)
