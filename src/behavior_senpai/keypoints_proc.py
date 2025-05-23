import time

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import pairwise_distances
from umap import UMAP


def has_keypoint(src_df):
    """
    src_dfにkeypointが含まれているかどうかを判定する
    """
    if "keypoint" in src_df.index.names:
        return True
    else:
        return False


def filter_by_timerange(src_df, start_msec: int, end_msec: int):
    """
    src_dfのtimestampの範囲を[start_msec, end_msec]に絞る
    """
    if start_msec > end_msec:
        print("start_msec > end_msec")
    dst_df = src_df.loc[src_df["timestamp"].between(start_msec - 1, end_msec + 1), :]
    # emptyなら空のDataFrameを返す
    if len(dst_df) == 0:
        print("Filtered DataFrame is empty.")
    return dst_df


def zero_point_to_nan(src_df):
    if "roi_left_top" in src_df.attrs:
        zero_point = src_df.attrs["roi_left_top"]
    else:
        zero_point = (0, 0)
    left, top = zero_point

    src_df.loc[(src_df["x"] == left) & (src_df["y"] == top), ["x", "y"]] = [np.nan, np.nan]

    members = src_df.index.get_level_values("member").unique().tolist()
    gohst_members = []
    for member in members:
        sliced_df = src_df.loc[pd.IndexSlice[:, member, :], :]
        sliced_df = sliced_df.loc[~(sliced_df["x"].isna()) & (~sliced_df["y"].isna())]
        if len(sliced_df.index.get_level_values(0).unique()) == 0:
            gohst_members.append(member)

    if len(gohst_members) > 0:
        print(f"{len(gohst_members)} members has no data")
        src_df = src_df.drop(gohst_members, level=1)

    return src_df


def calc_speed(src_df, step_frame: int):
    """
    src_dfの各keypointの速さを計算する
    speed = sqrt(dx^2 + dy^2) / step_frame
    dx = x(t) - x(t - step_frame)
    dy = y(t) - y(t - step_frame)
    """
    diff_df = src_df.groupby(level=["member", "keypoint"]).diff(step_frame) ** 2
    speed_df = pd.DataFrame(np.sqrt(diff_df["x"] + diff_df["y"]) / step_frame, columns=[f"spd_{step_frame}"])
    return speed_df


def calc_acceleration(speed_df, step_frame: int):
    """
    speed_dfの各keypointの加速度を計算する
    """
    diff_df = speed_df.groupby(level=["member", "keypoint"]).diff(step_frame)
    acc_df = pd.DataFrame(diff_df[f"spd_{step_frame}"] / step_frame).rename(columns={f"spd_{step_frame}": f"acc_{step_frame}"})
    return acc_df


def calc_total_distance(src_df, step_frame: int, per_plot=False):
    """
    src_dfの各keypointの総移動距離を計算する
    """
    diff_df = src_df.groupby(level=["member", "keypoint"]).diff(step_frame) ** 2
    total_distance_df = pd.DataFrame(np.sqrt(diff_df["x"] + diff_df["y"]).groupby(level=["member", "keypoint"]).sum(), columns=["total_distance"])
    if per_plot:
        plot_count_df = src_df.groupby(level=["member", "keypoint"]).size().to_frame("plot_count")
        total_distance_df = pd.concat([total_distance_df, plot_count_df], axis=1)
        total_distance_df["total_distance_per_plot"] = total_distance_df["total_distance"] / total_distance_df["plot_count"]
    return total_distance_df


def thinning(src_df, thinning: int):
    """
    thinningの値だけsrc_dfのframeを間引く
    thinningの倍数のframeのみを残す
    """
    if thinning <= 1:
        return src_df
    frames = src_df.index.get_level_values(0).unique().tolist()
    frames = frames[::thinning]
    thinned_df = src_df[src_df.index.get_level_values(0).isin(frames)]
    return thinned_df


def pca(src_df, tar_cols: list):
    """
    PCA: principal component analysis(主成分分析)
    src_dfのtar_colsを次元削減する
    """
    model = PCA(n_components=1)
    reduced_arr = model.fit_transform(src_df[tar_cols])
    return reduced_arr


def umap(src_df, tar_cols: list, n_components: int = 1, n_neighbors: int = 15, min_dist: float = 0.1, seed: int = None):
    start_time = time.perf_counter()
    if seed is not None:
        n_jobs = 1
    else:
        n_jobs = -1
    dst_df = pd.DataFrame()
    dst_df["timestamp"] = src_df["timestamp"]
    plot_df = src_df.dropna(how="all", axis=1)
    plot_df = plot_df.dropna(subset=tar_cols, how="any")
    model = UMAP(
        n_components=n_components, n_neighbors=n_neighbors, min_dist=min_dist, random_state=seed, n_jobs=n_jobs, tqdm_kwds={"disable": False}
    )
    reduced_arr = model.fit_transform(plot_df[tar_cols])
    reduced_df = pd.DataFrame(reduced_arr, columns=[f"umap_{i}" for i in range(n_components)], index=plot_df.index)
    reduced_df["umap_t"] = plot_df["timestamp"]
    dst_df = pd.concat([dst_df, reduced_df], axis=1)
    print(f"umap() (keypoints_proc):{time.perf_counter() - start_time:.3f}sec / {src_df.shape[0]:,}plots")
    return dst_df


def calc_recurrence(src_arr, threshold: float):
    """
    recurrence plotを計算する
    """
    distance_mat = pairwise_distances(src_arr, metric="euclidean")
    print(f"distance max:{distance_mat.max()}")
    if threshold == 0:
        dst_mat = distance_mat
    else:
        dst_mat = (distance_mat > threshold).astype(int)
    return dst_mat


def is_in_poly(src_df, poly_points, area_name, scale=1.0):
    """
    poly_pointsの内側にtarget_keypointがあったらTrue
    """
    tar_point = src_df
    in_out_df = pd.DataFrame()
    for i, point in enumerate(poly_points):
        vect_df = tar_point.copy()
        x_to = int(point[0] / scale)
        y_to = int(point[1] / scale)
        x_from = int(poly_points[i - 1][0] / scale)
        y_from = int(poly_points[i - 1][1] / scale)
        anchor_vector = np.array([x_to - x_from, y_to - y_from])
        vect_df["x"] = tar_point["x"] - x_from
        vect_df["y"] = tar_point["y"] - y_from
        cross_sr = anchor_vector[0] * vect_df["y"] - anchor_vector[1] * vect_df["x"]
        cross_sr = cross_sr < 0
        cross_df = cross_sr.to_frame()
        cross_df.columns = [i]
        in_out_df = pd.concat([in_out_df, cross_df], axis=1)
    # 全てのcolumnsがTrueならTrue
    isin_df = in_out_df.all(axis=1).to_frame()
    isin_df.columns = [area_name]
    return isin_df


def remove_by_bool_col(src_df, bool_col_name: str, drop_member: bool = False):
    """
    src_dfのbool_col_nameがFalseの行のxとyをnanにする
    drop_memberがTrueの場合は、keypointが1つでもFalseならそのmember丸ごとFalseにする
    """
    # concatでNanになった列をfloatにしてTrueで埋めてboolにする
    remove_sr = src_df[bool_col_name].astype("float").fillna(True).astype("bool")
    if drop_member is True:
        remove_sr = remove_sr.groupby(["frame", "member"]).transform("all")

    x_sr = np.where(remove_sr == False, np.nan, src_df["x"])
    y_sr = np.where(remove_sr == False, np.nan, src_df["y"])
    src_df["x"] = x_sr.copy()
    src_df["y"] = y_sr.copy()
    return src_df


def calc_xy_component(src_df, kp0: int, kp1: int):
    col_name_x = f"component_x({kp0}-{kp1})"
    col_name_y = f"component_y({kp0}-{kp1})"

    point0 = src_df.loc[pd.IndexSlice[:, :, kp0], :].droplevel(2)
    point1 = src_df.loc[pd.IndexSlice[:, :, kp1], :].droplevel(2)
    point1_0 = point1 - point0
    xy_df = point1_0.loc[:, ["x", "y"]]
    xy_df.columns = [col_name_x, col_name_y]
    return xy_df


def calc_direction(src_df, kp0: int, kp1: int):
    """
    Calculate the direction of kp0 -> kp1
    """
    col_name_sin = f"sin({kp0}-{kp1})"
    col_name_cos = f"cos({kp0}-{kp1})"
    point0 = src_df.loc[pd.IndexSlice[:, :, kp0], :].droplevel(2)
    point1 = src_df.loc[pd.IndexSlice[:, :, kp1], :].droplevel(2)
    point1_0 = point1 - point0
    norm = np.sqrt(point1_0["x"] ** 2 + point1_0["y"] ** 2)
    sin_sr = point1_0["y"] / norm
    cos_sr = point1_0["x"] / norm
    sin_cos_df = pd.concat([sin_sr, cos_sr], axis=1)
    sin_cos_df.columns = [col_name_sin, col_name_cos]
    return sin_cos_df


def calc_angle2(src_df, kp0: int, kp1: int):
    """
    Calculate the direction of kp0 -> kp1 in degrees (fast version)
    """
    col_name = f"deg({kp0}-{kp1})"

    # x, y のみを抽出
    xy_df = src_df.loc[:, ["x", "y"]]

    # 各キーポイントの座標を取得
    point0 = xy_df.xs(kp0, level="keypoint", drop_level=False)
    point1 = xy_df.xs(kp1, level="keypoint", drop_level=False)

    p0 = point0.to_numpy()
    p1 = point1.to_numpy()

    vec = p1 - p0

    angles_deg = np.degrees(np.arctan2(vec[:, 1], vec[:, 0]))
    angle_df = pd.DataFrame({col_name: angles_deg}, index=point0.index.droplevel("keypoint"))

    return angle_df


def calc_norm(src_df, kp0: int, kp1: int):
    col_name = f"norm({kp0}-{kp1})"
    point0 = src_df.loc[pd.IndexSlice[:, :, kp0], :].droplevel(2)
    point1 = src_df.loc[pd.IndexSlice[:, :, kp1], :].droplevel(2)
    point1_0 = point1 - point0
    norms_sr = np.sqrt(point1_0["x"] ** 2 + point1_0["y"] ** 2)
    norms_df = norms_sr.to_frame()
    norms_df.columns = [col_name]
    return norms_df


def calc_plus(src_df, kp0: int, kp1: int, kp2: int):
    """
    kp0 -> kp1とkp0 -> kp2のベクトル和を計算する
    """
    col_name_x = f"plus_x({kp0}-{kp1},{kp0}-{kp2})"
    col_name_y = f"plus_y({kp0}-{kp1},{kp0}-{kp2})"
    point0 = src_df.loc[pd.IndexSlice[:, :, kp0], :].droplevel(2)
    point1 = src_df.loc[pd.IndexSlice[:, :, kp1], :].droplevel(2)
    point2 = src_df.loc[pd.IndexSlice[:, :, kp2], :].droplevel(2)
    point1_0 = point1 - point0
    point2_0 = point2 - point0
    plus_df = point1_0.loc[:, ["x", "y"]] + point2_0.loc[:, ["x", "y"]]
    plus_df.columns = [col_name_x, col_name_y]
    return plus_df


def calc_cross_product(src_df, kp0: int, kp1: int, kp2: int):
    """
    kp0 -> kp1とkp0 -> kp2の外積を計算する
    """
    col_name = f"cross({kp0}-{kp1},{kp0}-{kp2})"
    point0 = src_df.loc[pd.IndexSlice[:, :, kp0], :].droplevel(2)
    point1 = src_df.loc[pd.IndexSlice[:, :, kp1], :].droplevel(2)
    point2 = src_df.loc[pd.IndexSlice[:, :, kp2], :].droplevel(2)
    point1_0 = point1 - point0
    point2_0 = point2 - point0
    cross_sr = point1_0["x"] * point2_0["y"] - point1_0["y"] * point2_0["x"]
    cross_df = cross_sr.to_frame()
    cross_df.columns = [col_name]
    return cross_df


def calc_dot_product(src_df, kp0: int, kp1: int, kp2: int):
    """
    kp0 -> kp1とkp0 -> kp2の内積を計算する
    """
    col_name = f"dot({kp0}-{kp1},{kp0}-{kp2})"
    point0 = src_df.loc[pd.IndexSlice[:, :, kp0], :].droplevel(2)
    point1 = src_df.loc[pd.IndexSlice[:, :, kp1], :].droplevel(2)
    point2 = src_df.loc[pd.IndexSlice[:, :, kp2], :].droplevel(2)
    point1_0 = point1 - point0
    point2_0 = point2 - point0
    dot_sr = point1_0["x"] * point2_0["x"] + point1_0["y"] * point2_0["y"]
    dot_df = dot_sr.to_frame()
    dot_df.columns = [col_name]
    return dot_df


def calc_sin_cos(src_df, kp0: int, kp1: int, kp2: int):
    point0 = src_df.loc[pd.IndexSlice[:, :, kp0], :].droplevel(2)
    point1 = src_df.loc[pd.IndexSlice[:, :, kp1], :].droplevel(2)
    point2 = src_df.loc[pd.IndexSlice[:, :, kp2], :].droplevel(2)
    point1_0 = point1 - point0
    point2_0 = point2 - point0
    norm = np.sqrt(point1_0["x"] ** 2 + point1_0["y"] ** 2) * np.sqrt(point2_0["x"] ** 2 + point2_0["y"] ** 2)
    sin_sr = (point1_0["x"] * point2_0["y"] - point1_0["y"] * point2_0["x"]) / norm
    cos_sr = (point1_0["x"] * point2_0["x"] + point1_0["y"] * point2_0["y"]) / norm
    sin_cos_df = pd.concat([sin_sr, cos_sr], axis=1)
    sin_cos_df.columns = [f"sin({kp0}-{kp1},{kp0}-{kp2})", f"cos({kp0}-{kp1},{kp0}-{kp2})"]
    return sin_cos_df


def calc_angle3(src_df, kp0: int, kp1: int, kp2: int):
    """
    kp0 -> kp1とkp0 -> kp2の角度を計算する
    """
    col_name = f"angle({kp0}-{kp1},{kp0}-{kp2})"

    # x, y のみを抽出（インデックスはそのまま）
    xy_df = src_df.loc[:, ["x", "y"]]

    # 各キーポイントの座標を取得
    point0 = xy_df.xs(kp0, level="keypoint", drop_level=False)
    point1 = xy_df.xs(kp1, level="keypoint", drop_level=False)
    point2 = xy_df.xs(kp2, level="keypoint", drop_level=False)

    p0 = point0.to_numpy()
    p1 = point1.to_numpy()
    p2 = point2.to_numpy()

    vec1 = p1 - p0
    vec2 = p2 - p0

    dot_product = np.einsum("ij,ij->i", vec1, vec2)
    norm1 = np.linalg.norm(vec1, axis=1)
    norm2 = np.linalg.norm(vec2, axis=1)

    cos_angle = np.clip(dot_product / (norm1 * norm2), -1.0, 1.0)

    angles = np.arccos(cos_angle)
    angles = np.degrees(angles)
    angle_df = pd.DataFrame(angles, index=point0.index.droplevel("keypoint"), columns=[col_name])
    return angle_df


def calc_norms(src_df, kp0: int, kp1: int, kp2: int):
    """
    kp0 -> kp1とkp0 -> kp2のベクトルのノルムの積を計算する
    """
    col_name = f"norms({kp0}-{kp1},{kp0}-{kp2})"
    point0 = src_df.loc[pd.IndexSlice[:, :, kp0], :].droplevel(2)
    point1 = src_df.loc[pd.IndexSlice[:, :, kp1], :].droplevel(2)
    point2 = src_df.loc[pd.IndexSlice[:, :, kp2], :].droplevel(2)
    point1_0 = point1 - point0
    point2_0 = point2 - point0
    norms_sr = np.sqrt(point1_0["x"] ** 2 + point1_0["y"] ** 2) * np.sqrt(point2_0["x"] ** 2 + point2_0["y"] ** 2)
    norms_df = norms_sr.to_frame()
    norms_df.columns = [col_name]
    return norms_df


def calc_cross_dot_plus_norms(src_df, kp0: int, kp1: int, kp2: int):
    """
    kp0 -> kp1とkp0 -> kp2の外積、内積、ベクトル和、ノルムの積を計算する
    別々にやるより少し速い
    """
    point0 = src_df.loc[pd.IndexSlice[:, :, kp0], :].droplevel(2)
    point1 = src_df.loc[pd.IndexSlice[:, :, kp1], :].droplevel(2)
    point2 = src_df.loc[pd.IndexSlice[:, :, kp2], :].droplevel(2)
    point1_0 = point1 - point0
    point2_0 = point2 - point0

    # cross
    col_name = f"cross({kp0}-{kp1},{kp0}-{kp2})"
    cross_sr = point1_0["x"] * point2_0["y"] - point1_0["y"] * point2_0["x"]
    cross_df = cross_sr.to_frame()
    cross_df.columns = [col_name]

    # dot
    col_name = f"dot({kp0}-{kp1},{kp0}-{kp2})"
    dot_sr = point1_0["x"] * point2_0["x"] + point1_0["y"] * point2_0["y"]
    dot_df = dot_sr.to_frame()
    dot_df.columns = [col_name]

    # plus
    col_name = f"plus({kp0}-{kp1},{kp0}-{kp2})"
    plus_df = point1_0.loc[:, ["x", "y"]] + point2_0.loc[:, ["x", "y"]]
    plus_df.columns = [f"{col_name}_x", f"{col_name}_y"]

    # norms
    col_name = f"norms({kp0}-{kp1},{kp0}-{kp2})"
    norms_sr = np.sqrt(point1_0["x"] ** 2 + point1_0["y"] ** 2) * np.sqrt(point2_0["x"] ** 2 + point2_0["y"] ** 2)
    norms_df = norms_sr.to_frame()
    norms_df.columns = [col_name]

    dst_df = pd.concat([cross_df, dot_df, plus_df, norms_df], axis=1)
    return dst_df


def calc_moving_average(src_df, window_size: int):
    """
    timestamp以外の全てのカラムを移動平均する
    indexがframe-memberの場合にのみ対応
    """
    rolling_df = pd.DataFrame()
    columns = src_df.columns.drop("timestamp")
    # indexのlevelが2つの場合
    if len(src_df.index.levels) == 2:
        rolling_df = src_df[columns].reset_index(["member"])
        rolling_df = rolling_df.groupby(["member"], as_index=True).rolling(window=window_size, center=True).mean()
        rolling_df = rolling_df.swaplevel("frame", "member").sort_index()
    elif len(src_df.index.levels) == 3:
        rolling_df = src_df[columns].reset_index(["member", "keypoint"])
        rolling_df = rolling_df.groupby(["member", "keypoint"], as_index=True).rolling(window=window_size, center=True).mean()
        rolling_df = rolling_df.swaplevel("frame", "member")
        rolling_df = rolling_df.swaplevel("member", "keypoint").sort_index()
    rolling_df["timestamp"] = src_df["timestamp"]
    return rolling_df


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    pd.set_option("display.min_rows", 100)
    pd.set_option("display.max_rows", 100)

    # テストデータ生成
    frame_num = 1000
    frames = range(frame_num)
    members = ["test1", "test2"]
    keypoints = [f"{i}" for i in range(1, 11)]
    data = {"frame": [], "member": [], "keypoint": [], "x": [], "y": [], "timestamp": []}
    for f in frames:
        for m in members:
            for k in keypoints:
                data["frame"].append(f)
                data["member"].append(m)
                data["keypoint"].append(k)
                data["x"].append(np.sin(2 * np.pi * f / frame_num) * 500 + 500)
                data["y"].append(np.cos(2 * np.pi * f / frame_num) * 500 + 500)
                data["timestamp"].append(f)
    test_df = pd.DataFrame(data).set_index(["frame", "member", "keypoint"])

    # テストデータをpkl出力
    #    test_df.attrs['video_name'] = 'test.mp4'
    #    test_df.attrs['frame_size'] = (500, 500)
    #    test_df.to_pickle('test.pkl')

    # calc_speed, calc_acceleration
    dt_span = 10
    speed_df = calc_speed(test_df, dt_span)
    acc_df = calc_acceleration(speed_df, dt_span)
    test_speed_df = pd.concat([test_df, speed_df, acc_df], axis=1)

    # thinning
    thinning_val = 140
    thinned_df = thinning(test_speed_df, thinning_val)

    # グラフ描画
    fig, ax = plt.subplots(4, 1)
    plot_df = test_speed_df.loc[pd.IndexSlice[:, "test1", "1"], :]
    # テストデータ
    ax[0].plot(plot_df["timestamp"], plot_df["x"], label="x")
    ax[0].plot(plot_df["timestamp"], plot_df["y"], label="y")
    ax[0].set_ylabel("x, y")
    ax[0].legend()
    # speed
    ax[1].plot(plot_df["timestamp"], plot_df[f"spd_{dt_span}"], label="speed")
    ax[1].set_ylim(0, 5)
    ax[1].set_ylabel(f"speed ({dt_span})")
    ax[1].axhline(np.pi, color="gray", lw=0.5)
    # acceleration
    ax[2].plot(plot_df["timestamp"], plot_df[f"acc_{dt_span}"], label="acceleration")
    ax[2].set_ylim(-5, 5)
    ax[2].set_ylabel(f"acceleration ({dt_span})")
    # thinning
    ax[3].plot(thinned_df["timestamp"], thinned_df["x"], label="x")
    ax[3].plot(thinned_df["timestamp"], thinned_df["y"], label="y")
    ax[3].set_ylabel(f"x, y ({thinning_val})")

    plt.show()
