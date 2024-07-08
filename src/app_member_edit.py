import tkinter as tk
from tkinter import ttk

import pandas as pd
from gui_parts import StrEntry, TempFile, TimeSpanEntry, Tree
from line_plotter import LinePlotter
from python_senpai import keypoints_proc, time_format


class App(ttk.Frame):
    """Application for editing members in the DataFrame."""

    def __init__(self, master, args):
        super().__init__(master)
        master.title("Member Edit")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.band = LinePlotter(fig_size=(width / dpi, height / dpi), dpi=dpi)

        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        setting_frame = ttk.Frame(control_frame)
        setting_frame.pack(fill=tk.X, expand=True, side=tk.LEFT)

        draw_frame = ttk.Frame(setting_frame)
        draw_frame.pack(pady=5)
        draw_btn = ttk.Button(draw_frame, text="Draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT)
        clear_btn = ttk.Button(draw_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT, padx=(10, 0))

        rename_frame = ttk.Frame(setting_frame)
        rename_frame.pack(pady=5)
        rename_member_label = ttk.Label(rename_frame, text="Rename Member")
        rename_member_label.pack(side=tk.LEFT, pady=5)
        self.tar_member_label_var = tk.StringVar()
        self.tar_member_label_var.set("None")
        tar_member_label = ttk.Label(rename_frame, textvariable=self.tar_member_label_var)
        tar_member_label.pack(side=tk.LEFT, padx=5)
        self.new_member_name_entry = StrEntry(rename_frame, label="to", width=12)
        self.new_member_name_entry.pack_horizontal(padx=(0, 5))
        rename_btn = ttk.Button(rename_frame, text="Rename", command=self.rename_member)
        rename_btn.pack(side=tk.LEFT, padx=5)

        self.time_span_entry = TimeSpanEntry(rename_frame)
        self.time_span_entry.pack(side=tk.LEFT, padx=20)

        remove_btn = ttk.Button(rename_frame, text="Remove", command=self.remove_member)
        remove_btn.pack(padx=(70, 0))

        tree_frame = ttk.Frame(setting_frame)
        tree_frame.pack(pady=5)
        cols = [
            {"name": "member", "width": 100},
            {"name": "start", "width": 100},
            {"name": "end", "width": 100},
            {"name": "duration", "width": 100},
            {"name": "keypoints/frame", "width": 100},
        ]
        self.tree = Tree(tree_frame, cols, height=6)
        self.tree.pack()
        self.tree.tree.bind("<<TreeviewSelect>>", self._select_tree_row)

        ok_frame = ttk.Frame(control_frame)
        ok_frame.pack(anchor=tk.NE, padx=(20, 0))
        ok_btn = ttk.Button(ok_frame, text="OK", command=self.on_ok)
        ok_btn.pack(pady=(0, 5))
        cancel_btn = ttk.Button(ok_frame, text="Cancel", command=self.cancel)
        cancel_btn.pack()

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)
        self.band.pack(plot_frame)
        self.band.set_single_ax()

        self.dst_df = None
        self.history = "member_edit"
        self._load(args)

    def _load(self, args):
        self.src_df = args["src_df"].copy()
        self.time_min, self.time_max = args["time_span_msec"]

        # Update GUI
        self.update_tree()
        self.clear()
        self.time_span_entry.update_entry(self.time_min, self.time_max)

        idx = self.src_df.index
        self.src_df.index = self.src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2]])
        self.band.set_vcap(args["cap"])

        # memberの数をカウント
        members = self.src_df.dropna().index.get_level_values(1).unique()
        print(f"members: {len(members)}")

    def draw(self):
        """Draw the selected member's keypoints within the specified timestamp range."""
        current_member = str(self.tree.get_selected_one()[0])

        tar_df = keypoints_proc.filter_by_timerange(self.src_df, self.time_min, self.time_max)
        tar_df = tar_df[~tar_df.index.duplicated(keep="last")]

        idx = tar_df.index
        tar_df.index = tar_df.index.set_levels([idx.levels[0], idx.levels[1], idx.levels[2].astype(str)])

        plot_df = tar_df
        self.band.set_trk_df(plot_df)
        self.band.set_plot_band(plot_df, current_member, self.time_min, self.time_max)
        self.band.draw()

    def update_tree(self):
        """Update the treeview widget with the data from the src_df."""
        self.tree.clear()
        members = self.src_df.index.get_level_values(1).unique()
        tree_df = self.src_df

        for member in members:
            sliced_df = tree_df.loc[pd.IndexSlice[:, member, :], :]
            sliced_df = sliced_df.loc[~(sliced_df["x"].isna()) & (~sliced_df["y"].isna())]
            if len(sliced_df.index.get_level_values(0).unique()) == 0:
                print(f"member {member} has no data")
                continue
            kpf = len(sliced_df) / len(sliced_df.index.get_level_values(0).unique())
            head_timestamp = time_format.msec_to_timestr_with_fff(sliced_df.head(1)["timestamp"].values[0])
            tail_timestamp = time_format.msec_to_timestr_with_fff(sliced_df.tail(1)["timestamp"].values[0])
            duration = sliced_df.tail(1)["timestamp"].values[0] - sliced_df.head(1)["timestamp"].values[0]
            duration_str = time_format.msec_to_timestr_with_fff(duration)
            values = [
                member,
                head_timestamp,
                tail_timestamp,
                duration_str,
                f"{kpf:.2f}",
            ]
            self.tree.insert(values)

    def rename_member(self):
        """Rename a member in the DataFrame."""
        old_member = self.tar_member_label_var.get()
        new_member = self.new_member_name_entry.get()
        if new_member == "":
            print("new member name is empty")
            return
        # self.time_min self.time_maxの間でかつ変更したいmemberを抽出
        start_time, end_time = self.time_span_entry.get_start_end()
        between_sr = self.src_df["timestamp"].between(start_time - 1, end_time + 1)
        tar_member_sr = self.src_df.index.get_level_values(1) == old_member
        rename_sr = between_sr & tar_member_sr
        # new_memberを追加してmemberと入れ替える
        new_member_sr = self.src_df.index.get_level_values(1).where(~rename_sr, new_member)
        self.src_df["new_member"] = new_member_sr
        self.src_df = self.src_df.set_index("new_member", append=True).swaplevel()
        self.src_df = self.src_df.droplevel(level="member").rename_axis(index={"new_member": "member"})

        self.src_df = self.src_df[~self.src_df.index.duplicated(keep="last")]
        self.update_tree()
        print(f"renamed {old_member} to {new_member}")

    def remove_member(self):
        """Remove a member from the DataFrame."""
        current_member = self.tar_member_label_var.get()
        if current_member == "":
            print("current member is empty")
            return
        start_time, end_time = self.time_span_entry.get_start_end()
        between_sr = self.src_df["timestamp"].between(start_time - 1, end_time + 1)
        tar_member_sr = self.src_df.index.get_level_values(1) == current_member
        remove_sr = between_sr & tar_member_sr
        self.src_df = self.src_df[~remove_sr]
        self.update_tree()
        print(f"removed {current_member}")

    def export_tree(self):
        """Export the tree data to a CSV file."""
        base_dict = {"member": [], "start": [], "end": [], "duration": []}
        data = self.tree.tree.get_children()
        for d in data:
            row = self.tree.tree.item(d)["values"]
            base_dict["member"].append(row[0])
            base_dict["start"].append(row[1])
            base_dict["end"].append(row[2])
            base_dict["duration"].append(row[3])
        df = pd.DataFrame(base_dict)
        df.to_csv("member_edit.csv", index=False)

    def on_ok(self):
        """Perform the action when the 'OK' button is clicked."""
        self.dst_df = self.src_df.copy()
        if len(self.dst_df) == 0:
            print("No data in DataFrame")
            self.dst_df = None
        self.master.destroy()

    def cancel(self):
        """Cancel the operation and destroy the window."""
        self.dst_df = None
        self.master.destroy()

    def clear(self):
        """Clear the data in the band."""
        self.band.clear()

    def _select_tree_row(self, event):
        """Handle the selection of a row in the tree."""
        cols = self.tree.get_selected_one()
        if cols is None:
            return
        current_member = str(cols[0])
        self.tar_member_label_var.set(current_member)
        start_msec = time_format.timestr_to_msec(cols[1])
        end_msec = time_format.timestr_to_msec(cols[2])
        self.time_span_entry.update_entry(start_msec, end_msec)

    def _validate(self, text):
        return text.replace(".", "").isdigit() or text == ""
