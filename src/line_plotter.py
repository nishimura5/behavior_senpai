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


class LinePlotter:
    def __init__(self, fig_size: tuple, dpi=72):
        self.dpi = dpi
        self.fig_size = fig_size
        self.fig = plt.figure(figsize=self.fig_size, dpi=self.dpi)
        self.fig.canvas.mpl_connect("button_press_event", self._click_graph)

        # axesのレイアウト設定
        gs = gridspec.GridSpec(1, 1, top=0.97, bottom=0.05)
        self.line_ax = self.fig.add_subplot(gs[0, 0])

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

    def draw(self, plot_df, member: str, data_col_name: str, thinning: int):
        # multiindexが重複していたらdrop
        plot_df = plot_df.reset_index().drop_duplicates(subset=['frame', 'member'], keep='last').set_index(['frame', 'member'])
        plot_df = plot_df.loc[pd.IndexSlice[:, member], :]

        self.line_ax.plot(plot_df['timestamp'], plot_df[data_col_name])
        self.line_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))

        show_df = plot_df.reset_index().set_index(['timestamp', 'member']).loc[:, :]
        self.timestamps = show_df.index.get_level_values('timestamp').unique().to_numpy()
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
        if frame.shape[0] >= 1080:
            resize_height = 720
            resize_width = int(frame.shape[1] * resize_height / frame.shape[0])
            frame = cv2.resize(frame, (resize_width, resize_height))
        if ret is True:
            cv2.imshow("frame", frame)
            cv2.waitKey(1)

