import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

from yolo_detector import YoloDetector
from mediapipe_detector import MediaPipeDetector
import windows_and_mac
import roi_by_click
from video_cap_with_roi import RoiCap


class App(tk.Frame):
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Video to Keypoints")
        self.pack(padx=10, pady=10)

        top_btn_frame = tk.Frame(self)
        top_btn_frame.pack(pady=10)
        select_video_btn = ttk.Button(top_btn_frame, text="Select video", command=self.select_video)
        select_video_btn.pack(side=tk.LEFT)
        self.video_path_label = ttk.Label(top_btn_frame, text="No video selected")
        self.video_path_label.pack(side=tk.LEFT)

        middle_btn_frame = tk.Frame(self)
        middle_btn_frame.pack()
        self.model_cbox = ttk.Combobox(middle_btn_frame, values=["YOLOv8 x-pose-p6", "MediaPipe Holistic"], state='readonly')
        self.model_cbox.pack(side=tk.LEFT, padx=15)
        self.roi_chk_val = tk.BooleanVar()
        self.roi_chk = ttk.Checkbutton(middle_btn_frame, text="ROI", variable=self.roi_chk_val)
        self.roi_chk.pack(side=tk.LEFT)

        bottom_btn_frame = tk.Frame(self)
        bottom_btn_frame.pack(pady=10)
        open_btn = ttk.Button(bottom_btn_frame, text="Open", command=lambda: windows_and_mac.open_file(self.video_path))
        open_btn.pack(side=tk.LEFT)
        exec_detector_btn = ttk.Button(bottom_btn_frame, text="Detect", command=self.exec_detector)
        exec_detector_btn.pack(side=tk.LEFT)
        go_to_folder_btn = ttk.Button(bottom_btn_frame, text="Go to 'trk' Folder", command=lambda: windows_and_mac.go_to_folder(self.video_path, 'trk'))
        go_to_folder_btn.pack(side=tk.LEFT)

    def select_video(self):
        init_dir = os.path.abspath(os.path.dirname(__file__))
        self.video_path = filedialog.askopenfilename(initialdir=init_dir)
        self.video_path_label["text"] = self.video_path

    def exec_detector(self):
        rcap = RoiCap(self.video_path)
        use_roi = self.roi_chk_val.get()
        if use_roi is True:
            roi_by_click.main(rcap)
        model_name = self.model_cbox.get()

        file_name = os.path.splitext(os.path.basename(self.video_path))[0]
        trk_dir = os.path.join(os.path.dirname(self.video_path), "trk")
        os.makedirs(trk_dir, exist_ok=True)
        pkl_path = os.path.join(trk_dir, f"{file_name}.pkl")

        if model_name == "YOLOv8 x-pose-p6":
            detector = YoloDetector(rcap)
        elif model_name == "MediaPipe Holistic":
            detector = MediaPipeDetector(rcap)

        detector.detect(roi=use_roi)
        result_df = detector.get_result()

        # attrsを埋め込み
        result_df.attrs["model"] = model_name

        result_df.to_pickle(pkl_path)


def quit(root):
    root.quit()
    root.destroy()


def main(args):
    root = tk.Tk()
    app = App(root, args)
    root.protocol("WM_DELETE_WINDOW", lambda: quit(root))
    app.mainloop()


if __name__ == "__main__":

    args = None

    main(args)
    exit()
