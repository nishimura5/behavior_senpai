import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.decomposition import PCA


def calc_speed(src_df, step_frame: int):
    '''
    src_dfの各keypointの速さを計算する
    speed = sqrt(dx^2 + dy^2)
    dx = x(t) - x(t - step_frame)
    dy = y(t) - y(t - step_frame)
    '''
    diff_df = src_df.groupby(level=['member', 'keypoint']).diff(step_frame)**2
    speed_df = pd.DataFrame(np.sqrt(diff_df['x'] + diff_df['y']) / step_frame, columns=[f'dt_{step_frame}'])
    return speed_df


def thinning(src_df, thinning: int):
    '''
    thinningの値だけsrc_dfのframeを間引く
    thinningの倍数のframeのみを残す
    '''
    if thinning <= 1:
        return src_df
    frames = src_df.index.get_level_values(0).unique().tolist()
    frames = frames[::thinning]
    thinned_df = src_df[src_df.index.get_level_values(0).isin(frames)]
    return thinned_df


def pca(src_df, members: list, keypoints: list, tar_cols: list):
    '''
    src_dfのtar_colsを次元削減する
    '''
    tar_df = src_df.loc[pd.IndexSlice[:, members, keypoints], [*tar_cols, 'timestamp']].dropna()

    pca = PCA(n_components=1)
    pca.fit(tar_df[tar_cols])
    reduced_arr = pca.transform(tar_df[tar_cols])
    timestamps = tar_df['timestamp'].values
    return reduced_arr, timestamps


def calc_recurrence(src_arr, threshold: float):
    '''
    recurrence plotを計算する
    '''
    distance_mat = pairwise_distances(src_arr)
    print(distance_mat.max())
    bin_mat = (distance_mat > threshold).astype(int)
    return bin_mat


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    pd.set_option("display.min_rows", 100)
    pd.set_option("display.max_rows", 100)

    # テストデータ生成
    frame_num = 1000
    frames = range(frame_num)
    members = ['test1', 'test2'] 
    keypoints = [f'{i}' for i in range(1, 11)]
    data = {'frame': [], 'member': [], 'keypoint': [], 'x': [], 'y': [], 'timestamp': []}
    for f in frames:
        for m in members:
            for k in keypoints:
                data['frame'].append(f)
                data['member'].append(m)
                data['keypoint'].append(k)
                data['x'].append(np.sin(2 * np.pi * f / frame_num) * 500 + 500)
                data['y'].append(np.cos(2 * np.pi * f / frame_num) * 500 + 500)
                data['timestamp'].append(f)
    test_df = pd.DataFrame(data).set_index(['frame', 'member', 'keypoint'])

    # テストデータをpkl出力
#    test_df.attrs['video_name'] = 'test.mp4'
#    test_df.attrs['frame_size'] = (500, 500)
#    test_df.to_pickle('test.pkl')

    # calc_speed
    dt_span = 10
    speed_df = calc_speed(test_df, dt_span)
    test_speed_df = pd.concat([test_df, speed_df], axis=1)

    # thinning
    thinning_val = 140
    thinned_df = thinning(test_speed_df, thinning_val)

    # グラフ描画
    fig, ax = plt.subplots(3, 1)
    plot_df = test_speed_df.loc[pd.IndexSlice[:, 'test1', '1'], :]
    # テストデータ
    ax[0].plot(plot_df['timestamp'], plot_df['x'], label='x')
    ax[0].plot(plot_df['timestamp'], plot_df['y'], label='y')
    ax[0].set_ylabel('x, y')
    ax[0].legend()
    # speed
    ax[1].plot(plot_df['timestamp'], plot_df[f'dt_{dt_span}'], label='speed')
    ax[1].set_ylim(0, 5)
    ax[1].set_ylabel(f'speed ({dt_span})')
    ax[1].axhline(np.pi, color='gray', lw=0.5)
    # thinning
    ax[2].plot(thinned_df['timestamp'], thinned_df['x'], label='x')
    ax[2].plot(thinned_df['timestamp'], thinned_df['y'], label='y')
    ax[2].set_ylabel(f'x, y ({thinning_val})')

    plt.show()
