import glob
import itertools
import os
import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import ttkthemes
from gui_parts import TempFile, Tree
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from python_senpai import time_format, windows_and_mac

# 日本語フォント
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Yu Gothic", "Meiryo", "Takao", "IPAexGothic", "IPAPGothic", "VL PGothic", "Noto Sans CJK JP"]
plt.rcParams["font.size"] = 15


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Compare")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        self.calc_case = temp.data["calc_case"]

        width = 1200
        height = 1200
        self.fig = plt.figure(figsize=(width / 200, height / 200), dpi=200, tight_layout=True)
        self.box_ax = self.fig.add_subplot(111)

        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X)
        select_folder_btn = ttk.Button(control_frame, text="Select Folder", command=self.select_folder)
        select_folder_btn.pack(side=tk.LEFT)

        draw_btn = ttk.Button(control_frame, text="Draw", command=self.calc)
        draw_btn.pack(side=tk.LEFT)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.X)
        cols = [
            {"name": "code", "width": 100},
            {"name": "label", "width": 100},
        ]
        self.tree = Tree(tree_frame, cols, height=10, right_click=True)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        toolbar.pack()
        self.canvas.get_tk_widget().pack(expand=False)

    def select_folder(self):
        print("selcect_folder")

    def calc(self):
        tar_folder = ""

        tar_file_list = glob.glob(os.path.join(tar_folder, "*.bc.pkl"))

        total_df = pd.DataFrame()
        for i, file_path in enumerate(tar_file_list):
            file_name = os.path.basename(file_path).split(".")[0]
            member_name = file_name.split("_")[1]
            print(f"member_name{i:02}: {member_name}")
            src_df = pd.read_pickle(file_path)
            scene_table = bool_to_dict(src_df)
            scene_df = pd.DataFrame(scene_table)
            scene_df["start"] = pd.to_timedelta(scene_df["start"]).dt.total_seconds()
            scene_df["end"] = pd.to_timedelta(scene_df["end"]).dt.total_seconds()
            scene_df["duration"] = scene_df["end"] - scene_df["start"]
            scene_df = scene_df.sort_values("description")

            sum_df = scene_df.groupby("description").sum()
            sum_df["description"] = sum_df.index
            sum_df["member"] = member_name
            sum_df["code"] = sum_df["description"]
            sum_df = sum_df.set_index(["member", "code"])

            if (member_name, "lean_forward") not in sum_df.index:
                sum_df.loc[(member_name, "lean_forward"), :] = 0
            if (member_name, "prone") not in sum_df.index:
                sum_df.loc[(member_name, "prone"), :] = 0
            if (member_name, "side_lying") not in sum_df.index:
                sum_df.loc[(member_name, "side_lying"), :] = 0
            if (member_name, "0") not in sum_df.index:
                sum_df.loc[(member_name, "0"), :] = 0

            sum_df = sum_df.loc[:, ["duration"]]
            print(sum_df)

            total_df = pd.concat([total_df, sum_df], axis=0)

        total_df["total"] = total_df["duration"] / 60
        total_df["time"] = total_df["total"] / 60
        total_df = total_df.reset_index()

        # codeごとにbar graphを作成
        total_df = total_df.set_index(["code", "member"])
        total_df = total_df.rename(index={"side_lying": "a", "prone": "b", "lean_forward": "c", "0": "d"})
        total_df = total_df.sort_index()["time"]
        self.draw(total_df)

    def draw(self, total_df):
        # hueの色数を増やす
        palette = sns.color_palette("coolwarm", 19)
        sns.swarmplot(
            x="code", y="time", data=total_df.reset_index(), hue="member", edgecolor="gray", linewidth=1, size=8, palette=palette, ax=self.box_ax
        )
        sns.boxplot(x="code", y="time", data=total_df.reset_index(), color="lightgray", width=0.7, ax=self.box_ax, showmeans=True)
        self.box_ax.yaxis.set_minor_locator(plt.MultipleLocator(0.1))

        self.box_ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0, fontsize=8, frameon=False)
        self.box_ax.grid(axis="y", color="gray", linestyle="--", linewidth=0.5)
        self.box_ax.grid(axis="y", color="gray", linestyle="--", linewidth=0.5, which="minor")
        self.canvas.draw()


#        dst_path = os.path.join(tar_folder, "scene_table_sum.png")
#        plt.savefig(dst_path, bbox_inches="tight", dpi=300)


def bool_to_dict(src_df, time_min=0, time_max=60 * 3600 * 1000 * 2):
    scene_table = {"start": [], "end": [], "description": []}
    for col_name in src_df.columns:
        if col_name not in ["side_lying", "prone", "lean_forward", "0"]:
            continue
        print(col_name)
        diff_prev_sr = src_df.groupby("member")[col_name].diff().astype(bool)
        diff_follow_sr = src_df.groupby("member")[col_name].diff(-1).astype(bool)
        # ラベリング、-1とNaNはastypeでTrueになる
        starts = src_df.loc[(src_df[col_name] & diff_prev_sr), "timestamp"].values.tolist()
        ends = src_df.loc[(src_df[col_name] & diff_follow_sr), "timestamp"].values.tolist()
        # 要素の先頭を比較してstartsの先頭にtime_minを追加
        if starts[0] > ends[0]:
            starts.insert(0, time_min)
        for start, end in itertools.zip_longest(starts, ends, fillvalue=time_max):
            start_str = time_format.msec_to_timestr_with_fff(start)
            end_str = time_format.msec_to_timestr_with_fff(end)
            scene_table["start"].append(start_str)
            scene_table["end"].append(end_str)
            scene_table["description"].append(col_name)
    return scene_table


def quit(root):
    root.quit()
    root.destroy()


def main():
    bg_color = "#e8e8e8"
    root = ttkthemes.ThemedTk(theme="breeze")
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
