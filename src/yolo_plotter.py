import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
import seaborn as sns


def plot(plot_df):
    fig, ax = plt.subplots(figsize=(16, 9))
    sns.lineplot(data=plot_df, x="timestamp", y="y", hue="member", style="keypoint", ax=ax)

    # 画像は左上が原点なので、y軸を反転させる
    ax.invert_yaxis()

    ax.xaxis.set_major_formatter(ticker.FuncFormatter(time_ticks))


def time_ticks(x, pos):
    return str(datetime.timedelta(milliseconds=x))


if __name__ == "__main__":
    pkl_path = "taiso.pkl"
    src_df = pd.read_csv(pkl_path)
    print(src_df)

    # 1人目の10番目のキーポイントのみ抽出
    member_id = [1, 2]
    keypoint_id = [10, 0]

    plot_df = src_df.loc[pd.IndexSlice[:, member_id, keypoint_id], :]
    plot(plot_df)
    plt.show()
