import cv2
import matplotlib
import matplotlib.pyplot as plt
import mediapipe_drawer
import numpy as np
import pandas as pd
import rtmpose_drawer
import yolo_drawer
from matplotlib import gridspec, ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from python_senpai import time_format


class LinePlotter:
    def __init__(self, fig_size: tuple, dpi=72, bottom=0.05):
        self.dpi = dpi
        self.fig_size = fig_size
        self.fig = plt.figure(figsize=self.fig_size, dpi=self.dpi)
        self.fig.canvas.mpl_connect("button_press_event", self._click_graph)

        # axesのレイアウト設定
        gs = gridspec.GridSpec(1, 1, top=0.97, bottom=bottom)
        self.line_ax = self.fig.add_subplot(gs[0, 0])

        # グラフクリック時にアノテーションを描画するかのフラグ
        self.draw_anno = False

    def pack(self, master):
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        toolbar = NavigationToolbar2Tk(self.canvas, master)
        toolbar.pack()
        self.canvas.get_tk_widget().pack(expand=False)

    def set_vcap(self, vcap):
        """
        VideoCapかMultiVcapが入ってくる
        """
        self.vcap = vcap

    def set_trk_df(self, trk_df):
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
        # sortによってkeypointの順番が変わる

    #        self.anno_df = self.anno_df.sort_index(level=['timestamp', 'member'])

    def set_plot(self, plot_df, member: str, data_col_names: list):
        self.member = member
        # 重複インデックス削除
        plot_df = plot_df[~plot_df.index.duplicated(keep="last")]
        plot_df = plot_df.loc[pd.IndexSlice[:, member], :]

        plot_df.plot(ax=self.line_ax, x="timestamp", y=data_col_names)
        self.line_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.line_ax.legend(loc="upper right")

        show_df = plot_df.reset_index().set_index(["timestamp", "member"]).loc[:, :]
        self.timestamps = show_df.index.get_level_values("timestamp").unique().to_numpy()
        print(show_df)

    def set_plot_band(self, plot_df, member: str, time_min_msec: int, time_max_msec: int):
        self.member = member

        plot_df = plot_df.dropna()
        keypoints = plot_df.index.get_level_values("keypoint").unique()
        chk_df = plot_df.reset_index().set_index(["member", "keypoint"]).sort_index()
        for keypoint in keypoints:
            # memberとkeypointのindexの組み合わせがない場合はスキップ
            if (self.member, keypoint) not in chk_df.index:
                print(f"{self.member}_{keypoint} not found")
                continue

            dst_df = plot_df.loc[pd.IndexSlice[:, self.member, keypoint], :]
            dst_df = dst_df.reset_index().set_index("frame")
            dst_df = dst_df.loc[:, ["keypoint", "timestamp"]].astype({"keypoint": str})
            self.line_ax.plot(dst_df["timestamp"], dst_df["keypoint"], label=f"{self.member}_{keypoint}", marker="|", linestyle="", picker=5)

        self.line_ax.set_xlim(time_min_msec, time_max_msec)
        self.line_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.line_ax.xaxis.set_major_locator(ticker.MultipleLocator(5 * 60 * 1000))
        self.line_ax.grid(which="major", axis="x", linewidth=0.3)

        show_df = plot_df.reset_index().set_index(["timestamp", "member"]).loc[:, :]
        self.timestamps = show_df.index.get_level_values("timestamp").unique().to_numpy()

    def set_plot_rect(self, plot_df, member: str, rects: list, time_min_msec: int, time_max_msec: int):
        self.member = member

        # カラムごとにdtypeを指定してDataFrameを作成
        rect_df = pd.DataFrame(rects, columns=["start", "end", "description"], dtype="str")
        rect_df = rect_df.sort_values("description")

        rect_df["start"] = pd.to_timedelta(rect_df["start"]).dt.total_seconds() * 1000
        rect_df["end"] = pd.to_timedelta(rect_df["end"]).dt.total_seconds() * 1000
        descriptions = rect_df["description"].unique()
        ticks = []
        for i, description in enumerate(descriptions):
            # descriptionでフィルタリング
            tar_df = rect_df.loc[rect_df["description"] == description, :]
            rectangles = []
            for _, row in tar_df.iterrows():
                rectangles.append(matplotlib.patches.Rectangle((row["start"], i), row["end"] - row["start"], 0.9, alpha=0.7, label=description))
            for rectangle in rectangles:
                self.line_ax.add_patch(rectangle)
            ticks.append(i + 0.45)
        self.line_ax.set_ylim(0, len(descriptions))
        self.line_ax.set_yticks(ticks)
        self.line_ax.set_yticklabels(descriptions)
        self.line_ax.set_xlim(time_min_msec, time_max_msec)
        self.line_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.line_ax.xaxis.set_major_locator(ticker.MultipleLocator(5 * 60 * 1000))
        self.line_ax.grid(which="major", axis="x", linewidth=0.3)

        show_df = plot_df.reset_index().set_index(["timestamp", "member"]).loc[:, :]
        self.timestamps = show_df.index.get_level_values("timestamp").unique().to_numpy()

    def draw(self):
        self.vline = self.line_ax.axvline(x=0, color="gray", linewidth=0.5)
        self.canvas.draw_idle()

    def clear(self):
        self.line_ax.cla()
        self.canvas.draw_idle()

    def _format_timedelta(self, x, pos):
        return time_format.msec_to_timestr(x)

    def _click_graph(self, event):
        if event.button == 1:
            x = event.xdata
            if x is None:
                return
            timestamp_msec = float(x)

        elif event.button == 3:
            timestamp_msec = self.vcap.get(cv2.CAP_PROP_POS_MSEC)
            timestamp_msec += 100

        # DataFrameにあるself.timestampsからクリックで得たtimestamp_msecに最も近い値を抽出
        timestamp_msec = self.timestamps[np.fabs(self.timestamps - timestamp_msec).argsort()[:1]][0]

        self.vline.set_xdata([timestamp_msec])
        self.line_ax.figure.canvas.draw_idle()

        time_format.copy_to_clipboard(timestamp_msec)
        ret, frame = self.vcap.read_at(timestamp_msec)
        if ret is False:
            return

        if self.draw_anno is True:
            if (timestamp_msec, self.member) not in self.anno_df.index:
                return
            tar_df = self.anno_df.loc[pd.IndexSlice[timestamp_msec, self.member, :], :]
            kps = tar_df.to_numpy()
            self.anno.set_img(frame)
            self.anno.set_pose(kps)
            self.anno.set_track(self.member)
            frame = self.anno.draw()

        if frame.shape[0] >= 1080:
            resize_height = 720
            resize_width = int(frame.shape[1] * resize_height / frame.shape[0])
            frame = cv2.resize(frame, (resize_width, resize_height))
        if ret is True:
            cv2.imshow("frame", frame)
            cv2.waitKey(1)
