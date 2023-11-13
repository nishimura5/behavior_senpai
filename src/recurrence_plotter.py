import os

import cv2
import matplotlib.pyplot as plt
from matplotlib import ticker, gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import time_format


class RecurrencePlotter:
    def __init__(self):
        dpi = 72
        fig_width = 700
        fig_height = 700
        self.fig = plt.figure(figsize=(fig_width/dpi, fig_height/dpi), dpi=dpi)
        self.fig.canvas.mpl_connect("button_press_event", self._click_graph)

        # axesのレイアウト設定
        gs = gridspec.GridSpec(1, 1)
        self.recu_ax = self.fig.add_subplot(gs[0, 0])
 
    def pack(self, master):
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        toolbar = NavigationToolbar2Tk(self.canvas, master)
        toolbar.pack()
        self.canvas.get_tk_widget().pack(expand=False)

    def draw(self, plot_mat, timestamps, video_path: str):
        if os.path.exists(video_path) is True:
            cap = cv2.VideoCapture(
                video_path,
                apiPreference=cv2.CAP_ANY,
                params=[cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY])
        else:
            cap = None
        self.cap = cap
        self.timestamps = timestamps
        self.recu_ax.imshow(plot_mat, cmap="gray")
        self.recu_ax.invert_yaxis()
        self.recu_ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))
        self.recu_ax.yaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))

        self.canvas.draw()

    def clear(self):
        self.recu_ax.cla()
        self.canvas.draw()

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
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_msec)
            ret, frame = self.cap.read()
            if frame.shape[0] >= 1080:
                resize_height = 720
                resize_width = int(frame.shape[1] * resize_height / frame.shape[0])
                frame = cv2.resize(frame, (resize_width, resize_height))
            if ret is True:
                cv2.imshow("frame", frame)
                cv2.waitKey(1)
