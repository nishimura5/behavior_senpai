import os

import cv2
import matplotlib.pyplot as plt
from matplotlib import ticker, gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


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
        sec = x / 1000
        hours = sec // 3600
        remain = sec - (hours*3600)
        minutes = remain // 60
        seconds = remain - (minutes * 60)
        return f'{int(hours)}:{int(minutes):02}:{int(seconds):02}'

    def _click_graph(self, event):
        x = event.xdata
        y = event.ydata
        if x is None or y is None:
            return
        x_msec = self.timestamps[int(event.xdata)]
        y_msec = self.timestamps[int(event.ydata)]
        self.cap.set(cv2.CAP_PROP_POS_MSEC, x_msec)
        ret, frame_x = self.cap.read()
        self.cap.set(cv2.CAP_PROP_POS_MSEC, y_msec)
        ret, frame_y = self.cap.read()
        show_img = cv2.vconcat([frame_x, frame_y])
        if show_img.shape[0] > 1000:
            resize_height = 1000
            resize_width = int(show_img.shape[1] * resize_height / show_img.shape[0])
            show_img = cv2.resize(show_img, (resize_width, resize_height))
        if ret is True:
            cv2.imshow("frame", show_img)
            cv2.waitKey(1)
