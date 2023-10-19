import tkinter as tk

import pandas as pd
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker, gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import seaborn as sns


class KeypointPlotter:
    def __init__(self):
        dpi = 100
        self.fig_width = 900
        self.fig_height = 700
        self.fig = plt.figure(figsize=(self.fig_width/dpi, self.fig_height/dpi), dpi=dpi)

    def pack(self, master):
#        fig.canvas.mpl_connect("scroll_event", self.scroll_graph)
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.mpl_connect("motion_notify_event", self._cross_line)
        self.canvas.mpl_connect("pick_event", self._click_graph)

        toolbar = NavigationToolbar2Tk(self.canvas, master)
        toolbar.pack()
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.X, expand=False)

    def draw(self, plot_df, member, keypoint, cap):
        self.cap = cap
        self.fig.clf()
        gs = gridspec.GridSpec(2, 2, width_ratios=[self.fig_height, self.fig_width], height_ratios=[1, 1])
        traj_ax = self.fig.add_subplot(gs[1, 1])
        self.x_time_ax = self.fig.add_subplot(gs[0, 1], sharex=traj_ax)
        self.y_time_ax = self.fig.add_subplot(gs[1, 0], sharey=traj_ax)

        width = plot_df.attrs["width"]
        height = plot_df.attrs["heigt"]
        self.plot_df = plot_df.loc[pd.IndexSlice[:, member, keypoint], :]

        self.x_time_ax.plot(self.plot_df['x'], self.plot_df['timestamp'], picker=5)
        self.x_time_ax.yaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.x_h = self.x_time_ax.axhline(0, color='gray', lw=0.5)
        self.x_time_ax.invert_yaxis()

        self.y_time_ax.plot(self.plot_df['timestamp'], self.plot_df['y'], picker=5)
        self.y_time_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.y_v = self.y_time_ax.axvline(0, color='gray', lw=0.5)

        sns.kdeplot(data=self.plot_df, x="x", y="y", fill=True, alpha=0.7, ax=traj_ax)
        self.traj_point, = traj_ax.plot(self.plot_df['x'], self.plot_df['y'], color="#02326f", marker='.')
        self.traj_img = traj_ax.imshow(np.full((height, width, 3), 255, dtype=np.uint8), aspect='auto')
        self.traj_img.autoscale()
        traj_ax.set_xlim(0, width)
        traj_ax.set_ylim(0, height)
        traj_ax.invert_yaxis()

        self.canvas.draw()

    def _format_timedelta(self, x, pos):
        sec = x / 1000
        hours = sec // 3600
        remain = sec - (hours*3600)
        minutes = remain // 60
        seconds = remain - (minutes * 60)
        return f'{int(hours)}:{int(minutes):02}:{int(seconds):02}'

    def _cross_line(self, event):
        if event.inaxes is None:
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
