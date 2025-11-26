import os
import sys
from tkinter import filedialog

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from behavior_senpai import hdf_df, windows_and_mac


def load_hdf(tar_path):
    if os.path.exists(tar_path) is False:
        print(f"File not found: {tar_path}")
        return
    hdf = hdf_df.DataFrameStorage(tar_path)
    return hdf


video_dir = "%USERPROFILE%/Videos"

filetypes = [("Feature files", "*.feat")]
filetypes = windows_and_mac.file_types(filetypes)
hdf_path = filedialog.askopenfilename(initialdir=video_dir, title="Select Feature file", filetypes=filetypes)
if hdf_path == "":
    print("No file selected.")
    sys.exit()


tar_hdf = load_hdf(hdf_path)
profile_dict = tar_hdf.load_profile()
print("[Profile]")
print(profile_dict)

print("[Points]")
points_df = tar_hdf.load_points_df()
points_source_cols = tar_hdf.load_points_source_cols()
print(f"  Points DataFrame: shape={points_df.shape[0]:,}x{points_df.shape[1]}")
print("  Columns:")
for col in points_df.columns:
    print(f"    {col}")
print("  Source columns:")
for row in points_source_cols:
    print("    ", row)

print("[Mixnorm]")
mixnorm_df = tar_hdf.load_mixnorm_df()
mixnorm_source_cols = tar_hdf.load_mixnorm_source_cols()
print(f"  Mixnorm DataFrame: shape={mixnorm_df.shape[0]:,}x{mixnorm_df.shape[1]}")
print("  Columns:")
for col in mixnorm_df.columns:
    print(f"    {col}")
print("  Source columns:")
for row in mixnorm_source_cols:
    print("    ", row)
