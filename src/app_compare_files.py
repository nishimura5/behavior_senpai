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

from behavior_senpai import df_attrs, hdf_df, keypoints_proc, time_format, windows_and_mac
from gui_parts import Combobox, IntEntry, TempFile
from gui_tree import Tree

# plt.rcParams["font.family"] = "sans-serif"
# plt.rcParams["font.sans-serif"] = ["Yu Gothic", "Meiryo", "Takao", "IPAexGothic", "IPAPGothic", "VL PGothic", "Noto Sans CJK JP"]


class App(ttk.Frame):
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Compare")
        self.pack(padx=14, pady=14)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()

        self.fig = plt.figure(
            figsize=(width / dpi, height / dpi),
            dpi=dpi,
            tight_layout=True,
        )
        self.box_ax = self.fig.add_subplot(111)

        head_frame = ttk.Frame(self)
        head_frame.pack(anchor=tk.NW, expand=True, fill=tk.X, pady=5)
        self.file_type_combo_dict = {"track_file (.pkl)": "pkl", "feature file (.feat.pkl)": "feat", "category file (.bc.pkl)": "bc"}
        self.tar_file_type_combo = Combobox(head_frame, label="File type:", width=18, values=list(self.file_type_combo_dict.keys()))
        self.tar_file_type_combo.pack_horizontal(padx=5)
        self.tar_file_type_combo.set_selected_bind(self.type_change)

        self.tar_dir = args["pkl_dir"]
        self.init_tar_dir = self.tar_dir
        if os.path.basename(self.tar_dir) == "trk":
            self.tar_file_type_combo.set("track_file (.pkl)")
        else:
            self.tar_file_type_combo.set("category file (.bc.pkl)")

        self.select_folder_btn = ttk.Button(head_frame, text="Select trk folder", width=16, command=self.select_folder)
        self.select_folder_btn.pack(side=tk.LEFT)

        self.folder_path_label = ttk.Label(head_frame, text="")
        self.folder_path_label.pack(padx=5, side=tk.LEFT, expand=True, fill=tk.X)

        self.scene_combo = Combobox(head_frame, label="Scene:", values=[""], width=15)
        self.scene_combo.pack_horizontal(anchor=tk.E, padx=5)

        control_frame = ttk.Frame(self)
        control_frame.pack(pady=5, fill=tk.X)

        self.diff_entry = IntEntry(control_frame, label="Diff period:", default=temp.data["dt_span"])
        self.diff_entry.pack_horizontal(padx=5)

        self.calc_combo = Combobox(control_frame, label="Calc:", values=["mean", "var", "median"])
        self.calc_combo.pack_horizontal(padx=5)

        self.y_axis_locater_entry = IntEntry(control_frame, label="Y axis locater:", default=0)
        self.y_axis_locater_entry.pack_horizontal(padx=5)

        cols = [1, 2, 3, 4]
        self.legend_col_combo = Combobox(control_frame, label="Legend column:", width=5, values=cols)
        self.legend_col_combo.pack_horizontal(padx=5)

        self.draw_btn = ttk.Button(control_frame, text="Draw", command=self.calc)
        self.draw_btn.pack(side=tk.LEFT)

        self.export_btn = ttk.Button(control_frame, text="Export", command=self.export)
        self.export_btn.pack(side=tk.LEFT)

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

        self.member_listbox = tk.Listbox(tree_frame, selectmode=tk.EXTENDED, height=6, exportselection=False)
        self.member_listbox.pack(side=tk.LEFT, fill=tk.Y)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        toolbar.pack()
        self.canvas.get_tk_widget().pack(expand=False)

        self.load_files()

    def select_folder(self):
        tar_dir = filedialog.askdirectory(initialdir=os.path.dirname(self.tar_dir))
        if not tar_dir:
            return
        self.tar_dir = tar_dir
        self.draw_btn["state"] = tk.DISABLED
        self.export_btn["state"] = tk.DISABLED
        self.load_files()

    def load_files(self):
        self.tree.clear()
        self.member_listbox.delete(0, tk.END)
        calc_type = self.file_type_combo_dict[self.tar_file_type_combo.get()]
        if calc_type == "pkl":
            file_num, member_list, tree_list = self.load_keypoint_files(self.tar_dir)
        elif calc_type == "bc":
            file_num, member_list, tree_list = self.load_category_files(self.tar_dir)
        elif calc_type == "feat":
            file_num, member_list, tree_list = self.load_feature_files(self.tar_dir)

        self.folder_path_label["text"] = f"{self.tar_dir} ({file_num} files)"
        # tree_list is keypoint_list or class_list
        for i, value in enumerate(tree_list):
            self.tree.insert([value, value])
        member_list.sort()
        for i, value in enumerate(member_list):
            self.member_listbox.insert(tk.END, value)
        self.draw_btn["state"] = tk.NORMAL
        self.export_btn["state"] = tk.NORMAL

    def load_category_files(self, tar_path):
        self.tar_pkl_list = glob.glob(os.path.join(tar_path, "*.h5"))
        file_num = len(self.tar_pkl_list)

        member_list = []
        class_list = []
        for file_path in self.tar_pkl_list:
            h5 = hdf_df.DataFrameStorage(file_path)
            src_df = h5.load_df("dimredu")
            idx = src_df.index
            src_df.index = src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str)])

            member_list += src_df.index.get_level_values("member").unique().tolist()
            scene_table = bool_to_dict(src_df)
            class_list += scene_table["class"]
        class_list = list(set(class_list))
        class_list.sort()
        member_list = list(set(member_list))

        return file_num, member_list, class_list

    def load_keypoint_files(self, tar_path):
        self.tar_pkl_list = glob.glob(os.path.join(tar_path, "*.pkl"))
        # remove feat.pkl files and bc.pkl files
        self.tar_pkl_list = [f for f in self.tar_pkl_list if not f.endswith(".feat.pkl") and not f.endswith(".bc.pkl")]
        file_num = len(self.tar_pkl_list)

        member_list = []
        keypoint_list = []
        scene_list = []
        for file_path in self.tar_pkl_list:
            src_df = pd.read_pickle(file_path)
            idx = src_df.index
            src_df.index = src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2]])

            member_list += src_df.index.get_level_values("member").unique().tolist()
            keypoint_list += src_df.index.get_level_values("keypoint").unique().tolist()

            src_attrs = df_attrs.DfAttrs(src_df)
            src_attrs.load_scene_table()
            scene_list += src_attrs.get_scene_descriptions(add_blank=True)

        keypoint_list = list(set(keypoint_list))
        member_list = list(set(member_list))
        scene_list = list(set(scene_list))
        self.scene_combo.set_values(scene_list)

        return file_num, member_list, keypoint_list

    def load_feature_files(self, tar_path):
        self.tar_pkl_list = glob.glob(os.path.join(tar_path, "*.h5"))
        file_num = len(self.tar_pkl_list)

        member_list = []
        feat_list = []
        scene_list = []
        for file_path in self.tar_pkl_list:
            h5 = hdf_df.DataFrameStorage(file_path)

            # get scene_table from attrs
            profile = h5.load_profile()
            dir_path = os.path.dirname(file_path)
            trk_path = os.path.join(dir_path, "..", "..", "trk", profile["track_name"])
            if not os.path.exists(trk_path):
                trk_path = os.path.join(dir_path, "..", "trk", profile["track_name"])
            if os.path.exists(trk_path):
                trk_df = pd.read_pickle(trk_path)
            src_attrs = df_attrs.DfAttrs(trk_df)
            src_attrs.load_scene_table()
            scene_list += src_attrs.get_scene_descriptions(add_blank=True)

            # get DataFrame
            points_df = h5.load_df("points")
            mixnorm_df = h5.load_df("mixnorm")
            # concat horizontally
            src_df = pd.concat([points_df, mixnorm_df], axis=1)
            idx = src_df.index
            src_df.index = src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str)])

            member_list += src_df.index.get_level_values("member").unique().tolist()
            feat_list += src_df.columns.tolist()

        feat_list = list(set(feat_list))
        feat_list.remove("timestamp")
        member_list = list(set(member_list))
        scene_list = list(set(scene_list))
        self.scene_combo.set_values(scene_list)

        return file_num, member_list, feat_list

    def calc(self):
        calc_type = self.file_type_combo_dict[self.tar_file_type_combo.get()]
        tree_list = self.tree.get_all()
        selected_member_idx_list = self.member_listbox.curselection()
        selected_member_list = [self.member_listbox.get(i) for i in selected_member_idx_list]
        if calc_type == "pkl":
            self.calc_keypoints(tree_list, selected_member_list)
        elif calc_type == "bc":
            self.calc_categories(tree_list, selected_member_list)
        elif calc_type == "feat":
            self.calc_features(tree_list, selected_member_list)

    def calc_categories(self, tree_list, member_list):
        draw_df = pd.DataFrame()
        class_list = [str(c) for c, _ in tree_list]
        member_list = [str(m) for m in member_list]
        # combination of member and keypoint
        for file_path in self.tar_pkl_list:
            # if not bc.pkl file, skip
            if not file_path.endswith(".h5"):
                continue
            h5 = hdf_df.DataFrameStorage(file_path)
            src_df = h5.load_df("dimredu")
            idx = src_df.index
            src_df.index = src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str)])
            src_columns = src_df.columns

            columns_white_list = class_list + ["class", "timestamp"]
            # and src_columns and columns_white_list
            code_list = [c for c in columns_white_list if c in src_columns]
            src_df = src_df[code_list]

            # filter by member_list
            valid_members = src_df.index.get_level_values("member").unique().tolist()
            valid_tree_list = [m for m in member_list if m in valid_members]
            extracted_df = src_df.loc[pd.IndexSlice[:, valid_tree_list], :]
            if extracted_df.empty:
                continue

            member_name = extracted_df.index.get_level_values("member").unique().tolist()[0]
            scene_table = bool_to_dict(extracted_df)
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
            draw_df = pd.concat([draw_df, sum_df], axis=0)

        draw_df["total"] = draw_df["duration"] / 60
        draw_df["time"] = draw_df["total"] / 60
        draw_df = draw_df.reset_index()

        # generate rename_dict from tree view
        rename_dict = {str(c): str(n) for c, n in tree_list}
        draw_df = draw_df.set_index(["code", "member"])
        draw_df = draw_df.rename(index=rename_dict)
        draw_df = draw_df.sort_index()["time"]
        self.draw(draw_df, "code", "time", locator=0.1)

    def calc_keypoints(self, tree_list, member_list):
        draw_df = pd.DataFrame()
        dt_span = self.diff_entry.get()
        tar_scene = self.scene_combo.get()
        y_axis_locater = self.y_axis_locater_entry.get()

        keypoint_list = [k for k, _ in tree_list]
        member_list = [str(m) for m in member_list]
        member_list.sort()
        # combination of member and keypoint
        tree_list = [(m, k) for m in member_list for k in keypoint_list]
        for file_path in self.tar_pkl_list:
            h5 = hdf_df.DataFrameStorage(file_path)
            src_df = h5.load_df("dimredu")
            idx = src_df.index
            src_df.index = src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2]])

            # filter by scene_table in attrs
            scene_filtered_df = self._filter_by_scene_table(src_df, tar_scene)
            if scene_filtered_df is None:
                continue

            # filter by member_list
            valid_members = scene_filtered_df.index.get_level_values("member").unique().tolist()
            valid_tree_list = [(m, k) for m, k in tree_list if m in valid_members]
            extracted_df = scene_filtered_df.loc[pd.IndexSlice[:, [m for m, k in valid_tree_list], [k for m, k in valid_tree_list]], :]
            if extracted_df.empty:
                continue

            total_df = keypoints_proc.calc_total_distance(extracted_df, step_frame=int(dt_span), per_plot=True)
            draw_df = pd.concat([draw_df, total_df], axis=0)
        draw_df = draw_df.sort_values("total_distance_per_plot", ascending=False)
        draw_df = draw_df.sort_index()
        self.draw(draw_df, "keypoint", "total_distance_per_plot", locator=y_axis_locater)

    def calc_features(self, tree_list, member_list):
        draw_df = pd.DataFrame()
        tar_scene = self.scene_combo.get()
        y_axis_locater = self.y_axis_locater_entry.get()

        feat_list = [f for f, _ in tree_list]
        member_list = [str(m) for m in member_list]
        member_list.sort()
        # combination of member and feature
        tree_list = [(m, f) for m in member_list for f in feat_list]
        for file_path in self.tar_pkl_list:
            h5 = hdf_df.DataFrameStorage(file_path)
            points_df = h5.load_df("points")
            mixnorm_df = h5.load_df("mixnorm")
            # concat horizontally
            src_df = pd.concat([points_df, mixnorm_df], axis=1)
            idx = src_df.index
            src_df.index = src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str)])

            # filter by scene_table in attrs
            scene_filtered_df = self._filter_by_scene_table(src_df, tar_scene)
            if scene_filtered_df is None:
                continue

            # filter by member_list and features
            valid_members = scene_filtered_df.index.get_level_values("member").unique().tolist()
            valid_features = scene_filtered_df.columns.tolist()
            valid_tree_list = [(m, f) for m, f in tree_list if m in valid_members and f in valid_features]
            extracted_df = scene_filtered_df.loc[pd.IndexSlice[:, [m for m, f in valid_tree_list]], [f for m, f in valid_tree_list]]
            if extracted_df.empty:
                continue

            calc_code = self.calc_combo.get()
            if calc_code == "mean":
                calc_df = extracted_df.groupby("member").mean()
            elif calc_code == "var":
                calc_df = extracted_df.groupby("member").var()
            elif calc_code == "median":
                calc_df = extracted_df.groupby("member").median()

            draw_df = pd.concat([draw_df, calc_df], axis=0)
        draw_df = draw_df.stack().reset_index()
        draw_df.columns = ["member", "feature", "mean"]
        draw_df = draw_df.set_index(["member", "feature"])
        draw_df = draw_df.sort_index()
        self.draw(draw_df, "feature", "mean", locator=y_axis_locater)

    def _filter_by_scene_table(self, src_df, tar_scene):
        src_attrs = df_attrs.DfAttrs(src_df)
        src_attrs.load_scene_table()
        scenes = src_attrs.get_scenes(tar_scene)
        scene_filtered_df = src_df.copy()
        if scenes is not None and len(scenes) > 0:
            condition_sr = pd.Series(False, index=src_df.index)
            for scene in scenes:
                condition_sr |= src_df["timestamp"].between(scene[0] - 1, scene[1] + 1)
            scene_filtered_df.loc[~condition_sr, :] = pd.NA
        elif tar_scene != "":
            return None
        return scene_filtered_df

    def draw(self, src_df, x, y, locator):
        self.box_ax.clear()
        legend_col = int(self.legend_col_combo.get())
        # number of hue is number of members
        members = len(src_df.index.get_level_values("member").unique().tolist())
        if members < 10:
            plot_size = 8
        else:
            plot_size = 6
        palette = sns.color_palette("coolwarm", members)
        sns.swarmplot(x=x, y=y, data=src_df.reset_index(), hue="member", size=plot_size, linewidth=1, palette=palette, ax=self.box_ax)
        sns.boxplot(
            x=x,
            y=y,
            data=src_df.reset_index(),
            color="lightgray",
            width=0.7,
            ax=self.box_ax,
            showmeans=True,
        )
        if locator > 0:
            self.box_ax.yaxis.set_major_locator(plt.MultipleLocator(locator))

        self.box_ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0, ncol=legend_col, fontsize=8, frameon=False)
        self.box_ax.grid(axis="y", color="gray", linestyle="--", linewidth=0.5)
        self.box_ax.grid(axis="y", color="gray", linestyle="--", linewidth=0.5, which="minor")
        self.canvas.draw()
        self.export_df = src_df

    def remove(self):
        self.tree.delete_selected()

    def type_change(self, event):
        calc_type = self.file_type_combo_dict[self.tar_file_type_combo.get()]
        if calc_type == "pkl":
            self.select_folder_btn["text"] = "Select trk folder"
        elif calc_type == "bc" or calc_type == "feat":
            self.select_folder_btn["text"] = "Select calc folder"
        self.draw_btn["state"] = tk.DISABLED
        self.export_btn["state"] = tk.DISABLED
        self.tar_dir = self.init_tar_dir
        self.folder_path_label["text"] = self.tar_dir
        self.member_listbox.delete(0, tk.END)
        self.tree.clear()

    def export(self):
        """Export result as csv file"""
        save_path = filedialog.asksaveasfilename(initialdir=self.tar_dir, filetypes=[("csv file", "*.csv")])
        if not save_path:
            return
        self.export_df.to_csv(save_path, index=True, header=True)

    def close(self):
        pass


def bool_to_dict(src_df, time_min=0, time_max=60 * 3600 * 1000 * 2):
    scene_table = {"start": [], "end": [], "class": []}
    end_src_df = src_df.copy()
    diff_ave = src_df["timestamp"].diff().mean()
    end_src_df["timestamp"] = src_df["timestamp"].shift(-1).fillna(src_df["timestamp"].max() + diff_ave)
    for col_name in src_df.columns:
        if col_name == "class" or col_name == "timestamp":
            continue
        diff_prev_sr = src_df.groupby("member")[col_name].diff().astype(bool)
        diff_follow_sr = src_df.groupby("member")[col_name].diff(-1).astype(bool)
        # ラベリング、-1とNaNはastypeでTrueになる
        starts = src_df.loc[(src_df[col_name] & diff_prev_sr), "timestamp"].values.tolist()
        ends = end_src_df.loc[(src_df[col_name] & diff_follow_sr), "timestamp"].values.tolist()
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
