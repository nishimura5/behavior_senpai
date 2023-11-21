import cv2
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


class RecurrencePlotter:
    def __init__(self, fig_size: tuple, dpi=72):
        self.dpi = dpi
        self.fig_size = fig_size
        self.fig = plt.figure(figsize=self.fig_size, dpi=self.dpi)
        self.fig.canvas.mpl_connect("button_press_event", self._click_graph)

        # axesのレイアウト設定
        gs = gridspec.GridSpec(1, 1)
        self.recu_ax = self.fig.add_subplot(gs[0, 0])
 
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

    def draw(self, plot_mat, timestamps):
        self.timestamps = timestamps
        self.recu_ax.imshow(plot_mat, cmap="gray")
        self.recu_ax.invert_yaxis()
        self.recu_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.recu_ax.yaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.canvas.draw_idle()
        print('draw')

    def clear(self):
        self.recu_ax.cla()
        self.canvas.draw_idle()
        print('clear')

    def _format_timedelta(self, x, pos):
        if int(x) >= len(self.timestamps):
            return ""
        x = self.timestamps[int(x)]
        return time_format.msec_to_timestr_with_fff(x)

    def _click_graph(self, event):
        x = event.xdata
        y = event.ydata
        if x is None or y is None:
            return
        timestamp_msec = self.timestamps[int(event.xdata)]

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
