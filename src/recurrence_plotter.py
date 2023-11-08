import os

import cv2
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class RecurrencePlotter:
    def __init__(self):
        dpi = 72
        fig_width = 700
        fig_height = 700
        self.fig = plt.figure(figsize=(fig_width/dpi, fig_height/dpi), dpi=dpi)
        self.fig.canvas.mpl_connect("button_press_event", self._click_graph)

        # axesのレイアウト設定
        gs = gridspec.GridSpec(1, 1, hspace=0.05, wspace=0.05)
        self.recu_ax = self.fig.add_subplot(gs[0, 0])
 
    def pack(self, master):
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        toolbar = NavigationToolbar2Tk(self.canvas, master)
        toolbar.pack()
        self.canvas.get_tk_widget().pack(expand=False)

    def draw(self, plot_df, member: str, keypoint: str, dt_span: int, thinning: int, video_path: str):
        if os.path.exists(video_path) is True:
            cap = cv2.VideoCapture(
                video_path,
                apiPreference=cv2.CAP_ANY,
                params=[cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY])
        else:
            cap = None
        self.cap = cap

        self.recu_ax.imshow(plot_df, cmap="gray")
        self.recu_ax.invert_yaxis()
        self.canvas.draw()

    def clear(self):
        self.recu_ax.cla()
        self.canvas.draw()

    def _click_graph(self, event):
        x = event.xdata
        y = event.ydata
        if x is None or y is None:
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, int(x))
        ret, frame_x = self.cap.read()
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, int(y))
        ret, frame_y = self.cap.read()
        show_img = cv2.vconcat([frame_x, frame_y])
        if ret is True:
            cv2.imshow("frame", show_img)
            cv2.waitKey(1)
