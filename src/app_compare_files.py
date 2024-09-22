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

from behavior_senpai import keypoints_proc, time_format, windows_and_mac
from gui_parts import Combobox, TempFile
from gui_tree import Tree

# plt.rcParams["font.family"] = "sans-serif"
# plt.rcParams["font.sans-serif"] = ["Yu Gothic", "Meiryo", "Takao", "IPAexGothic", "IPAPGothic", "VL PGothic", "Noto Sans CJK JP"]


class App(ttk.Frame):
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Compare")
        self.pack(padx=14, pady=14)

        temp = TempFile()
        width, height, dpi = temp.get_scene_table_graph_size()

        self.fig = plt.figure(
            figsize=(width / dpi, height / dpi),
            dpi=dpi,
            tight_layout=True,
        )
        self.box_ax = self.fig.add_subplot(111)

        head_frame = ttk.Frame(self)
        head_frame.pack(pady=5, fill=tk.X)
        #        self.file_type_combo_dict = {"track_file (.pkl)": "pkl", "feature file (.feat.pkl)": "feat", "category file (.bc.pkl)": "bc"}
        self.file_type_combo_dict = {"track_file (.pkl)": "pkl", "category file (.bc.pkl)": "bc"}
        self.tar_file_type_combo = Combobox(head_frame, label="File type:", width=18, values=list(self.file_type_combo_dict.keys()))
        self.tar_file_type_combo.pack_horizontal(padx=5)
        self.tar_file_type_combo.set_selected_bind(self.type_change)

        self.tar_dir = args["pkl_dir"]
        if os.path.basename(self.tar_dir) == "trk":
            self.tar_file_type_combo.set("track_file (.pkl)")
        else:
            self.tar_file_type_combo.set("category file (.bc.pkl)")

        self.select_folder_btn = ttk.Button(head_frame, text="Select trk folder", width=16, command=self.select_folder)
        self.select_folder_btn.pack(side=tk.LEFT)

        self.folder_path_label = ttk.Label(head_frame, text="")
        self.folder_path_label.pack(padx=5, side=tk.LEFT)

        load_btn = ttk.Button(head_frame, text="Load", command=self.load_files)
        load_btn.pack(side=tk.LEFT)

        control_frame = ttk.Frame(self)
        control_frame.pack(pady=5, fill=tk.X)

        cols = [1, 2, 3, 4]
        self.legend_col_combo = Combobox(control_frame, label="Legend column:", width=5, values=cols)
        self.legend_col_combo.pack_horizontal(padx=5)

        self.draw_btn = ttk.Button(control_frame, text="Draw", command=self.calc)
        self.draw_btn.pack(side=tk.LEFT)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(pady=5, fill=tk.X)
        cols = [
            {"name": "keypoint or code", "width": 100},
            {"name": "label on boxplot", "width": 100},
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

        self.load_files()

    def select_folder(self):
        self.tree.clear()
        self.tar_dir = filedialog.askdirectory(initialdir=self.tar_dir)
        self.folder_path_label["text"] = self.tar_dir
        # disable draw button
        self.draw_btn["state"] = tk.DISABLED

    def load_files(self):
        calc_type = self.file_type_combo_dict[self.tar_file_type_combo.get()]
        self.member_list = []
        if calc_type == "pkl":
            file_num, tree_list = self.load_keypoint_files(self.tar_dir)
        elif calc_type == "bc":
            file_num, tree_list = self.load_category_files(self.tar_dir)

        self.folder_path_label["text"] = f"{self.tar_dir} ({file_num} files)"
        print(self.member_list)
        # tree_list is keypoint_list or class_list
        for i, value in enumerate(tree_list):
            values = [value, value]
            self.tree.insert(values)
        self.draw_btn["state"] = tk.NORMAL

    def load_category_files(self, tar_path):
        self.tar_pkl_list = glob.glob(os.path.join(tar_path, "*.bc.pkl"))
        file_num = len(self.tar_pkl_list)

        class_list = []
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
        return file_num, class_list

    def load_keypoint_files(self, tar_path):
        self.tar_pkl_list = glob.glob(os.path.join(tar_path, "*.pkl"))
        # remove feat.pkl files and bc.pkl files
        self.tar_pkl_list = [f for f in self.tar_pkl_list if not f.endswith(".feat.pkl") and not f.endswith(".bc.pkl")]

        file_num = len(self.tar_pkl_list)

        keypoint_list = []
        for file_path in self.tar_pkl_list:
            src_df = pd.read_pickle(file_path)
            members = src_df.index.get_level_values("member").unique().tolist()
            keypoint_list += src_df.index.get_level_values("keypoint").unique().tolist()
            self.member_list += members
        keypoint_list = list(set(keypoint_list))
        self.member_list = list(set(self.member_list))
        self.member_list.sort()
        return file_num, keypoint_list

    def calc(self):
        calc_type = self.file_type_combo_dict[self.tar_file_type_combo.get()]
        tree_list = self.tree.get_all()
        if calc_type == "pkl":
            self.calc_keypoints(tree_list)
        elif calc_type == "bc":
            self.calc_categories(tree_list)

    def calc_categories(self, tree_list):
        total_df = pd.DataFrame()
        for file_path in self.tar_pkl_list:
            # if not bc.pkl file, skip
            if not file_path.endswith(".bc.pkl"):
                continue
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
        self.draw(total_df, "code", "time", locator=0.1)

    def calc_keypoints(self, tree_list):
        total_df = pd.DataFrame()
        for file_path in self.tar_pkl_list:
            src_df = pd.read_pickle(file_path)
            total_df = keypoints_proc.calc_total_distance(src_df, step_frame=1)
            total_df = pd.concat([total_df, total_df], axis=0)
        total_df = total_df.sort_values("total_distance", ascending=False)
        total_df = total_df.head(30)
        print(total_df)
        self.draw(total_df, "keypoint", "total_distance", locator=100)

    def draw(self, total_df, x, y, locator):
        self.box_ax.clear()
        legend_col = int(self.legend_col_combo.get())
        # number of hue is number of members
        members = len(total_df.index.get_level_values("member").unique().tolist())
        palette = sns.color_palette("coolwarm", members)
        sns.swarmplot(x=x, y=y, data=total_df.reset_index(), hue="member", size=4, linewidth=1, palette=palette, ax=self.box_ax)
        sns.boxplot(
            x=x,
            y=y,
            data=total_df.reset_index(),
            color="lightgray",
            width=0.7,
            ax=self.box_ax,
            showmeans=True,
        )
        self.box_ax.yaxis.set_minor_locator(plt.MultipleLocator(locator))

        self.box_ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0, ncol=legend_col, fontsize=8, frameon=False)
        self.box_ax.grid(axis="y", color="gray", linestyle="--", linewidth=0.5)
        self.box_ax.grid(axis="y", color="gray", linestyle="--", linewidth=0.5, which="minor")
        self.canvas.draw()

    def remove(self):
        self.tree.delete_selected()

    def type_change(self, event):
        calc_type = self.file_type_combo_dict[self.tar_file_type_combo.get()]
        if calc_type == "pkl":
            self.select_folder_btn["text"] = "Select trk folder"
        elif calc_type == "bc":
            self.select_folder_btn["text"] = "Select calc folder"
        self.draw_btn["state"] = tk.DISABLED

    def close(self):
        pass


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
