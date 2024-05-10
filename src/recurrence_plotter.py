import cv2
import matplotlib.pyplot as plt
from matplotlib import ticker, gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from python_senpai import time_format


class RecurrencePlotter:
    def __init__(self, fig_size: tuple, dpi=72):
        self.dpi = dpi
        self.fig_size = fig_size
        self.fig = plt.figure(figsize=self.fig_size, dpi=self.dpi)
        self.fig.canvas.mpl_connect("button_press_event", self._click_graph)
        self.fig.canvas.mpl_connect("motion_notify_event", self._horizontal_line)

        # axesのレイアウト設定
        gs = gridspec.GridSpec(2, 1, height_ratios=(4, 1), top=0.97, bottom=0.05)
        self.recu_ax = self.fig.add_subplot(gs[0, 0])
        self.line_ax = self.fig.add_subplot(gs[1, 0], sharex=self.recu_ax)

    def pack(self, master):
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        toolbar = NavigationToolbar2Tk(self.canvas, master)
        toolbar.pack()
        self.canvas.get_tk_widget().pack(expand=False)

    def set_vcap(self, vcap):
        self.vcap = vcap

    def draw(self, plot_mat, timestamps):
        self.recu_ax.cla()
        self.line_ax.cla()

        self.timestamps = timestamps
        self.plot_mat = plot_mat
        self.recu_ax.imshow(plot_mat, cmap="magma")
        self.recu_ax.invert_yaxis()
        self.recu_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.recu_ax.yaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))

        self.canvas.draw_idle()

    def _format_timedelta(self, x, pos):
        if int(x) >= len(self.timestamps):
            return ""
        x = self.timestamps[int(x)]
        return time_format.msec_to_timestr_with_fff(x)

    def _click_graph(self, event):
        x = event.xdata
        y = event.ydata
        tar_ax = event.inaxes
        if x is None or y is None:
            return

        # click event on recu_ax
        if tar_ax == self.recu_ax:
            # extract dataframe at timestamp_msec
            plot_arr = self.plot_mat[:, int(y)]
            self.line_ax.cla()
            self.line_ax.plot(plot_arr)
            self.line_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
            self.hline = self.line_ax.axhline(0.1, color='gray', lw=0.5)
            self.canvas.draw_idle()
        # click event on line_ax
        elif tar_ax == self.line_ax:
            timestamp_msec = self.timestamps[int(x)]
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

    def _horizontal_line(self, event):
        if event.inaxes is None or self.line_ax is None:
            return
        x = event.xdata
        y = event.ydata
        if x is None or y is None:
            return
        self.hline.set_ydata([y])
        self.canvas.draw_idle()
