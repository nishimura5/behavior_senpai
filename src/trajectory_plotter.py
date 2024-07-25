import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import gridspec, ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from python_senpai import time_format


class TrajectoryPlotter:
    def __init__(self, fig_size: tuple, dpi=72):
        self.dpi = dpi
        self.fig_size = fig_size
        self.fig = plt.figure(figsize=self.fig_size, dpi=self.dpi)
        self.fig.canvas.mpl_connect("motion_notify_event", self._gray_line)
        self.fig.canvas.mpl_connect("pick_event", self._click_graph)

        # axesのレイアウト設定
        gs = gridspec.GridSpec(2, 2, width_ratios=self.fig_size, height_ratios=[1, 1], top=0.94, bottom=0.05, hspace=0.04, wspace=0.03)
        self.traj_ax = self.fig.add_subplot(gs[1, 1])
        self.x_time_ax = self.fig.add_subplot(gs[0, 1], sharex=self.traj_ax)
        self.y_time_ax = self.fig.add_subplot(gs[1, 0], sharey=self.traj_ax)
        self.speed_ax = self.fig.add_subplot(gs[0, 0], sharex=self.y_time_ax)
        self.x_h = None
        self.y_v = None
        self.dt_v = None

    def pack(self, master):
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        toolbar = NavigationToolbar2Tk(self.canvas, master)
        toolbar.pack()
        self.canvas.get_tk_widget().pack(expand=False)

    def set_draw_param(self, kde_alpha, kde_adjust, kde_thresh, kde_levels):
        self.kde_alpha = kde_alpha
        self.kde_adjust = kde_adjust
        self.kde_thresh = kde_thresh
        self.kde_levels = kde_levels

    def set_vcap(self, vcap):
        self.vcap = vcap

    def draw(self, plot_df, member: str, keypoint: str, dt_span: int, thinning: int):
        # 重複インデックス削除
        plot_df = plot_df[~plot_df.index.duplicated(keep="last")]
        plot_df = plot_df.loc[pd.IndexSlice[:, member, keypoint], :]
        plot_len = len(plot_df["x"])
        width, height = self.vcap.get_frame_size()
        self.traj_ax.cla()

        if self.x_h is not None:
            self.x_h.remove()
        if self.y_v is not None:
            self.y_v.remove()
        if self.dt_v is not None:
            self.dt_v.remove()

        # x座標時系列グラフ
        self.x_time_ax.plot(plot_df["x"], plot_df["timestamp"], picker=5)
        self.x_time_ax.yaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        # tickをグラフの上・右に表示
        self.x_time_ax.set_xlabel("x(px)")
        self.x_time_ax.xaxis.tick_top()
        self.x_time_ax.xaxis.set_label_position("top")
        self.x_time_ax.yaxis.tick_right()
        time_max = plot_df["timestamp"].max()
        self.x_time_ax.set_ylim(0, time_max)
        self.x_time_ax.invert_yaxis()
        self.x_h = self.x_time_ax.axhline(0, color="gray", lw=0.5)

        # y座標時系列グラフ
        self.y_time_ax.plot(plot_df["timestamp"], plot_df["y"], picker=5)
        self.y_time_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.y_time_ax.set_ylabel("y(px)")
        self.y_v = self.y_time_ax.axvline(0, color="gray", lw=0.5)

        # 軌跡グラフ
        if plot_len > 10:
            sns.kdeplot(
                data=plot_df,
                x="x",
                y="y",
                fill=True,
                alpha=self.kde_alpha,
                bw_adjust=self.kde_adjust,
                thresh=self.kde_thresh,
                levels=self.kde_levels,
                ax=self.traj_ax,
            )
        else:
            print(plot_len)
        (self.traj_point,) = self.traj_ax.plot([], [], color="#02326f", marker=".")
        self.traj_img = self.traj_ax.imshow(np.full((height, width, 3), 255, dtype=np.uint8), aspect="auto")
        self.traj_img.autoscale()
        self.traj_ax.xaxis.set_visible(False)
        self.traj_ax.yaxis.set_visible(False)

        # speedグラフ
        nan_shift = int((dt_span - thinning) / 2) - 1
        label = f"{member}_{keypoint} (speed={dt_span}, thinning={thinning})"
        self.speed_ax.plot(plot_df["timestamp"], plot_df[f"spd_{dt_span}"].shift(-nan_shift), label=label, picker=5)
        self.speed_ax.xaxis.set_visible(False)
        self.speed_ax.set_ylabel("speed")
        self.speed_ax.legend(loc="upper right")
        self.dt_v = self.speed_ax.axvline(0, color="gray", lw=0.5)

        self.plot_df = plot_df
        self.canvas.draw_idle()

    def clear(self):
        self.x_time_ax.cla()
        self.y_time_ax.cla()
        self.traj_ax.cla()
        self.speed_ax.cla()
        self.canvas.draw_idle()

    def _format_timedelta(self, x, pos):
        return time_format.msec_to_timestr(x)

    def _gray_line(self, event):
        if event.inaxes is None or self.x_h is None or self.y_v is None or self.dt_v is None:
            return
        x = [event.xdata]
        y = [event.ydata]
        if event.inaxes == self.x_time_ax:
            self.x_h.set_ydata(y)
            self.y_v.set_xdata(y)
            self.dt_v.set_xdata(y)
        elif event.inaxes == self.y_time_ax:
            self.x_h.set_ydata(x)
            self.y_v.set_xdata(x)
            self.dt_v.set_xdata(x)
        elif event.inaxes == self.speed_ax:
            self.x_h.set_ydata(x)
            self.y_v.set_xdata(x)
            self.dt_v.set_xdata(x)
        self.x_time_ax.figure.canvas.draw_idle()
        self.y_time_ax.figure.canvas.draw_idle()
        self.traj_ax.figure.canvas.draw_idle()
        self.speed_ax.figure.canvas.draw_idle()

    def _click_graph(self, event):
        center_ind = event.ind[int(len(event.ind) / 2)]
        left_ind = center_ind - 4
        right_ind = center_ind + 5
        if left_ind < 0:
            left_ind = 0

        row = self.plot_df.iloc[left_ind:right_ind, :]
        if row.empty:
            return
        timestamp_msec = row.iloc[int(len(row) / 2)].timestamp
        self.traj_point.set_data(row.x, row.y)
        time_format.copy_to_clipboard(timestamp_msec)
        if self.vcap.isOpened() is True:
            ok, frame = self.vcap.read_at(timestamp_msec, rgb=True)
            self.traj_img.set_data(frame)
        self.traj_ax.figure.canvas.draw_idle()

    def close(self):
        plt.close(self.fig)
