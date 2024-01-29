import tkinter as tk
from tkinter import ttk

import pandas as pd

from gui_parts import TempFile
from line_plotter import LinePlotter
from python_senpai import time_format
from python_senpai import keypoints_proc


class App(ttk.Frame):
    """
    帯プロット(Band Plot)を描画するためのGUIです。帯プロットは動画内の各フレームでkeypoint検出に成功しているかを可視化するためのグラフです。
    以下の機能を有します
     - 以上の処理で得られたデータをBandPlotterに渡す機能
     - Trackファイルのmember名を変更する機能
    """
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Member Edit")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.band = LinePlotter(fig_size=(width/dpi, height/dpi), dpi=dpi)

        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        # Frameの色を赤にする
        setting_frame = ttk.Frame(control_frame)
        setting_frame.pack(fill=tk.X, expand=True, side=tk.LEFT)

        draw_frame = ttk.Frame(setting_frame)
        draw_frame.pack(pady=5)
        draw_btn = ttk.Button(draw_frame, text="Draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT)
        clear_btn = ttk.Button(draw_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT)

        rename_frame = ttk.Frame(setting_frame)
        rename_frame.pack(pady=5)
        remove_btn = ttk.Button(rename_frame, text="Remove", command=self.remove_member)
        remove_btn.pack(anchor=tk.W, padx=5)
        rename_member_label = ttk.Label(rename_frame, text="Rename Member")
        rename_member_label.pack(side=tk.LEFT, pady=5)
        self.tar_member_label_var = tk.StringVar()
        self.tar_member_label_var.set("None")
        tar_member_label = ttk.Label(rename_frame, textvariable=self.tar_member_label_var)
        tar_member_label.pack(side=tk.LEFT, padx=5)
        to_label = ttk.Label(rename_frame, text="to")
        to_label.pack(side=tk.LEFT, padx=5)
        self.new_member_name_entry = ttk.Entry(rename_frame, width=12)
        self.new_member_name_entry.pack(side=tk.LEFT, padx=5)
        rename_btn = ttk.Button(rename_frame, text="Rename", command=self.rename_member)
        rename_btn.pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.Frame(setting_frame)
        tree_frame.pack(pady=5)
        cols = ("member", "start", "end", "duration", "keypoints/frame")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode="extended")
        self.tree.heading("member", text="member")
        self.tree.heading("start", text="start")
        self.tree.heading("end", text="end")
        self.tree.heading("duration", text="duration")
        self.tree.heading("keypoints/frame", text="keypoints/frame")
        self.tree.column("start", width=100)
        self.tree.column("end", width=100)
        self.tree.column("duration", width=100)
        self.tree.pack()
        # rowを選択したときのイベントを設定
        self.tree.bind("<<TreeviewSelect>>", self._select_tree_row)

        ok_frame = ttk.Frame(control_frame)
        ok_frame.pack(anchor=tk.NE, padx=(20, 0))
        ok_btn = ttk.Button(ok_frame, text="OK", command=self.on_ok)
        ok_btn.pack(pady=(0, 5))
        cancel_btn = ttk.Button(ok_frame, text="Cancel", command=self.cancel)
        cancel_btn.pack()

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)
        self.band.pack(plot_frame)

        self.dst_df = None
        self.history = "member_edit"
        self.load(args)

    def load(self, args):
        self.src_df = args['src_df']
        self.cap = args['cap']
        self.time_min, self.time_max = args['time_span_msec']

        # UIの更新
        self.current_dt_span = None
        self.update_tree()
        self.clear()

        idx = self.src_df.index
        self.src_df.index = self.src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2]])
        self.band.set_vcap(self.cap)

        # memberの数をカウント
        members = self.src_df.dropna().index.get_level_values(1).unique()
        print(f"members: {len(members)}")

    def draw(self):
        # treeから選択した行のmemberを取得
        current_member = str(self.tree.item(self.tree.selection()[0])["values"][0])

        # timestampの範囲を抽出
        tar_df = keypoints_proc.filter_by_timerange(self.src_df, self.time_min, self.time_max)
        # keypointのインデックス値を文字列に変換
        idx = tar_df.index
        tar_df.index = tar_df.index.set_levels([idx.levels[0], idx.levels[1], idx.levels[2].astype(str)])

        plot_df = tar_df
        self.band.set_trk_df(plot_df)
        self.band.set_plot_band(plot_df, current_member, self.time_min, self.time_max)
        self.band.draw()

    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        members = self.src_df.index.get_level_values(1).unique()
        if "roi_left_top" in self.src_df.attrs:
            zero_point = self.src_df.attrs['roi_left_top']
        else:
            zero_point = (0, 0)
        tree_df = keypoints_proc.zero_point_to_nan(self.src_df, zero_point)

        for member in members:
            sliced_df = tree_df.loc[pd.IndexSlice[:, member, :], :]
            sliced_df = sliced_df.loc[~(sliced_df['x'].isna()) & (~sliced_df['y'].isna())]
            if len(sliced_df.index.get_level_values(0).unique()) == 0:
                print(f"member {member} has no data")
                continue
            kpf = len(sliced_df)/len(sliced_df.index.get_level_values(0).unique())
            head_timestamp = time_format.msec_to_timestr_with_fff(sliced_df.head(1)['timestamp'].values[0])
            tail_timestamp = time_format.msec_to_timestr_with_fff(sliced_df.tail(1)['timestamp'].values[0])
            duration = sliced_df.tail(1)['timestamp'].values[0] - sliced_df.head(1)['timestamp'].values[0]
            duration_str = time_format.msec_to_timestr_with_fff(duration)
            self.tree.insert("", "end", values=(member, head_timestamp, tail_timestamp, duration_str, f"{kpf:.2f}"))

    def rename_member(self):
        """
        memberをリネームする、モデルによってはmemberはintで保持されているが、リネーム後はstrになる
        """
        old_member = self.tar_member_label_var.get()
        new_member = self.new_member_name_entry.get()
        if new_member == "":
            print("new member name is empty")
            return
        # indexのtypeを表示
        self.src_df = self.src_df.rename(index={old_member: new_member}, level=1)
        self.update_tree()
        print(f"renamed {old_member} to {new_member}")

    def remove_member(self):
        """
        memberを削除する
        """
        current_member = self.tar_member_label_var.get()
        if current_member == "":
            print("current member is empty")
            return
        # indexのtypeを表示
        self.src_df = self.src_df.drop(current_member, level=1)
        self.update_tree()
        print(f"removed {current_member}")

    def export_tree(self):
        # treeの内容をCSVで出力
        base_dict = {"member": [], "start": [], "end": [], "duration": []}
        data = self.tree.get_children()
        for d in data:
            row = self.tree.item(d)["values"]
            base_dict["member"].append(row[0])
            base_dict["start"].append(row[1])
            base_dict["end"].append(row[2])
            base_dict["duration"].append(row[3])
        df = pd.DataFrame(base_dict)
        df.to_csv("member_edit.csv", index=False)

    def on_ok(self):
        self.dst_df = self.src_df.copy()
        if len(self.dst_df) == 0:
            print("No data in DataFrame")
            self.dst_df = None
        self.master.destroy()

    def cancel(self):
        self.dst_df = None
        self.master.destroy()

    def clear(self):
        self.band.clear()

    def _select_tree_row(self, event):
        # 選択した行のmemberを取得
        if len(self.tree.selection()) == 0:
            return
        current_member = str(self.tree.item(self.tree.selection()[0])["values"][0])
        self.tar_member_label_var.set(current_member)

    def _validate(self, text):
        return (text.replace(".", "").isdigit() or text == "")
