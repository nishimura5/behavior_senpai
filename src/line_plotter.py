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

from python_senpai import time_format


class LinePlotter:
    def __init__(self, fig_size: tuple, dpi=72):
        self.dpi = dpi
        self.fig_size = fig_size
        self.fig = plt.figure(figsize=self.fig_size, dpi=self.dpi)
        self.fig.canvas.mpl_connect("button_press_event", self._click_graph)

        # axesのレイアウト設定
        gs = gridspec.GridSpec(1, 1, top=0.97, bottom=0.05)
        self.line_ax = self.fig.add_subplot(gs[0, 0])

        # グラフクリック時にアノテーションを描画するかのフラグ
        self.draw_anno = False

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

    def set_trk_df(self, trk_df):
        self.draw_anno = True
        import yolo_drawer
        import mediapipe_drawer

        if trk_df.attrs['model'] == "YOLOv8 x-pose-p6":
            self.anno = yolo_drawer.Annotate()
            cols_for_anno = ['x', 'y', 'conf']
        elif trk_df.attrs['model'] == "MediaPipe Holistic":
            self.anno = mediapipe_drawer.Annotate()
            cols_for_anno = ['x', 'y', 'z']
        self.anno_df = trk_df.reset_index().set_index(['timestamp', 'member', 'keypoint']).loc[:, cols_for_anno]

    def set_plot(self, plot_df, member: str, data_col_names: list, thinning: int):
        self.member = member
        # multiindexが重複していたらdrop
        plot_df = plot_df.reset_index().drop_duplicates(subset=['frame', 'member'], keep='last').set_index(['frame', 'member'])
        plot_df = plot_df.loc[pd.IndexSlice[:, member], :]

        for col_name in data_col_names:
            self.line_ax.plot(plot_df['timestamp'], plot_df[col_name], label=col_name)
        self.line_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.line_ax.legend(loc='upper right')

        show_df = plot_df.reset_index().set_index(['timestamp', 'member']).loc[:, :]
        self.timestamps = show_df.index.get_level_values('timestamp').unique().to_numpy()

    def set_plot_band(self, plot_df, member: str, time_min_msec: int, time_max_msec: int):
        self.member = member

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
            self.line_ax.plot(dst_df['timestamp'], dst_df['keypoint'], label=f'{self.member}_{keypoint}', marker='|', linestyle='', picker=5)

        self.line_ax.set_xlim(time_min_msec, time_max_msec)
        self.line_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.line_ax.xaxis.set_major_locator(ticker.MultipleLocator(5*60*1000))
        self.line_ax.grid(which='major', axis='x', linewidth=0.3)

        show_df = plot_df.reset_index().set_index(['timestamp', 'member']).loc[:, :]
        self.timestamps = show_df.index.get_level_values('timestamp').unique().to_numpy()

    def draw(self):
        self.canvas.draw_idle()

    def clear(self):
        self.line_ax.cla()
        self.canvas.draw_idle()

    def _format_timedelta(self, x, pos):
        return time_format.msec_to_timestr(x)

    def _click_graph(self, event):
        x = event.xdata
        timestamp_msec = float(x)

        # DataFrameにあるself.timestampsからクリックで得たtimestamp_msecに最も近い値を抽出
        timestamp_msec = self.timestamps[np.fabs(self.timestamps-timestamp_msec).argsort()[:1]][0]

        time_format.copy_to_clipboard(timestamp_msec)
        if self.vcap.isOpened() is False:
            return

        ret, frame = self.vcap.read_at(timestamp_msec)

        if self.draw_anno is True:
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
