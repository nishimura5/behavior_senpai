import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import gridspec, ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from python_senpai import time_format


class DimensionalReductionPlotter:
    def __init__(self, fig_size: tuple, dpi=72):
        self.dpi = dpi
        self.fig_size = fig_size
        self.fig = plt.figure(figsize=self.fig_size, dpi=self.dpi)
        self.fig.canvas.mpl_connect("pick_event", self._click_plot)
        self.fig.canvas.mpl_connect("button_press_event", self._click_graph)

        # axesのレイアウト設定
        gs = gridspec.GridSpec(2, 1, height_ratios=(4, 1), top=0.97, bottom=0.05)
        self.cluster_ax = self.fig.add_subplot(gs[0, 0])
        self.line_ax = self.fig.add_subplot(gs[1, 0])

        self.class_data = None

    def pack(self, master):
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        toolbar = NavigationToolbar2Tk(self.canvas, master)
        toolbar.pack()
        self.canvas.get_tk_widget().pack(expand=False)

    def set_vcap(self, vcap):
        self.vcap = vcap

    def draw(self, plot_mat, timestamps, frames):
        self.frames = frames
        self.cluster_ax.cla()
        self.line_ax.cla()

        if self.class_data is None or len(self.class_data) != len(timestamps):
            self.class_data = np.zeros(len(timestamps))

        self.timestamps = timestamps
        self.plot_mat = plot_mat
        self.picker_range = 5
        scatter_plot = self.cluster_ax.scatter(self.plot_mat[:, 0], self.plot_mat[:, 1], c=self.class_data, picker=self.picker_range, cmap="tab10")
        legend = self.cluster_ax.legend(*scatter_plot.legend_elements(), title="cluster")
        self.cluster_ax.add_artist(legend)

        # 0: unclustered
        self.cluster_number = 0
        (self.line_plot,) = self.line_ax.plot(timestamps, self.class_data)
        self.line_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.line_ax.set_ylim(0, 10)
        self.vline = self.line_ax.axvline(x=0, color="gray", linewidth=0.5)

        self.canvas.draw_idle()

    def clear(self):
        self.clear_class_data()
        self.cluster_ax.cla()
        self.line_ax.cla()
        self.canvas.draw_idle()

    def clear_class_data(self):
        self.class_data = None

    def set_cluster_number(self, cluster_number):
        self.cluster_number = cluster_number

    def set_picker_range(self, picker_range):
        self.picker_range = picker_range
        self.cluster_ax.cla()
        scatter_plot = self.cluster_ax.scatter(self.plot_mat[:, 0], self.plot_mat[:, 1], c=self.class_data, picker=self.picker_range, cmap="tab10")
        legend = self.cluster_ax.legend(*scatter_plot.legend_elements(), title="cluster")
        self.cluster_ax.add_artist(legend)

    def get_cluster_df(self, names):
        classes = np.unique(self.class_data)
        ret_dict = {
            "frame": self.frames,
            "timestamp": self.timestamps,
        }
        for c in classes:
            mask = self.class_data == c
            ret_dict[names[int(c)]] = mask

        ret_df = pd.DataFrame(ret_dict)
        return ret_df

    def _format_timedelta(self, x, pos):
        return time_format.msec_to_timestr(x)

    def _click_plot(self, event):
        # right click
        if event.mouseevent.button == 3:
            for ind in event.ind:
                self.class_data[ind] = self.cluster_number
            self.cluster_ax.cla()
            scatter_plot = self.cluster_ax.scatter(
                self.plot_mat[:, 0], self.plot_mat[:, 1], c=self.class_data, picker=self.picker_range, cmap="tab10"
            )
            legend = self.cluster_ax.legend(*scatter_plot.legend_elements(), title="cluster")
            self.cluster_ax.add_artist(legend)

            self.line_plot.set_data(self.timestamps, self.class_data)

        center_ind = event.ind[0]
        timestamp_msec = self.timestamps[center_ind]
        self.vline.set_xdata([timestamp_msec])
        self.canvas.draw_idle()

        time_format.copy_to_clipboard(timestamp_msec)
        if self.vcap.isOpened() is False:
            return

        ret, frame = self.vcap.read_at(timestamp_msec)
        if frame.shape[0] >= 1080:
            resize_height = 720
            resize_width = int(frame.shape[1] * resize_height / frame.shape[0])
            frame = cv2.resize(frame, (resize_width, resize_height))
        if ret is True:
            cv2.imshow("frame", frame)
            cv2.waitKey(1)

    def _click_graph(self, event):
        x = event.xdata
        y = event.ydata
        tar_ax = event.inaxes
        if x is None or y is None or tar_ax == self.cluster_ax:
            return

        if event.button == 1:
            self.cluster_ax.cla()
            timestamp_msec = float(x)
            idx = np.abs(self.timestamps - timestamp_msec).argmin()
            size = np.ones(len(self.timestamps)) * 5
            size[idx] = 40
            scatter_plot = self.cluster_ax.scatter(
                self.plot_mat[:, 0], self.plot_mat[:, 1], c=self.class_data, s=size, picker=self.picker_range, cmap="tab10"
            )
            legend = self.cluster_ax.legend(*scatter_plot.legend_elements(), title="cluster")
            self.cluster_ax.add_artist(legend)
        elif event.button == 3:
            timestamp_msec = self.vcap.get(cv2.CAP_PROP_POS_MSEC)
            timestamp_msec += 100

        self.vline.set_xdata([timestamp_msec])
        self.canvas.draw_idle()

        if tar_ax == self.line_ax:
            time_format.copy_to_clipboard(timestamp_msec)
            if self.vcap.isOpened() is False:
                return

            ret, frame = self.vcap.read_at(timestamp_msec)
            if frame.shape[0] >= 1080:
                resize_height = 720
                resize_width = int(frame.shape[1] * resize_height / frame.shape[0])
                frame = cv2.resize(frame, (resize_width, resize_height))
            if ret is True:
                cv2.imshow("frame", frame)
                cv2.waitKey(1)
