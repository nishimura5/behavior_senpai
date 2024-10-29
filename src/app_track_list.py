import glob
import os
import tkinter as tk
from tkinter import messagebox, ttk

import pandas as pd

from behavior_senpai import windows_and_mac
from gui_parts import Combobox, IntEntry, StrEntry


class App(ttk.Frame):
    """
    Trackファイルの一覧を表示するためのGUIです。
    """

    def __init__(self, master, args):
        super().__init__(master)
        master.title("Track List")
        self.pack(padx=14, pady=14)

        self.folder_path = args["pkl_dir"]

        take_part_frame = ttk.Frame(self)
        take_part_frame.pack(pady=5)
        self.take_entry = StrEntry(take_part_frame, label="take:", width=10)
        self.take_entry.pack_horizontal(padx=(0, 10))

        # 文字列でソートする都合で9までに対応、(''も想定しているので10以上に拡張するときは注意)
        vals = ("1", "2", "3", "4", "5", "6", "7", "8", "9")
        self.part_combo = Combobox(take_part_frame, "part:", values=vals, width=5)
        self.part_combo.pack_horizontal(padx=5)
        assign_btn = ttk.Button(take_part_frame, text="Assign", command=self.assign)
        assign_btn.pack(side=tk.LEFT, padx=5)
        overwrite_btn = ttk.Button(take_part_frame, text="Overwrite", command=self.overwrite)
        overwrite_btn.pack(side=tk.LEFT, padx=5)
        merge_btn = ttk.Button(take_part_frame, text="Merge track files", command=self.merge)
        merge_btn.pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(pady=5)
        cols = ("take", "part", "track", "model", "video")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="extended")
        self.tree.heading("take", text="take")
        self.tree.heading("part", text="part")
        self.tree.heading("track", text="track")
        self.tree.heading("model", text="model")
        self.tree.heading("video", text="video")
        self.tree.column("take", width=80)
        self.tree.column("part", width=40)
        # 選択したtrackを取得するためのcommandを設定
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.tree.pack()

        bottom_btn_frame = ttk.Frame(self)
        bottom_btn_frame.pack(pady=10)
        open_btn = ttk.Button(bottom_btn_frame, text="Open", command=self._open_video)
        open_btn.pack(side=tk.LEFT)

        if self.folder_path != "":
            self._load_folder()

    def _load_folder(self):
        for item in self.tree.get_children(""):
            self.tree.delete(item)

        self.src_tl = TrackList()

        trk_paths = glob.glob(os.path.join(self.folder_path, "*.pkl"))
        attr_dict = {}
        for trk_path in trk_paths:
            take, prev_name, next_name = "", None, None
            tar_df = pd.read_pickle(trk_path)
            if "take" in tar_df.attrs.keys():
                take = tar_df.attrs["take"]
            if "next" in tar_df.attrs.keys():
                next_name = tar_df.attrs["next"]
            if "prev" in tar_df.attrs.keys():
                prev_name = tar_df.attrs["prev"]
            attr_dict[os.path.basename(trk_path)] = {"model": tar_df.attrs["model"], "video": tar_df.attrs["video_name"]}
            self.src_tl.append(take, prev_name, next_name, os.path.basename(trk_path))

        take_dict = self.src_tl.get_dict()
        for take in take_dict.keys():
            link_list = take_dict[take]
            for part_num, file_name in link_list.items():
                if take == "":
                    part_num = ""
                attr = attr_dict[file_name]
                if isinstance(attr["video"], list):
                    attr["video"] = attr["video"][0]
                self.tree.insert("", "end", values=(take, part_num, file_name, attr["model"], attr["video"]))

    def _on_select(self, event):
        selected_items = self.tree.selection()
        if len(selected_items) == 0:
            return
        take = self.tree.item(selected_items[0])["values"][0]
        part = self.tree.item(selected_items[0])["values"][1]
        self.take_entry.update(take)
        self.part_combo.set(part)

    def assign(self):
        take = self.take_entry.get()
        part = self.part_combo.get()
        selected_items = self.tree.selection()
        for item in selected_items:
            self.tree.set(item, "take", take)
            self.tree.set(item, "part", part)
        self._treeview_sort_column(self.tree)

    def _treeview_sort_column(self, tv):
        tar_list = [(tv.set(k, "take"), tv.set(k, "part"), k) for k in tv.get_children("")]
        tar_list.sort()
        for index, (_val_take, _val_part, k) in enumerate(tar_list):
            tv.move(k, "", index)

    def _open_video(self):
        video_file_name = self.tree.item(self.tree.selection()[0])["values"][4]
        video_path = os.path.join(self.folder_path, os.pardir, video_file_name)
        windows_and_mac.open_file(video_path)

    def overwrite(self):
        """Overwrite the track information in the pickle files based on the selected values in the treeview."""
        take_part_name_list = []
        for item in self.tree.get_children(""):
            take = self.tree.set(item, "take")
            part = self.tree.set(item, "part")
            file_name = self.tree.set(item, "track")
            take_part_name_list.append({"take": take, "part": part, "name": file_name})
        dst_tl = TrackList()
        dst_tl.set_take_part_name_list(take_part_name_list)
        #        dst_tl.show()
        for take, links in dst_tl.track_dict.items():
            for item in links.link_list:
                src_take, src_item = self.src_tl.find_by_item_name(item.name)
                if take == src_take and item.name == src_item.name and item.prev == src_item.prev and item.next == src_item.next:
                    print(f"same! {item.name} and {src_item.name}")
                elif take == "":
                    tar_df = pd.read_pickle(os.path.join(self.folder_path, item.name))
                    tar_df.attrs["prev"] = None
                    tar_df.attrs["next"] = None
                    tar_df.attrs["take"] = ""
                    tar_df.to_pickle(os.path.join(self.folder_path, item.name))
                else:
                    tar_df = pd.read_pickle(os.path.join(self.folder_path, item.name))
                    tar_df.attrs["prev"] = item.prev
                    tar_df.attrs["next"] = item.next
                    tar_df.attrs["take"] = take
                    tar_df.to_pickle(os.path.join(self.folder_path, item.name))
        print("overwrite done")
        self._load_folder()

    def merge(self):
        """Merge the track files based on the treeview."""
        # open fps dialog
        fps_dialog = FpsDialog(self)
        self.wait_window(fps_dialog)
        if fps_dialog.fps is None:
            return
        self.fps = fps_dialog.fps

        merge_dict = {}
        for item in self.tree.get_children(""):
            take = self.tree.set(item, "take")
            part = self.tree.set(item, "part")
            file_name = self.tree.set(item, "track")
            if take == "":
                continue
            if take not in merge_dict.keys():
                merge_dict[take] = {}
            merge_dict[take][int(part)] = file_name
        for take, part_dict in merge_dict.items():
            part_list = [part_dict[k] for k in sorted(part_dict.keys())]
            if len(part_list) > 1:
                self._merge_track_files(take, part_list)
        messagebox.showinfo("Merge track files", "Merge finished.")

    def close(self):
        pass

    def _merge_track_files(self, take_name, file_name_list):
        dst_df = pd.DataFrame()
        videos = []
        for file_name in file_name_list:
            src_df = pd.read_pickle(os.path.join(self.folder_path, file_name))
            if len(dst_df) == 0:
                dst_df = src_df
                attrs = src_df.attrs
            else:
                prev_max_frame = dst_df.index.get_level_values("frame").max()
                prev_max_timestamp = dst_df["timestamp"].max()
                src_df.index = src_df.index.set_levels(src_df.index.levels[0] + prev_max_frame + 1, level=0)
                src_df["timestamp"] = src_df["timestamp"] + prev_max_timestamp + self.fps

                # old code
                # step = dst_df.groupby(level=1)["timestamp"].diff().max()
                # src_df["timestamp"] = src_df["timestamp"] + prev_max_timestamp + step

                dst_df = pd.concat([dst_df, src_df], axis=0)
            videos.append(src_df.attrs["video_name"])
            # move to backup folder
            os.makedirs(os.path.join(self.folder_path, "backup"), exist_ok=True)
            backup_path = os.path.join(self.folder_path, "backup", file_name)
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(os.path.join(self.folder_path, file_name), backup_path)
        attrs["prev"] = None
        attrs["next"] = None
        attrs["video_name"] = videos
        dst_df.attrs = attrs
        dst_path = os.path.join(self.folder_path, take_name + ".pkl")
        dst_df.to_pickle(dst_path)


class TrackList:
    def __init__(self):
        self.track_dict = {}

    def set_take_part_name_list(self, src_list):
        """
        以下の形のリストを受け取ってtrack_dictを作る
        [{take: xxx, part: 1, name: aaa}, {take: xxx, part: 2, name: bbb}]
        まずtakeで仕分けてからpartがkeyの辞書を作ってset_dict()
        """
        self.track_dict = {}
        new_dict = {}
        for row in src_list:
            take = row["take"]
            part = row["part"]
            name = row["name"]
            if take not in new_dict.keys():
                new_dict[take] = {}
            if part not in new_dict[take].keys():
                new_dict[take][part] = name
            else:
                print("duplicate part")
        for take, part_dict in new_dict.items():
            self.track_dict[take] = LinkList()
            self.track_dict[take].set_dict(part_dict)

    def append(self, take, prev_name, next_name, name):
        """
        track_dictに追加する
        """
        item = LinkItem(name)
        item.prev = prev_name
        item.next = next_name
        if take not in self.track_dict.keys():
            self.track_dict[take] = LinkList()
        self.track_dict[take].append_link_item(item)

    def get_dict(self):
        dst_dict = {}
        for take, links in self.track_dict.items():
            links.sort_links()
            dst_dict[take] = links.get_dict()
        return dst_dict

    def show(self):
        """
        デバッグのprint用
        """
        for take, links in self.track_dict.items():
            print(f"<take: {take}>")
            links.sort_links()
            for item in links.link_list:
                print(item.name, item.prev, item.next)

    def find_by_item_name(self, item_name):
        """
        item_nameからtakeを検索して返す
        """
        for take, links in self.track_dict.items():
            for item in links.link_list:
                if item.name == item_name:
                    return take, item
        return None, None


class LinkList:
    """
    各要素がnextとprevを持っているリスト
    """

    def __init__(self):
        self.link_list = []

    def append_link_item(self, src_item):
        ret = False
        # 重複データがあったら追加しない
        for item in self.link_list:
            if (src_item.prev is not None) and (src_item.prev == item.prev):
                print("duplicate prev")
                return ret
            if (src_item.next is not None) and (src_item.next == item.next):
                print("duplicate next")
                return ret
            if src_item.name == item.name:
                print("duplicate name")
                return ret
        ret = True
        self.link_list.append(src_item)
        return ret

    def sort_links(self):
        # prevがNoneのものを先頭に持ってくる
        for i, item in enumerate(self.link_list):
            if item.prev is None:
                self.link_list.insert(0, self.link_list.pop(i))
        for i, item in enumerate(self.link_list):
            for j, item2 in enumerate(self.link_list):
                if item.name == item2.prev:
                    self.link_list.insert(i + 1, self.link_list.pop(j))
                    break

    def append(self, src_item):
        item = LinkItem(src_item)
        if len(self.link_list) > 0:
            item.prev = self.link_list[-1].name
            self.link_list[-1].next = item.name
        self.link_list.append(item)

    def set_dict(self, src_dict):
        """
        keyでソートしてからappend
        """
        keys = sorted([k for k in src_dict.keys()])
        for key in keys:
            self.append(src_dict[key])

    def get_dict(self):
        """
        link_listをdictに変換して返す
        """
        ret_dict = {}
        for i, item in enumerate(self.link_list):
            ret_dict[str(i + 1)] = item.name
        return ret_dict


class LinkItem:
    def __init__(self, item):
        self.name = item
        self.next = None
        self.prev = None


class FpsDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("FPS")
        self.geometry("200x100")
        self.fps_entry = IntEntry(self, label="fps:", default=29.97, width=10)
        self.fps_entry.pack_vertical(pady=10)
        self.cancel_btn = ttk.Button(self, text="Cancel", command=self.destroy)
        self.cancel_btn.pack(side=tk.LEFT, padx=10)
        self.ok_btn = ttk.Button(self, text="OK", command=self.ok)
        self.ok_btn.pack(pady=10)
        self.fps = None

    def ok(self):
        self.fps = float(self.fps_entry.get())
        self.destroy()
