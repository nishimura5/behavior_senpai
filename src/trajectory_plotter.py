import os

import pandas as pd
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker, gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import seaborn as sns


class TrajectoryPlotter:
    def __init__(self):
        dpi = 72
        fig_width = 900
        fig_height = 700
        self.fig = plt.figure(figsize=(fig_width/dpi, fig_height/dpi), dpi=dpi)
        self.fig.canvas.mpl_connect("motion_notify_event", self._gray_line)
        self.fig.canvas.mpl_connect("pick_event", self._click_graph)

        # axesのレイアウト設定
        gs = gridspec.GridSpec(2, 2, width_ratios=[fig_height, fig_width], height_ratios=[1, 1], hspace=0.04, wspace=0.03)
        self.traj_ax = self.fig.add_subplot(gs[1, 1])
        self.x_time_ax = self.fig.add_subplot(gs[0, 1], sharex=self.traj_ax)
        self.y_time_ax = self.fig.add_subplot(gs[1, 0], sharey=self.traj_ax)
        self.x_h = None
        self.y_v = None

    def pack(self, master):
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        toolbar = NavigationToolbar2Tk(self.canvas, master)
        toolbar.pack()
        self.canvas.get_tk_widget().pack(expand=False)

    def draw(self, plot_df, member, keypoint, pkl_dir):
        video_path = os.path.join(pkl_dir, os.pardir, plot_df.attrs["video_name"])
        if os.path.exists(video_path) is True:
            cap = cv2.VideoCapture(
                video_path,
                apiPreference=cv2.CAP_ANY,
                params=[cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY])
        else:
            cap = None
        self.cap = cap

        self.plot_df = plot_df.loc[pd.IndexSlice[:, member, keypoint], :]
        width, height = plot_df.attrs["frame_size"]
        self.traj_ax.cla()
        self.x_time_ax.cla()
        self.y_time_ax.cla()

        # x座標時系列グラフ
        self.x_time_ax.plot(self.plot_df['x'], self.plot_df['timestamp'], picker=5)
        self.x_time_ax.yaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        # tickをグラフの上部に表示
        self.x_time_ax.set_xlabel('x(px)')
        self.x_time_ax.xaxis.tick_top()
        self.x_time_ax.xaxis.set_label_position('top')
        self.x_time_ax.invert_yaxis()
        self.x_h = self.x_time_ax.axhline(0, color='gray', lw=0.5)
        # y座標時系列グラフ
        self.y_time_ax.plot(self.plot_df['timestamp'], self.plot_df['y'], picker=5)
        self.y_time_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.y_time_ax.set_ylabel('y(px)')
        self.y_v = self.y_time_ax.axvline(0, color='gray', lw=0.5)
        # 軌跡グラフ
        sns.kdeplot(data=self.plot_df, x="x", y="y", fill=True, alpha=0.7, ax=self.traj_ax)
        self.traj_point, = self.traj_ax.plot([], [], color="#02326f", marker='.')
        self.traj_img = self.traj_ax.imshow(np.full((height, width, 3), 255, dtype=np.uint8), aspect='auto')
        self.traj_img.autoscale()
        self.traj_ax.set_ylim(0, height)
        self.traj_ax.invert_yaxis()
        self.traj_ax.xaxis.set_visible(False)
        self.traj_ax.yaxis.set_visible(False)

        self.canvas.draw()

    def _format_timedelta(self, x, pos):
        sec = x / 1000
        hours = sec // 3600
        remain = sec - (hours*3600)
        minutes = remain // 60
        seconds = remain - (minutes * 60)
        return f'{int(hours)}:{int(minutes):02}:{int(seconds):02}'

    def _gray_line(self, event):
        if event.inaxes is None or self.x_h is None or self.y_v is None:
            return
        x = event.xdata
        y = event.ydata
        if event.inaxes == self.x_time_ax:
            self.x_h.set_ydata(y)
            self.y_v.set_xdata(y)
        elif event.inaxes == self.y_time_ax:
            self.x_h.set_ydata(x)
            self.y_v.set_xdata(x)
        self.canvas.draw()

    def _click_graph(self, event):
        center_ind = event.ind[int(len(event.ind)/2)]
        left_ind = center_ind - 4
        right_ind = center_ind + 5
        if left_ind < 0:
            left_ind = 0

        row = self.plot_df.iloc[left_ind:right_ind, :]
        timestamp = row.iloc[int(len(row)/2)].timestamp
        self.traj_point.set_data(row.x, row.y)

        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_MSEC, timestamp)
            ok, frame = self.cap.read()
            show_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.traj_img.set_data(show_img)
        self.canvas.draw()
