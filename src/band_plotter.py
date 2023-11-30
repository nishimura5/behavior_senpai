import cv2
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import ticker, gridspec

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
except ImportError:
    # 環境によってはtkaggが使えないことがあるのでその対策
    USE_TKAGG = False
    # 代わりのバックエンドを指定
    matplotlib.use('Qt5Agg')
else:
    USE_TKAGG = True 

import time_format
import yolo_drawer
import mediapipe_drawer


# dataframeのprint時の行数指定
pd.set_option('display.max_rows', 1000)
pd.set_option('display.min_rows', 1000)


class BandPlotter:
    def __init__(self, fig_size: tuple, dpi=72):
        self.dpi = dpi
        self.fig_size = (fig_size[0], fig_size[1]*0.8)
        self.fig = plt.figure(figsize=self.fig_size, dpi=self.dpi)
        self.fig.canvas.mpl_connect("button_press_event", self._click_graph)

        # axesのレイアウト設定
        gs = gridspec.GridSpec(1, 1)
        self.band_ax = self.fig.add_subplot(gs[0, 0])

    def pack(self, master):
        if USE_TKAGG is True:
            self.canvas = FigureCanvasTkAgg(self.fig, master=master)
            toolbar = NavigationToolbar2Tk(self.canvas, master)
            toolbar.pack()
            self.canvas.get_tk_widget().pack(expand=False)
        else:
            # TKAggが使えない場合はplt.show()を使う
            self.canvas = self.fig.canvas
            plt.show(block=False)

    def set_vcap(self, vcap):
        self.vcap = vcap

    def draw(self, plot_df, member: str, time_min_msec: int, time_max_msec: int):
        if plot_df.attrs['model'] == "YOLOv8 x-pose-p6":
            self.anno = yolo_drawer.Annotate()
        elif plot_df.attrs['model'] == "MediaPipe Holistic":
            self.anno = mediapipe_drawer.Annotate()
        self.member = member

        self.anno_df = plot_df.reset_index().set_index(['timestamp', 'member', 'keypoint']).loc[:, ['x', 'y', 'conf']]
        self.timestamps = self.anno_df.index.get_level_values('timestamp').unique().to_numpy()

        plot_df = plot_df.dropna()
        keypoints = plot_df.index.get_level_values('keypoint').unique()
        chk_df = plot_df.reset_index().set_index(['member', 'keypoint']).sort_index()
        for keypoint in keypoints:
            # memberとkeypointのindexの組み合わせがない場合はスキップ
            if (self.member, keypoint) not in chk_df.index:
                print(f'{self.member}_{keypoint} not found')
                continue

            dst_df = plot_df.loc[pd.IndexSlice[:, self.member, keypoint], :]
            dst_df = dst_df.reset_index().set_index('frame')
            dst_df = dst_df.loc[:, ['keypoint', 'timestamp']].astype({'keypoint': str})
            self.band_ax.plot(dst_df['timestamp'], dst_df['keypoint'], label=f'{self.member}_{keypoint}', marker='|', linestyle='', picker=5)

        self.band_ax.set_xlim(time_min_msec, time_max_msec)
        self.band_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.canvas.draw_idle()

    def clear(self):
        self.band_ax.cla()
        self.canvas.draw_idle()

    def _format_timedelta(self, x, pos):
        return time_format.msec_to_timestr(x)

    def _click_graph(self, event):
        x = event.xdata
        timestamp_msec = float(x)

        # DataFrameにあるself.timestampsからクリックで得たtimestamp_msecに最も近い値を抽出
        timestamp_msec = self.timestamps[np.fabs(self.timestamps-timestamp_msec).argsort()[:1]][0]
        tar_df = self.anno_df.loc[pd.IndexSlice[timestamp_msec, self.member, :], :]

        time_format.copy_to_clipboard(timestamp_msec)
        if self.vcap.isOpened() is False:
            return

        ret, frame = self.vcap.read_at(timestamp_msec)
        self.anno.set_img(frame)
        kps = tar_df.to_numpy()
        self.anno.set_pose(kps)
        self.anno.set_track(self.member)
        dst_img = self.anno.draw_idle()

        if frame.shape[0] >= 1080:
            resize_height = 720
            resize_width = int(frame.shape[1] * resize_height / frame.shape[0])
            dst_img = cv2.resize(dst_img, (resize_width, resize_height))
        if ret is True:
            cv2.imshow("frame", dst_img)
            cv2.waitKey(1)
