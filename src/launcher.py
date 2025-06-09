import os
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
import ttkthemes

import app_area_filter
import app_compare_files
import app_detect
import app_dimredu
import app_dlc_to_trk
import app_feat_mix
import app_keypoint_samples
import app_member_edit
import app_points_calc
import app_scene_table
import app_smoothing
import app_track_list
import app_trajplot as k2t
import license_view
import pref_list
from behavior_senpai import df_attrs, file_inout, keypoints_proc, vcap, windows_and_mac
from gui_parts import CalcCaseEntry, TempFile
from main_gui_parts import PklSelector, VideoViewer


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Behavior Senpai")
        self.pack(padx=14, pady=14)
        self.bind("<Map>", self.load)

        temp = TempFile()
        w_width, w_height = temp.get_top_window_size()
        w_height = int(w_height)

        # ボタンのフレーム
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(side=tk.LEFT, anchor=tk.NW)

        detect_label = ttk.Label(buttons_frame, text="Preparation")
        detect_label.pack(side=tk.TOP)
        v2k_button = ttk.Button(buttons_frame, text="Detect", command=lambda: self.launch_detect_window())
        v2k_button.pack(side=tk.TOP, fill=tk.X, pady=4)
        self.tl_button = ttk.Button(
            buttons_frame,
            text="Track list",
            command=lambda: self.launch_window(app_track_list.App, grab=True),
            state=tk.DISABLED,
        )
        self.tl_button.pack(side=tk.TOP, fill=tk.X, pady=4)
        edit_label = ttk.Label(buttons_frame, text="Edit")
        edit_label.pack(side=tk.TOP, pady=(8, 0))
        self.member_edit_button = ttk.Button(
            buttons_frame,
            text="Member",
            command=lambda: self.launch_window(app_member_edit.App, dialog_size="1000x750", edit_df=True, grab=True),
            state=tk.DISABLED,
        )
        self.member_edit_button.pack(side=tk.TOP, fill=tk.X, pady=4)
        self.area_filter_button = ttk.Button(
            buttons_frame,
            text="Area",
            command=lambda: self.launch_window(app_area_filter.App, edit_df=True, grab=True),
            state=tk.DISABLED,
        )
        self.area_filter_button.pack(side=tk.TOP, fill=tk.X, pady=4)
        self.smooth_button = ttk.Button(
            buttons_frame,
            text="Smooth",
            command=lambda: self.launch_window(app_smoothing.App, dialog_size="1000x750", edit_df=True, grab=True),
            state=tk.DISABLED,
        )
        self.smooth_button.pack(side=tk.TOP, fill=tk.X, pady=4)
        self.scene_table_button = ttk.Button(
            buttons_frame,
            text="Scene table",
            command=lambda: self.launch_scene_table_window(app_scene_table.App),
            state=tk.DISABLED,
        )
        self.scene_table_button.pack(side=tk.TOP, fill=tk.X, pady=4)

        calc_label = ttk.Label(buttons_frame, text="Feature")
        calc_label.pack(side=tk.TOP, pady=(8, 0))
        self.k2f_button = ttk.Button(
            buttons_frame,
            text="Trajectory",
            command=lambda: self.launch_window(k2t.App, dialog_size="1200x800"),
            state=tk.DISABLED,
        )
        self.k2f_button.pack(side=tk.TOP, fill=tk.X, pady=4)
        self.multi_point_button = ttk.Button(
            buttons_frame,
            text="Multiple points",
            command=lambda: self.launch_window(app_points_calc.App, dialog_size="1200x800"),
            state=tk.DISABLED,
        )
        self.multi_point_button.pack(side=tk.TOP, fill=tk.X, pady=4)
        self.feat_mix_button = ttk.Button(
            buttons_frame,
            text="Mix/Norm",
            command=lambda: self.launch_window(app_feat_mix.App, dialog_size="1200x800"),
            state=tk.DISABLED,
        )
        self.feat_mix_button.pack(side=tk.TOP, fill=tk.X, pady=4)
        self.dimredu_button = ttk.Button(
            buttons_frame,
            text="Dim-reduction",
            command=lambda: self.launch_window(app_dimredu.App, dialog_size="1500x800"),
            state=tk.DISABLED,
        )
        self.dimredu_button.pack(side=tk.TOP, fill=tk.X, pady=4)

        pref_label = ttk.Label(buttons_frame, text="Misc")
        pref_label.pack(side=tk.TOP, pady=(8, 0))
        pref_list_button = ttk.Button(
            buttons_frame,
            text="Preference",
            command=lambda: self.launch_window(pref_list.App),
        )
        pref_list_button.pack(side=tk.TOP, fill=tk.X, pady=4)

        # srcにlicense.jsonがある場合はボタンを表示
        license_path = "./src/license.json"
        if os.path.exists(license_path):
            license_button = ttk.Button(
                buttons_frame,
                text="License",
                command=lambda: self.launch_window(license_view.App),
                width=20,
            )
            license_button.pack(side=tk.TOP, fill=tk.X, pady=4)

        main_frame = ttk.Frame(self)
        main_frame.pack(side=tk.RIGHT, anchor=tk.NE, padx=(24, 0))
        head_frame = ttk.Frame(main_frame)
        head_frame.pack(anchor=tk.N, expand=True, fill=tk.X)
        load_frame = ttk.Frame(head_frame)
        load_frame.pack(side=tk.LEFT, anchor=tk.W, pady=(0, 5))

        a_frame = ttk.Frame(load_frame)
        a_frame.pack()
        self.pkl_selector = PklSelector(a_frame)
        self.pkl_selector.pack()
        self.pkl_selector.set_command(cmd=self.load)

        calc_case_frame = ttk.Frame(load_frame)
        calc_case_frame.pack(anchor=tk.W, pady=(4, 0))
        self.calc_case_entry = CalcCaseEntry(calc_case_frame, temp.data["calc_case"])
        self.calc_case_entry.pack(pady=(4, 0), side=tk.LEFT)
        self.go_to_folder_btn = ttk.Button(
            calc_case_frame,
            text="Open calc folder",
            command=lambda: windows_and_mac.go_to_folder(os.path.dirname(os.path.dirname(self.pkl_path)), "calc"),
        )
        self.go_to_folder_btn.pack(padx=(4, 0))

        save_frame = ttk.Frame(head_frame)
        save_frame.pack(anchor=tk.E)
        self.save_button = ttk.Button(save_frame, text="Overwrite", command=self.overwrite, width=10)
        self.save_button.pack()
        self.save_button["state"] = tk.DISABLED
        compare_button = ttk.Button(
            save_frame,
            text="Compare",
            command=lambda: self.launch_window(app_compare_files.App),
            width=10,
        )
        compare_button.pack(pady=4)

        view_frame = ttk.Frame(main_frame)
        view_frame.pack(pady=(5, 0), anchor=tk.W)

        video_frame = ttk.Frame(view_frame)
        video_frame.pack(side=tk.LEFT, anchor=tk.N)
        self.vw = VideoViewer(video_frame, width=w_width, height=w_height)
        self.vw.pack()

        attrs_frame = ttk.Frame(view_frame)
        attrs_frame.pack(side=tk.RIGHT, anchor=tk.N)
        self.attrs_textbox = tk.Text(attrs_frame, relief=tk.FLAT, width=40, padx=10, pady=10)
        self.attrs_textbox.pack(fill=tk.BOTH, expand=True, padx=(10, 0))

        keypoints_btn = ttk.Button(attrs_frame, text="Keypoint samples", command=self.open_kp_samples)
        keypoints_btn.pack(padx=(10, 0), pady=(5, 0), expand=True, fill=tk.X)

        self.vcap = vcap.VideoCap()
        self.cap = self.vcap
        self.pkl_path = ""
        self.pkl_dir = None
        self.src_df = None
        self.time_span = None
        self.calc_case = self.calc_case_entry.get()
        self.rotate_angle = 0

    def load(self, event=None):
        pkl_path = self.pkl_selector.get_trk_path()
        print(f"Loading {pkl_path}")
        # check if deeplabcut file (ext = .h5)
        if pkl_path.endswith(".h5"):
            pkl_path = self.launch_dlc_to_trk(pkl_path)
            self.pkl_selector.rename_pkl_path_label(pkl_path)
            temp = TempFile()
            data = temp.load()
            data["trk_path"] = pkl_path
            temp.save(data)

        load_df = file_inout.load_track_file(pkl_path)
        if load_df is None:
            self.pkl_selector.rename_pkl_path_label(self.pkl_path)
            return
        # enable buttons
        self.tl_button.config(state="normal")
        self.member_edit_button.config(state="normal")
        self.area_filter_button.config(state="normal")
        self.smooth_button.config(state="normal")
        self.scene_table_button.config(state="normal")
        self.k2f_button.config(state="normal")
        self.multi_point_button.config(state="normal")
        self.feat_mix_button.config(state="normal")
        self.dimredu_button.config(state="normal")

        self.pkl_path = pkl_path
        self.src_df = load_df
        self.src_df = keypoints_proc.zero_point_to_nan(self.src_df)
        self.src_df = self.src_df[~self.src_df.index.duplicated(keep="first")]
        src_attrs = df_attrs.DfAttrs(self.src_df)
        self.pkl_dir = os.path.dirname(self.pkl_path)
        self.vcap.set_frame_size(src_attrs.attrs["frame_size"])
        if isinstance(src_attrs.attrs["video_name"], list):
            video_list = [os.path.abspath(os.path.join(self.pkl_dir, os.pardir, video)) for video in src_attrs.attrs["video_name"]]
            self.cap = vcap.MultiVcap(self.vcap)
            self.cap.open_files(video_list)
        else:
            self.vcap.open_file(os.path.join(self.pkl_dir, os.pardir, src_attrs.attrs["video_name"]))
            self.cap = self.vcap

        # UIの更新
        self.time_span = (
            self.src_df["timestamp"].min(),
            self.src_df["timestamp"].max(),
        )
        self.pkl_selector.set_prev_next(src_attrs.attrs)
        self.rotate_angle = src_attrs.attrs["rotate"] if "rotate" in src_attrs.attrs.keys() else 0
        print(f"rotate = {self.rotate_angle}")
        self.vw.set_cap(self.cap, src_attrs.attrs["frame_size"], anno_trk=self.src_df, rotate=self.rotate_angle)
        self.update_attrs()

    def update_attrs(self):
        src_attrs = self.src_df.attrs
        self.attrs_textbox.delete("1.0", tk.END)
        print_str = ""
        for key, value in src_attrs.items():
            if key == "scene_table":
                num = len(value["start"])
                print_str += f"{key}: # {num} scenes.\n"
            elif isinstance(value, dict):
                print_str += f"{key}:\n"
                for key2, value2 in value.items():
                    print_str += f"  {key2}: {value2}\n"
            else:
                print_str += f"{key}: {value}\n"
        self.attrs_textbox.insert(tk.END, print_str)

    def launch_detect_window(self):
        window_pos = self.master.geometry().split("+")[1:]
        dlg_modal = tk.Toplevel(self)
        dlg_modal.geometry(f"+{window_pos[0]}+{window_pos[1]}")
        dlg_modal.focus_set()
        dlg_modal.grab_set()
        dlg_modal.transient(self.master)
        d = app_detect.App(dlg_modal)
        dlg_modal.protocol(
            "WM_DELETE_WINDOW",
            lambda: [dlg_modal.destroy(), cv2.destroyAllWindows(), d.close()],
        )
        self.wait_window(dlg_modal)
        if d.trk_path != "":
            self.pkl_selector.trk_path = d.trk_path
            self.pkl_selector.rename_pkl_path_label(d.trk_path)
            temp = TempFile()
            data = temp.load()
            data["trk_path"] = d.trk_path
            temp.save(data)
            self.load()

    def launch_scene_table_window(self, app):
        self.calc_case_entry.save()
        window_pos = self.master.geometry().split("+")[1:]
        dlg_modal = tk.Toplevel(self)
        dlg_modal.geometry(f"+{window_pos[0]}+{window_pos[1]}")
        dlg_modal.focus_set()
        dlg_modal.grab_set()
        dlg_modal.transient(self.master)
        args = {
            "src_df": self.src_df,
            "trk_pkl_name": os.path.basename(self.pkl_path),
            "time_span_msec": self.time_span,
            "cap": self.cap,
            "pkl_dir": self.pkl_dir,
        }
        self.a = app(dlg_modal, args)
        dlg_modal.protocol(
            "WM_DELETE_WINDOW",
            lambda: [dlg_modal.destroy(), cv2.destroyAllWindows(), self.a.close()],
        )
        self.wait_window(dlg_modal)

        # ダイアログを閉じた後の処理
        cv2.destroyAllWindows()
        if self.a.scene_table is None:
            return

        self.src_df.attrs["scene_table"] = self.a.scene_table
        if "proc_history" not in self.src_df.attrs.keys():
            self.src_df.attrs["proc_history"] = []
        if self.a.history is not None:
            self.src_df.attrs["proc_history"].append(self.a.history)

        self.update_attrs()

        self.save_button["state"] = "normal"
        args["src_df"] = self.src_df

    def launch_window(self, app, dialog_size="", edit_df=False, grab=False):
        self.calc_case_entry.save()
        window_pos = self.master.geometry().split("+")[1:]
        dlg_modal = tk.Toplevel(self)
        dlg_modal.geometry(dialog_size + f"+{window_pos[0]}+{window_pos[1]}")
        dlg_modal.focus_set()
        if grab is True:
            dlg_modal.grab_set()
        dlg_modal.transient(self.master)
        current_position = self.vw.get_current_position()
        args = {
            "src_df": self.src_df,
            "trk_pkl_name": os.path.basename(self.pkl_path),
            "time_span_msec": self.time_span,
            "cap": self.cap,
            "pkl_dir": self.pkl_dir,
            "current_position": current_position,
        }
        self.a = app(dlg_modal, args)
        dlg_modal.protocol(
            "WM_DELETE_WINDOW",
            lambda: [dlg_modal.destroy(), cv2.destroyAllWindows(), self.a.close()],
        )
        self.wait_window(dlg_modal)

        # after closing the dialog
        cv2.destroyAllWindows()

        self.vw.canvas.anno.reload_temp_file()

        if edit_df is False:
            return
        if hasattr(self.a, "dst_df") is False:
            return
        if self.a.dst_df is None:
            return
        if self.src_df.equals(self.a.dst_df) is True and self.src_df.attrs == self.a.dst_df.attrs:
            return

        print("DataFrame Updated")
        self.src_df = self.a.dst_df
        if "proc_history" not in self.src_df.attrs.keys():
            self.src_df.attrs["proc_history"] = []
        if self.a.history is not None:
            self.src_df.attrs["proc_history"].append(self.a.history)

        self.update_attrs()
        if "rotate" in self.src_df.attrs.keys():
            self.rotate_angle = self.src_df.attrs["rotate"]
        print(f"rotate = {self.rotate_angle}")
        self.vw.set_trk(self.src_df, rotate=self.rotate_angle)

        self.save_button["state"] = "normal"
        args["src_df"] = self.src_df

        member_count = self.src_df.index.get_level_values(1).unique().size
        print(f"member_num = {member_count}")

    def launch_dlc_to_trk(self, h5_path):
        window_pos = self.master.geometry().split("+")[1:]
        dlg_modal = tk.Toplevel(self)
        dlg_modal.geometry(f"+{window_pos[0]}+{window_pos[1]}")
        dlg_modal.focus_set()
        dlg_modal.grab_set()
        dlg_modal.transient(self.master)
        self.a = app_dlc_to_trk.App(dlg_modal, h5_path)
        dlg_modal.protocol("WM_DELETE_WINDOW", lambda: [dlg_modal.destroy()])
        self.wait_window(dlg_modal)
        return self.a.trk_path

    def open_kp_samples(self):
        dataset_name = self.src_df.attrs["model"]
        kp_sample_dialog = app_keypoint_samples.App(self, dataset_name)
        self.wait_window(kp_sample_dialog)

    def overwrite(self):
        pkl_name = file_inout.overwrite_track_file(self.pkl_path, self.src_df)
        messagebox.showinfo("Overwrite", f"Overwritten.\nfile name: {pkl_name}")
        self.save_button["state"] = tk.DISABLED


def quit(root):
    root.quit()
    root.destroy()


def main():
    print("Behavior Senpai")
    bg_color = "#e8e8e8"
    root = ttkthemes.ThemedTk(theme="breeze")
    root.geometry("+100+100")
    root.configure(background=bg_color)
    root.option_add("*background", bg_color)
    root.option_add("*Canvas.background", bg_color)
    root.option_add("*Text.background", "#fcfcfc")
    windows_and_mac.set_app_icon(root)
    s = ttk.Style(root)
    s.configure(".", background=bg_color)
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", lambda: quit(root))
    app.mainloop()


if __name__ == "__main__":
    main()
