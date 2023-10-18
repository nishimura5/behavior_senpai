import tkinter as tk

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import seaborn as sns


class KeypointPlotter:
    def __init__(self):
        dpi = 100
#        self.fig, self.ax = plt.subplots(figsize=(1280/dpi, 600/dpi), dpi=dpi)
        self.fig = plt.figure(figsize=(700/dpi, 700/dpi), dpi=dpi)
        self.plot_styles = ["line-x", "line-y", "trajectory"]

    def pack(self, master):
#        fig.canvas.mpl_connect("button_press_event", self.click_graph)
#        fig.canvas.mpl_connect("scroll_event", self.scroll_graph)
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.mpl_connect("motion_notify_event", self._cross_line)

        toolbar = NavigationToolbar2Tk(self.canvas, master)
        toolbar.pack()
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.X, expand=False)

    def draw(self, plot_df, member, keypoint, plot_style):
        self.fig.clf()
        traj_ax = self.fig.add_subplot(224)
        x_time_ax = self.fig.add_subplot(222, sharex=traj_ax)
        y_time_ax = self.fig.add_subplot(223, sharey=traj_ax)

        width = plot_df.attrs["width"]
        height = plot_df.attrs["heigt"]
        plot_df = plot_df.loc[pd.IndexSlice[:, member, keypoint], :]

        if plot_style == 'line-x':
            x_time_ax.plot(plot_df['x'], plot_df['timestamp'])
            x_time_ax.set_xlim(0, width)
            x_time_ax.invert_yaxis()
            x_time_ax.yaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        elif plot_style == 'line-y':
            y_time_ax.plot(plot_df['timestamp'], plot_df['y'])
            y_time_ax.set_ylim(0, height)
            y_time_ax.invert_yaxis()
            y_time_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        elif plot_style == 'trajectory':
            x_time_ax.plot(plot_df['x'], plot_df['timestamp'])
            x_time_ax.yaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
            self.x_v = x_time_ax.axvline(0, color='black', lw=0.5)
            x_time_ax.invert_yaxis()

            y_time_ax.plot(plot_df['timestamp'], plot_df['y'])
            y_time_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
            self.y_h = y_time_ax.axhline(0, color='black', lw=0.5)

            sns.kdeplot(data=plot_df, x="x", y="y", fill=True, ax=traj_ax)
            sns.scatterplot(data=plot_df, x="x", y="y", s=10, ax=traj_ax)
            self.traj_v = traj_ax.axvline(0, color='black', lw=0.5)
            self.traj_h = traj_ax.axhline(0, color='black', lw=0.5)
            traj_ax.set_xlim(0, width)
            traj_ax.set_ylim(0, height)
            traj_ax.invert_yaxis()


        self.canvas.draw()

    def _format_timedelta(self, x, pos):
        hours = x // 3600
        remain = x - (hours*3600)
        minutes = remain // 60
        seconds = remain - (minutes * 60)
        return f'{int(hours)}:{int(minutes):02}:{int(seconds):02}'

    def _cross_line(self, event):
        if event.inaxes is None:
            return
        x = event.xdata
        y = event.ydata
        self.traj_v.set_xdata(x)
        self.traj_h.set_ydata(y)
        self.x_v.set_xdata(x)
        self.y_h.set_ydata(y)
        self.canvas.draw()