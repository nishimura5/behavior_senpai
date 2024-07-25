import time

import cv2
import matplotlib.pyplot as plt
import mediapipe_drawer
import numpy as np
import pandas as pd
import rtmpose_drawer
import yolo_drawer
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

        self.draw_anno = False
        self.class_names = None
        self.picker_range = None
        self.plot_df = None

    def pack(self, master):
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        toolbar = NavigationToolbar2Tk(self.canvas, master)
        toolbar.pack()
        self.canvas.get_tk_widget().pack(expand=False)

    def set_vcap(self, vcap):
        self.vcap = vcap

    def set_trk_df(self, trk_df):
        start_time = time.perf_counter()
        self.draw_anno = True
        if trk_df.attrs["model"] == "YOLOv8 x-pose-p6":
            self.anno = yolo_drawer.Annotate()
            cols_for_anno = ["x", "y", "conf"]
        elif trk_df.attrs["model"] == "MediaPipe Holistic":
            self.anno = mediapipe_drawer.Annotate()
            cols_for_anno = ["x", "y", "z"]
        elif trk_df.attrs["model"] == "MMPose RTMPose-x":
            self.anno = rtmpose_drawer.Annotate()
            cols_for_anno = ["x", "y", "score"]
        self.anno_df = trk_df.reset_index().set_index(["timestamp", "member", "keypoint"]).loc[:, cols_for_anno]
        self.anno_time_member_indexes = self.anno_df.index.droplevel(2).unique()
        print(f"set_trk_df() (dimredu_plotter.DimensionalReductionPlotter): {time.perf_counter() - start_time:.3f}sec")

    def set_init_class_names(self, class_names):
        self.init_class_names = class_names
        self.class_names = class_names

    def set_member(self, member):
        self.member = member

    def draw(self, plot_df, class_sr):
        self.plot_df = plot_df
        if class_sr is not None:
            self.plot_df["class"] = class_sr
        else:
            self.plot_df["class"] = 0
        self.plot_df.loc[self.plot_df["umap_t"].isna(), "class"] = np.nan
        self.timestamps = self.plot_df["timestamp"].to_numpy()

        self.line_ax.cla()

        if self.picker_range is None:
            self.picker_range = 10

        self.cluster_number = 0
        (self.line_plot,) = self.line_ax.plot(self.timestamps, self.plot_df["class"])
        self._update_scatter()
        self.line_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.line_ax.set_ylim(0, 10)
        self.line_ax.yaxis.grid(True)
        self.vline = self.line_ax.axvline(x=0, color="gray", linewidth=0.5)

        self.canvas.draw_idle()

    def clear(self):
        self.clear_class_data()
        self.cluster_ax.cla()
        self.line_ax.cla()
        self.canvas.draw_idle()

    def clear_class_data(self):
        self.class_names = self.init_class_names

    def set_cluster_names(self, class_names):
        self.class_names = class_names

    def set_cluster_number(self, cluster_number):
        self.cluster_number = cluster_number

    def set_picker_range(self, picker_range):
        self.picker_range = picker_range
        self._update_scatter(hold_lim=True)

        self.canvas.draw_idle()

    def get_cluster_df(self):
        return self.plot_df.loc[:, ["class", "timestamp"]]

    def _update_scatter(self, size=None, hold_lim=False):
        if hold_lim is True:
            xlim = self.cluster_ax.get_xlim()
            ylim = self.cluster_ax.get_ylim()
            self.cluster_ax.cla()
            self.cluster_ax.set_xlim(xlim)
            self.cluster_ax.set_ylim(ylim)
        else:
            self.cluster_ax.cla()
        if size is None:
            size = np.ones(len(self.timestamps)) * 5

        class_codes = self.plot_df["class"].unique()
        class_codes = np.sort(class_codes[~np.isnan(class_codes)])
        classes = [self.class_names[int(c)] for c in class_codes]

        scatter_plot = self.cluster_ax.scatter(
            self.plot_df["umap_0"], self.plot_df["umap_1"], c=self.plot_df["class"], picker=self.picker_range, cmap="tab10", s=size, vmin=0, vmax=10
        )
        handles = [
            plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=scatter_plot.cmap(scatter_plot.norm(c)), markersize=10) for c in class_codes
        ]
        legend = self.cluster_ax.legend(handles=handles, labels=classes, loc="upper right", title="Cluster")
        self.cluster_ax.add_artist(legend)

    def _format_timedelta(self, x, pos):
        return time_format.msec_to_timestr(x)

    def _click_plot(self, event):
        # right click
        if event.mouseevent.button == 3:
            self.plot_df.loc[self.plot_df.index[event.ind], "class"] = self.cluster_number
            self.line_plot.set_data(self.timestamps, self.plot_df["class"])
        self._update_scatter(hold_lim=True)

        # search the nearest point
        near_df = self.plot_df.loc[self.plot_df.index[event.ind], :]
        distances = np.sqrt((near_df["umap_0"] - event.mouseevent.xdata) ** 2 + (near_df["umap_1"] - event.mouseevent.ydata) ** 2)
        timestamp_msec = near_df.iloc[np.argmin(distances)]["timestamp"]

        self.vline.set_xdata([timestamp_msec])
        self.canvas.draw_idle()

        time_format.copy_to_clipboard(timestamp_msec)
        self._show(timestamp_msec)

    def _click_graph(self, event):
        x = event.xdata
        y = event.ydata
        tar_ax = event.inaxes
        if x is None or y is None or tar_ax == self.cluster_ax:
            return

        timestamp_msec = float(x)
        idx = np.fabs(self.timestamps - timestamp_msec).argmin()
        timestamp_msec = self.timestamps[idx]
        isnan = np.isnan(self.plot_df.loc[self.plot_df.index[idx], "umap_t"])
        if event.button == 3 and ~isnan:
            self.plot_df.loc[self.plot_df.index[idx], "class"] = self.cluster_number
            self.line_plot.set_data(self.timestamps, self.plot_df["class"])
        size = np.ones(len(self.timestamps)) * 5
        size[idx] = 60
        self._update_scatter(size)

        self.vline.set_xdata([timestamp_msec])
        self.canvas.draw_idle()

        if tar_ax == self.line_ax:
            time_format.copy_to_clipboard(timestamp_msec)
            self._show(timestamp_msec)

    def _show(self, timestamp_msec):
        if self.vcap.isOpened() is False:
            return
        ret, frame = self.vcap.read_at(timestamp_msec)
        if ret is False:
            return

        if self.draw_anno is True:
            if (timestamp_msec, self.member) in self.anno_time_member_indexes:
                tar_df = self.anno_df.loc[pd.IndexSlice[timestamp_msec, self.member, :], :]
                kps = tar_df.to_numpy()
                self.anno.set_img(frame)
                self.anno.set_pose(kps)
                self.anno.set_track(self.member)
                frame = self.anno.draw()

        if frame.shape[0] >= 1080:
            resize_height = 800
            resize_width = int(frame.shape[1] * resize_height / frame.shape[0])
            frame = cv2.resize(frame, (resize_width, resize_height))
        if ret is True:
            cv2.imshow("frame", frame)
            cv2.waitKey(1)

    def close(self):
        plt.close(self.fig)
