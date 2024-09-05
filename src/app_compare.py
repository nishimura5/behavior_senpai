import glob
import itertools
import os
import tkinter as tk
from tkinter import filedialog, ttk

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import ttkthemes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from behavior_senpai import time_format, windows_and_mac
from gui_parts import Combobox, TempFile
from gui_tree import Tree

# plt.rcParams["font.family"] = "sans-serif"
# plt.rcParams["font.sans-serif"] = ["Yu Gothic", "Meiryo", "Takao", "IPAexGothic", "IPAPGothic", "VL PGothic", "Noto Sans CJK JP"]


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Compare")
        self.pack(padx=14, pady=14)

        temp = TempFile()
        width, height, dpi = temp.get_scene_table_graph_size()
        if temp.data["trk_path"] == "":
            self.tar_dir = "~"
        else:
            trk_path = temp.data["trk_path"]
            if temp.data["calc_case"] != "":
                calc_case = temp.data["calc_case"]
                self.tar_dir = os.path.abspath(os.path.join(trk_path, "..", "..", "calc", calc_case))
            else:
                self.tar_dir = os.path.dirname(trk_path)

        self.fig = plt.figure(
            figsize=(width / dpi, height / dpi),
            dpi=dpi,
            tight_layout=True,
        )
        self.box_ax = self.fig.add_subplot(111)

        head_frame = ttk.Frame(self)
        head_frame.pack(pady=5, fill=tk.X)
        select_folder_btn = ttk.Button(head_frame, text="Select Folder", command=self.select_folder)
        select_folder_btn.pack(padx=(0, 5), side=tk.LEFT)

        draw_btn = ttk.Button(head_frame, text="Draw", command=self.calc)
        draw_btn.pack(side=tk.LEFT)

        control_frame = ttk.Frame(self)
        control_frame.pack(pady=5, fill=tk.X)

        cols = [1, 2, 3, 4]
        self.legend_col_combo = Combobox(control_frame, label="Legend column:", width=5, values=cols)
        self.legend_col_combo.pack_horizontal(padx=5)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(pady=5, fill=tk.X)
        cols = [
            {"name": "code", "width": 100},
            {"name": "label", "width": 100},
        ]
        self.tree = Tree(tree_frame, cols, height=6, right_click=True)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.add_rename(column=1)
        self.tree.add_menu("Remove", self.remove)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        toolbar.pack()
        self.canvas.get_tk_widget().pack(expand=False)

    def select_folder(self):
        tar_path = filedialog.askdirectory(initialdir=self.tar_dir)
        self.tar_pkl_list = glob.glob(os.path.join(tar_path, "*.bc.pkl"))

        self.tree.clear()
        class_list = []
        self.member_list = []
        for file_path in self.tar_pkl_list:
            src_df = pd.read_pickle(file_path)
            members = src_df.index.get_level_values("member").unique().tolist()
            scene_table = bool_to_dict(src_df)
            class_list += scene_table["class"]
            self.member_list += members
        class_list = list(set(class_list))
        class_list.sort()
        self.member_list = list(set(self.member_list))
        self.member_list.sort()

        print(class_list)
        print(self.member_list)
        for i, class_name in enumerate(class_list):
            values = [class_name, class_name]
            self.tree.insert(values)

    def calc(self):
        tree_list = self.tree.get_all()
        total_df = pd.DataFrame()
        for file_path in self.tar_pkl_list:
            src_df = pd.read_pickle(file_path)
            src_columns = src_df.columns
            columns_white_list = [str(c) for c, _ in tree_list] + ["class", "timestamp"]
            # and src_columns and columns_white_list
            code_list = [c for c in columns_white_list if c in src_columns]
            src_df = src_df[code_list]
            member_name = src_df.index.get_level_values("member").unique().tolist()[0]
            scene_table = bool_to_dict(src_df)
            scene_df = pd.DataFrame(scene_table)
            scene_df["start"] = pd.to_timedelta(scene_df["start"]).dt.total_seconds()
            scene_df["end"] = pd.to_timedelta(scene_df["end"]).dt.total_seconds()
            scene_df["duration"] = scene_df["end"] - scene_df["start"]
            scene_df = scene_df.sort_values("class")

            sum_df = scene_df.groupby("class").sum()
            sum_df["class"] = sum_df.index
            sum_df["member"] = member_name
            sum_df["code"] = sum_df["class"]
            sum_df = sum_df.set_index(["member", "code"])

            for class_name, _ in tree_list:
                class_name = str(class_name)
                if (member_name, class_name) not in sum_df.index:
                    sum_df.loc[(member_name, class_name), :] = 0

            sum_df = sum_df.loc[:, ["duration"]]
            total_df = pd.concat([total_df, sum_df], axis=0)

        total_df["total"] = total_df["duration"] / 60
        total_df["time"] = total_df["total"] / 60
        total_df = total_df.reset_index()

        # generate rename_dict from tree view
        rename_dict = {str(c): str(n) for c, n in tree_list}
        total_df = total_df.set_index(["code", "member"])
        total_df = total_df.rename(index=rename_dict)
        total_df = total_df.sort_index()["time"]
        self.draw(total_df)

    def draw(self, total_df):
        self.box_ax.clear()
        legend_col = int(self.legend_col_combo.get())
        palette = sns.color_palette("coolwarm", 19)
        sns.swarmplot(x="code", y="time", data=total_df.reset_index(), hue="member", size=4, linewidth=1, palette=palette, ax=self.box_ax)
        sns.boxplot(
            x="code",
            y="time",
            data=total_df.reset_index(),
            color="lightgray",
            width=0.7,
            ax=self.box_ax,
            showmeans=True,
        )
        self.box_ax.yaxis.set_minor_locator(plt.MultipleLocator(0.1))

        self.box_ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0, ncol=legend_col, fontsize=8, frameon=False)
        self.box_ax.grid(axis="y", color="gray", linestyle="--", linewidth=0.5)
        self.box_ax.grid(axis="y", color="gray", linestyle="--", linewidth=0.5, which="minor")
        self.canvas.draw()

    def remove(self):
        self.tree.delete_selected()


def bool_to_dict(src_df, time_min=0, time_max=60 * 3600 * 1000 * 2):
    scene_table = {"start": [], "end": [], "class": []}
    for col_name in src_df.columns:
        if col_name == "class" or col_name == "timestamp":
            continue
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
            scene_table["class"].append(col_name)
    return scene_table


def quit(root):
    root.quit()
    root.destroy()


def main():
    bg_color = "#e8e8e8"
    root = ttkthemes.ThemedTk(theme="breeze")
    root.geometry("+150+150")
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
