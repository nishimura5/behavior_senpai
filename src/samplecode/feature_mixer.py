import os
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.stats import jarque_bera
from sklearn.preprocessing import RobustScaler

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from behavior_senpai import file_inout

# Load Feature file
video_dir = "%USERPROFILE%/Videos"
pkl_path = file_inout.open_pkl(video_dir)
src_df = file_inout.load_track_file(pkl_path, allow_calculated_track_file=True)

# Rename Member Code with file name
tar_member = "face"
renamed_member = os.path.basename(pkl_path).split(".")[0]
src_df = src_df.rename(index={tar_member: renamed_member})

# Print Columns
cols = src_df.columns
print(f"src_df.columns: {cols}")

mixed_df = pd.DataFrame()
mixed_df["new_feature"] = src_df["norm(61-291)"] / src_df["norm(143-372)"]
mixed_df["new_feature2"] = src_df["norm(55-285)"] / src_df["norm(143-372)"]
mixed_df["new_feature3"] = src_df["norm(13-14)"]
mixed_df["new_feature4"] = src_df["norm(143-372)"]

print("=======")
for col in mixed_df.columns:
    stat, p = jarque_bera(mixed_df[col])
    mean = mixed_df[col].mean()
    std = mixed_df[col].std()
    print(f"{col}: p={p:.3f}, mean={mean:.4f}, std={std:.4f}")

# robust scale remove outliers
scaler = RobustScaler(quantile_range=(25, 75))
scaled_df = pd.DataFrame(scaler.fit_transform(mixed_df), columns=mixed_df.columns)
print(scaled_df)

# plot
sns.violinplot(data=scaled_df)
plt.show()

# to pickle
out_dir = os.path.dirname(pkl_path)
pkl_path = os.path.join(out_dir, f"mixed_{renamed_member}.pkl")
file_inout.save_pkl(pkl_path, scaled_df)
