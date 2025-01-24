import pandas as pd


def read_h5(file_path):
    with pd.HDFStore(file_path, "r") as store:
        if "/df_with_missing" not in store.keys():
            raise ValueError("No data found in the file.")
        df = store.get("df_with_missing")
        return df


def get_keypoint_codes(src_df):
    src_df.columns = src_df.columns.droplevel(0)
    keypoints = src_df.columns.get_level_values("bodyparts").unique()
    # rename keypoints string to int
    rename_table = {k: i for i, k in enumerate(keypoints)}
    return rename_table


def transform_df(src_df, rename_table, fps):
    src_df.columns = src_df.columns.droplevel(0)
    frames = src_df.index
    keypoints = src_df.columns.get_level_values("bodyparts").unique()

    multi_index = pd.MultiIndex.from_product([frames, ["0"], keypoints], names=["frame", "member", "keypoint"])
    x_values = []
    y_values = []
    likelihood_values = []

    for frame in frames:
        for keypoint in keypoints:
            x_values.append(src_df.loc[frame, (keypoint, "x")])
            y_values.append(src_df.loc[frame, (keypoint, "y")])
            likelihood_values.append(src_df.loc[frame, (keypoint, "likelihood")])

    dst_df = pd.DataFrame(
        {"x": x_values, "y": y_values, "likelihood": likelihood_values},
        index=multi_index,
    )

    dst_df = dst_df.rename(index=rename_table, level=2)

    # Add timestamp column
    dst_df["timestamp"] = dst_df.index.get_level_values("frame") / fps * 1000

    return dst_df


def generate_toml(rename_table, color_rgb_str="[40,40,255]"):
    # search values in the rename_table and get val=0
    zero_key = [k for k, v in rename_table.items() if v == 0][0]
    with open("src/keypoint/deeplabcut.toml", "w") as f:
        f.write("[keypoints]\n")
        for k, v in rename_table.items():
            f.write(f'"{k}" = {{id={v}, color={color_rgb_str}}}\n')
        f.write("\n")
        f.write("[draw]\n")
        f.write(f'labels = ["{zero_key}"]\n')
        f.write(f'mask = ["{zero_key}"]\n')
        f.write("\n")
        f.write("[bones]\n")
        f.write("bones = []\n")
        f.write("\n")
        f.write("threshold = 0.4\n")
