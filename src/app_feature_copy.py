import ctypes
import json
import os
import sys
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import pandas as pd

import export_mp4
from app_track_list import TrackList
from behavior_senpai import calc_features, df_attrs, feature_proc, hdf_df, vcap, windows_and_mac


class App(ttk.Frame):
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Feature copy")
        self.pack(padx=14, pady=14, fill=tk.BOTH, expand=True)

        self.pkl_dir = args["pkl_dir"]
        self.calc_case = args["calc_case"]
        self.feat_dir = os.path.join(os.path.dirname(self.pkl_dir), "calc", self.calc_case)
        feat_copy_name = "feat_copy" if sys.platform.startswith("win32") else ".feat_copy"
        self.feat_copy_path = os.path.join(self.feat_dir, feat_copy_name)
        self.saved_values = self._load_feat_copy()
        saved_master_feature_path = self.saved_values.get("master_feature_path", "")
        self.master_feature_path = saved_master_feature_path if isinstance(saved_master_feature_path, str) else ""
        self.options_by_item = {}
        self.video_cap = vcap.VideoCap()

        master_feature_frame = ttk.Frame(self)
        master_feature_frame.pack(fill=tk.X, pady=(0, 10))
        master_feature_button = ttk.Button(
            master_feature_frame,
            text="Select feature file",
            command=self._select_master_feature_file,
        )
        master_feature_button.pack(side=tk.LEFT)
        self.master_feature_path_label = ttk.Label(master_feature_frame, text=self.master_feature_path)
        self.master_feature_path_label.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)

        self.execute_button = ttk.Button(
            master_feature_frame,
            text="Execute",
            command=self._execute,
            state=tk.NORMAL if self.master_feature_path != "" else tk.DISABLED,
        )
        self.execute_button.pack(side=tk.LEFT, padx=(5, 0))

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("pkl_name", "video_timestamp", "take", "part", "scene", "member")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("pkl_name", text="pkl_name", command=lambda: self._sort_tree("pkl_name"))
        self.tree.heading("video_timestamp", text="video timestamp")
        self.tree.heading("take", text="take", command=lambda: self._sort_tree("take"))
        self.tree.heading("part", text="part", command=lambda: self._sort_tree("part"))
        self.tree.heading("scene", text="target scene")
        self.tree.heading("member", text="member")
        self.tree.column("pkl_name", width=220, minwidth=160)
        self.tree.column("video_timestamp", width=150, minwidth=120)
        self.tree.column("take", width=100, minwidth=60)
        self.tree.column("part", width=60, minwidth=40)
        self.tree.column("scene", width=100, minwidth=60)
        self.tree.column("member", width=100, minwidth=60)

        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        y_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        x_scrollbar.grid(row=1, column=0, sticky=tk.EW)

        self.context_menu = tk.Menu(self, tearoff=False)
        self.context_menu.add_command(label="Target scene", command=self._edit_selected)
        self.context_menu.add_command(label="Take and Part", command=self._edit_take_and_part)
        self.context_menu.add_command(label="Export MP4", command=self._export_selected_mp4)
        right_click = "<Button-2>" if sys.platform.startswith("darwin") else "<Button-3>"
        self.tree.bind(right_click, self._show_context_menu)

        self._load_folder()

    def _load_folder(self):
        for item in self.tree.get_children(""):
            self.tree.delete(item)
        self.options_by_item = {}

        metadata_by_name = {}
        track_list = TrackList()
        pkl_names = self._get_pkl_names()
        for pkl_name in pkl_names:
            metadata = self._get_metadata(os.path.join(self.pkl_dir, pkl_name))
            metadata_by_name[pkl_name] = metadata
            track_list.append(metadata["take"], metadata["prev"], metadata["next"], pkl_name)

        parts_by_name = {}
        for take, links in track_list.get_dict().items():
            for part, pkl_name in links.items():
                parts_by_name[pkl_name] = "" if take == "" else part

        video_timestamps_changed = False
        for pkl_name in pkl_names:
            metadata = metadata_by_name[pkl_name]
            saved_values = self.saved_values.get(pkl_name, {})
            if not isinstance(saved_values, dict):
                saved_values = {}
            saved_scene = saved_values.get("scene", "")
            scene = "" if saved_scene is None else str(saved_scene)
            members_by_scene = metadata["members_by_scene"]
            member = ", ".join(members_by_scene.get(scene, []))
            saved_video_timestamp = saved_values.get("video_timestamp", "")
            if saved_video_timestamp is None or str(saved_video_timestamp) == "":
                pkl_path = os.path.join(self.pkl_dir, pkl_name)
                video_timestamp = self._get_video_timestamp(pkl_path, metadata["video_names"])
                video_timestamps_changed = True
            else:
                video_timestamp = str(saved_video_timestamp)
            item = self.tree.insert(
                "",
                tk.END,
                values=(pkl_name, video_timestamp, metadata["take"], parts_by_name.get(pkl_name, ""), scene, member),
            )
            self.options_by_item[item] = {
                "scenes": metadata["scenes"],
                "members_by_scene": members_by_scene,
            }

        if video_timestamps_changed:
            try:
                self._save_feat_copy()
            except OSError as error:
                print(f"Could not save video timestamps to feat_copy: {error}")

    def _get_pkl_names(self):
        if not self.pkl_dir or not os.path.isdir(self.pkl_dir):
            return []
        return sorted(
            entry.name
            for entry in os.scandir(self.pkl_dir)
            if entry.is_file() and entry.name.lower().endswith(".pkl")
        )

    def _sort_tree(self, column):
        items = list(self.tree.get_children(""))
        items.sort(key=lambda item: str(self.tree.set(item, column)).casefold())
        for index, item in enumerate(items):
            self.tree.move(item, "", index)

    def _load_feat_copy(self):
        if not os.path.isfile(self.feat_copy_path):
            return {}
        try:
            with open(self.feat_copy_path, encoding="utf-8") as file:
                saved_values = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            print(f"Could not load {self.feat_copy_path}: {error}")
            return {}
        if not isinstance(saved_values, dict):
            print(f"Invalid feat_copy data: {self.feat_copy_path}")
            return {}
        return saved_values

    def _save_feat_copy(self):
        saved_values = {"master_feature_path": self.master_feature_path}
        for item in self.tree.get_children(""):
            pkl_name, video_timestamp, _take, _part, scene, _member = self.tree.item(item)["values"]
            saved_values[str(pkl_name)] = {
                "scene": str(scene),
                "video_timestamp": str(video_timestamp),
            }

        os.makedirs(self.feat_dir, exist_ok=True)
        temp_path = f"{self.feat_copy_path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(saved_values, file, ensure_ascii=False, indent=2)
            if os.path.exists(self.feat_copy_path):
                self._set_feat_copy_hidden_on_windows(False)
            os.replace(temp_path, self.feat_copy_path)
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            finally:
                if os.path.exists(self.feat_copy_path):
                    self._set_feat_copy_hidden_on_windows(True)
        self.saved_values = saved_values

    def _select_master_feature_file(self):
        filetypes = windows_and_mac.file_types([("Feature files", "*.feat")])
        selected_path = filedialog.askopenfilename(
            initialdir=self.feat_dir,
            title="Select feature file",
            filetypes=filetypes,
        )
        if selected_path == "":
            return

        previous_path = self.master_feature_path
        self.master_feature_path = selected_path
        self.master_feature_path_label["text"] = selected_path
        self.execute_button["state"] = tk.NORMAL
        try:
            self._save_feat_copy()
        except OSError as error:
            self.master_feature_path = previous_path
            self.master_feature_path_label["text"] = previous_path
            self.execute_button["state"] = tk.NORMAL if previous_path != "" else tk.DISABLED
            messagebox.showerror("Feature copy", f"Could not save feat_copy.\n{error}", parent=self)

    def _execute(self):
        if not os.path.isfile(self.master_feature_path):
            messagebox.showerror("Feature copy", "Feature file not found.", parent=self)
            return

        master_hdf = hdf_df.DataFrameStorage(self.master_feature_path)
        source_cols = master_hdf.load_mixnorm_source_cols()
        if len(source_cols) == 0:
            messagebox.showerror("Feature copy", "No Mix/Norm definitions found in the selected feature file.", parent=self)
            return

        targets = []
        for item in self.tree.get_children(""):
            pkl_name, _video_timestamp, _take, _part, scene, _member = self.tree.item(item)["values"]
            if str(scene) != "":
                targets.append((str(pkl_name), str(scene)))
        if len(targets) == 0:
            messagebox.showinfo("Feature copy", "No rows have a scene selected.", parent=self)
            return

        completed = []
        failed = []
        self.execute_button["state"] = tk.DISABLED
        try:
            for pkl_name, scene in targets:
                try:
                    self._create_feature_file(pkl_name, scene, source_cols)
                    completed.append(pkl_name)
                except Exception as error:
                    print(f"Feature copy failed: {pkl_name}: {error}")
                    failed.append((pkl_name, str(error)))
        finally:
            self.execute_button["state"] = tk.NORMAL

        if len(failed) == 0:
            messagebox.showinfo("Feature copy", f"Created {len(completed)} feature files.", parent=self)
        else:
            failed_names = "\n".join(name for name, _error in failed)
            messagebox.showwarning(
                "Feature copy",
                f"Created: {len(completed)}\nFailed: {len(failed)}\n\n{failed_names}",
                parent=self,
            )

    def _create_feature_file(self, pkl_name, scene, source_cols):
        pkl_path = os.path.join(self.pkl_dir, pkl_name)
        src_df = pd.read_pickle(pkl_path)
        member = self._get_scene_member(src_df, scene)

        calc_args = {
            "src_df": src_df,
            "pkl_dir": self.pkl_dir,
            "trk_pkl_name": pkl_name,
            "calc_case": self.calc_case,
            "member": member,
        }
        calc_features.execute_calc_features(calc_args)

        feat_name = os.path.splitext(pkl_name)[0] + ".feat"
        feat_path = os.path.join(self.feat_dir, feat_name)
        if not os.path.isfile(feat_path):
            raise FileNotFoundError(f"Feature file was not created: {feat_path}")

        target_hdf = hdf_df.DataFrameStorage(feat_path)
        points_df = target_hdf.load_points_df()
        if points_df is None:
            raise ValueError(f"No points data: {feat_path}")

        scene_ranges = self._get_scene_ranges(src_df, scene)
        mixnorm_df, target_source_cols = self._calculate_mixnorm(points_df, member, scene_ranges, source_cols)
        mixnorm_df.attrs = src_df.attrs
        target_hdf.save_mixnorm_df(mixnorm_df, pkl_name, target_source_cols)

    @classmethod
    def _get_scene_member(cls, src_df, scene):
        scene_table = getattr(src_df, "attrs", {}).get("scene_table", {})
        if not isinstance(scene_table, dict):
            raise ValueError("scene_table is not available.")

        scene_members = cls._get_members_by_scene(scene_table).get(scene, [])
        if len(scene_members) == 0:
            raise ValueError(f"No member is assigned to scene: {scene}")
        if len(scene_members) > 1:
            raise ValueError(f"Multiple members are assigned to scene: {scene}")
        return scene_members[0]

    @staticmethod
    def _get_scene_ranges(src_df, scene):
        src_attrs = df_attrs.DfAttrs(src_df)
        src_attrs.load_scene_table()
        scene_ranges = src_attrs.get_scenes(scene)
        if scene_ranges is None or len(scene_ranges) == 0:
            raise ValueError(f"No time range is assigned to scene: {scene}")
        return scene_ranges

    @staticmethod
    def _calculate_mixnorm(points_df, member, scene_ranges, source_cols):
        points_df = points_df[~points_df.index.duplicated(keep="last")]
        member_values = points_df.index.get_level_values(1).astype(str)
        member_df = points_df.loc[member_values == str(member)].copy()
        if member_df.empty:
            raise ValueError(f"Member not found in feature file: {member}")

        timestamp = member_df["timestamp"].copy()
        in_scene = pd.Series(False, index=member_df.index)
        for start_msec, end_msec in scene_ranges:
            in_scene |= member_df["timestamp"].between(start_msec - 1, end_msec + 1)
        member_df.loc[~in_scene, :] = pd.NA
        calc_df = member_df.drop(columns="timestamp")

        name_and_code = feature_proc.get_calc_codes()
        feature_series = []
        target_source_cols = []
        for source_col in source_cols:
            feature_name, _source_member, col_a, op, col_b, normalize = source_col
            if col_a not in calc_df.columns and col_a != " ":
                print(f"Column not found: {col_a}")
                continue
            if col_b not in calc_df.columns and col_b != " ":
                print(f"Column not found: {col_b}")
                continue
            normalize_code = name_and_code.get(normalize, normalize)
            new_sr = feature_proc.arithmetic_operations(calc_df, op, col_a, col_b)
            new_sr = feature_proc.calc(new_sr, normalize_code)
            feature_series.append(new_sr.rename(str(feature_name)))
            target_source_cols.append([feature_name, str(member), col_a, op, col_b, normalize])

        if len(feature_series) == 0:
            raise ValueError("No Mix/Norm definitions could be applied.")
        mixnorm_df = pd.concat(feature_series, axis=1).sort_index()
        mixnorm_df["timestamp"] = timestamp.reindex(mixnorm_df.index)
        return mixnorm_df, target_source_cols

    def _set_feat_copy_hidden_on_windows(self, hidden):
        if not sys.platform.startswith("win32"):
            return

        get_attributes = ctypes.windll.kernel32.GetFileAttributesW
        get_attributes.argtypes = [ctypes.c_wchar_p]
        get_attributes.restype = ctypes.c_uint32
        set_attributes = ctypes.windll.kernel32.SetFileAttributesW
        set_attributes.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32]
        set_attributes.restype = ctypes.c_int

        file_attributes = get_attributes(self.feat_copy_path)
        if file_attributes == 0xFFFFFFFF:
            raise ctypes.WinError()
        if hidden:
            file_attributes |= 0x02
        else:
            file_attributes &= ~0x02
        if not set_attributes(self.feat_copy_path, file_attributes):
            raise ctypes.WinError()

    @classmethod
    def _get_metadata(cls, pkl_path):
        metadata = {"take": "", "prev": None, "next": None, "scenes": [], "members_by_scene": {}, "video_names": []}
        try:
            src_df = pd.read_pickle(pkl_path)
        except Exception as error:
            print(f"Could not load {pkl_path}: {error}")
            return metadata

        attrs = getattr(src_df, "attrs", {})
        take = attrs.get("take", "")
        metadata["take"] = "" if take is None else str(take)
        metadata["prev"] = attrs.get("prev")
        metadata["next"] = attrs.get("next")
        metadata["video_names"] = cls._as_list(attrs.get("video_name"))

        scene_table = attrs.get("scene_table", {})
        if isinstance(scene_table, dict):
            metadata["scenes"] = cls._unique_strings(scene_table.get("description", []))
            metadata["members_by_scene"] = cls._get_members_by_scene(scene_table)
        return metadata

    @staticmethod
    def _get_video_timestamp(pkl_path, video_names):
        video_dir = os.path.abspath(os.path.join(os.path.dirname(pkl_path), os.pardir))
        for video_name in video_names:
            try:
                video_path = os.fspath(video_name)
            except TypeError:
                continue
            if not os.path.isabs(video_path):
                video_path = os.path.join(video_dir, video_path)
            video_path = os.path.normpath(video_path)
            try:
                file_stat = os.stat(video_path)
            except OSError as error:
                print(f"Could not get video timestamp: {video_path}: {error}")
                continue
            creation_time = getattr(file_stat, "st_birthtime", file_stat.st_ctime)
            video_time = min(creation_time, file_stat.st_mtime)
            return datetime.fromtimestamp(video_time).strftime("%Y-%m-%d %H:%M:%S")
        return ""

    @classmethod
    def _get_members_by_scene(cls, scene_table):
        descriptions = cls._as_list(scene_table.get("description", []))
        members = cls._as_list(scene_table.get("member", []))
        members_by_scene = {}
        for index, description in enumerate(descriptions):
            if description is None or index >= len(members) or members[index] is None:
                continue
            scene = str(description)
            member = str(members[index])
            if scene == "" or member == "":
                continue
            scene_members = members_by_scene.setdefault(scene, [])
            if member not in scene_members:
                scene_members.append(member)
        return members_by_scene

    @staticmethod
    def _as_list(values):
        if values is None:
            return []
        if isinstance(values, (str, int, float)):
            return [values]
        try:
            return list(values)
        except TypeError:
            return [values]

    @classmethod
    def _unique_strings(cls, values):
        unique_values = []
        for value in cls._as_list(values):
            if value is None:
                continue
            value = str(value)
            if value != "" and value not in unique_values:
                unique_values.append(value)
        return unique_values

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item == "":
            return
        if item not in self.tree.selection():
            self.tree.selection_set(item)
        self.tree.focus(item)
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
        return "break"

    def _edit_selected(self):
        selected = self.tree.selection()
        if len(selected) == 0:
            return

        scene_values = self._get_common_scenes(selected)
        scene = self.tree.set(selected[0], "scene") if len(selected) == 1 else ""
        dialog = RowEditDialog(self, scene_values=scene_values, scene=scene)
        self.wait_window(dialog)
        if dialog.result is None:
            return

        scene = dialog.result
        previous_values = {item: list(self.tree.item(item)["values"]) for item in selected}
        if all(scene == self.tree.set(item, "scene") for item in selected):
            return

        for item in selected:
            self.tree.set(item, "scene", scene)
            self.tree.set(item, "member", self._get_member_display(item, scene))

        try:
            self._save_feat_copy()
        except OSError as error:
            for item, values in previous_values.items():
                self.tree.set(item, "scene", values[3])
                self.tree.set(item, "member", values[4])
            messagebox.showerror("Feature copy", f"Could not save feat_copy.\n{error}", parent=self)

    def _edit_take_and_part(self):
        selected = self.tree.selection()
        if len(selected) == 0:
            return

        takes = [self.tree.set(item, "take") for item in selected]
        take = takes[0] if all(value == takes[0] for value in takes[1:]) else ""
        dialog = TakeAndPartDialog(
            self,
            take=take,
            part=self.tree.set(selected[0], "part"),
            part_enabled=len(selected) == 1,
        )
        self.wait_window(dialog)
        if dialog.result is None:
            return

        take = dialog.result["take"]
        part = dialog.result["part"]
        previous_values = {item: list(self.tree.item(item)["values"]) for item in selected}
        track_changed = any(
            take != self.tree.set(item, "take") or (part is not None and part != self.tree.set(item, "part")) for item in selected
        )
        if not track_changed:
            return

        for item in selected:
            self.tree.set(item, "take", take)
            if part is not None:
                self.tree.set(item, "part", part)

        try:
            self._overwrite_track_attrs()
        except Exception as error:
            for item, values in previous_values.items():
                self.tree.item(item, values=values)
            messagebox.showerror("Feature copy", f"Could not update track attrs.\n{error}", parent=self)
            return

        self._load_folder()

    def _overwrite_track_attrs(self):
        rows = []
        used_parts = set()
        for item in self.tree.get_children(""):
            take = self.tree.set(item, "take")
            part = self.tree.set(item, "part")
            pkl_name = self.tree.set(item, "pkl_name")
            if take != "":
                if part == "":
                    raise ValueError(f"Part is not selected: {pkl_name}")
                take_part = (take, part)
                if take_part in used_parts:
                    raise ValueError(f"Duplicate part '{part}' in take '{take}'.")
                used_parts.add(take_part)
            rows.append({"take": take, "part": part, "name": pkl_name})

        track_list = TrackList()
        track_list.set_take_part_name_list([row for row in rows if row["take"] != ""])
        desired_attrs = {row["name"]: ("", None, None) for row in rows if row["take"] == ""}
        for take, links in track_list.track_dict.items():
            for link in links.link_list:
                desired_attrs[link.name] = (take, link.prev, link.next)

        pending_writes = []
        for pkl_name, (take, prev_name, next_name) in desired_attrs.items():
            pkl_path = os.path.join(self.pkl_dir, pkl_name)
            src_df = pd.read_pickle(pkl_path)
            attrs = getattr(src_df, "attrs", {})
            if (attrs.get("take", ""), attrs.get("prev"), attrs.get("next")) == (take, prev_name, next_name):
                continue
            pending_writes.append((pkl_path, src_df, dict(attrs), take, prev_name, next_name))

        completed_writes = []
        try:
            for pkl_path, src_df, original_attrs, take, prev_name, next_name in pending_writes:
                src_df.attrs["take"] = take
                src_df.attrs["prev"] = prev_name
                src_df.attrs["next"] = next_name
                self._write_pickle(src_df, pkl_path)
                completed_writes.append((pkl_path, src_df, original_attrs))
        except Exception:
            for pkl_path, src_df, original_attrs in reversed(completed_writes):
                try:
                    src_df.attrs = original_attrs
                    self._write_pickle(src_df, pkl_path)
                except Exception as rollback_error:
                    print(f"Could not roll back {pkl_path}: {rollback_error}")
            raise

    @staticmethod
    def _write_pickle(src_df, pkl_path):
        temp_path = f"{pkl_path}.tmp"
        try:
            src_df.to_pickle(temp_path)
            os.replace(temp_path, pkl_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _export_selected_mp4(self):
        item = self.tree.focus()
        if item == "":
            selected = self.tree.selection()
            if len(selected) == 0:
                return
            item = selected[0]

        pkl_name = str(self.tree.set(item, "pkl_name"))
        scene = str(self.tree.set(item, "scene"))
        if scene == "":
            messagebox.showinfo("Export MP4", "No scene is selected for this row.", parent=self)
            return

        pkl_path = os.path.join(self.pkl_dir, pkl_name)
        exporter = None
        try:
            src_df = pd.read_pickle(pkl_path)
            scene_ranges = self._get_scene_ranges(src_df, scene)
            cap = self._open_video(src_df, pkl_path)

            exporter = export_mp4.MakeMp4()
            exporter.load(
                {
                    "src_df": src_df,
                    "cap": cap,
                    "pkl_dir": self.pkl_dir,
                    "trk_pkl_name": pkl_name,
                }
            )
            exporter.set_time_ranges(scene_ranges)
            exporter.export()
        except Exception as error:
            print(f"MP4 export failed: {pkl_name}: {error}")
            messagebox.showerror("Export MP4", f"Could not export MP4.\n{error}", parent=self)
        finally:
            if exporter is not None:
                exporter.out.release()

    def _open_video(self, src_df, pkl_path):
        attrs = getattr(src_df, "attrs", {})
        video_names = self._as_list(attrs.get("video_name"))
        if len(video_names) == 0:
            raise ValueError("video_name is not available in pkl attrs.")

        video_dir = os.path.abspath(os.path.join(os.path.dirname(pkl_path), os.pardir))
        video_paths = []
        for video_name in video_names:
            video_path = os.fspath(video_name)
            if not os.path.isabs(video_path):
                video_path = os.path.join(video_dir, video_path)
            video_path = os.path.normpath(video_path)
            if not os.path.isfile(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            video_paths.append(video_path)

        frame_size = attrs.get("frame_size")
        if frame_size is None or len(frame_size) != 2:
            raise ValueError("frame_size is not available in pkl attrs.")

        self.video_cap.set_frame_size(frame_size)
        if len(video_paths) == 1:
            self.video_cap.open_file(video_paths[0])
            cap = self.video_cap
        else:
            cap = vcap.MultiVcap(self.video_cap)
            cap.open_files(video_paths)
        if cap.isOpened() is not True:
            raise OSError(f"Could not open video: {video_paths[0]}")
        return cap

    def _get_common_scenes(self, selected):
        scene_lists = [self.options_by_item[item]["scenes"] for item in selected]
        if len(scene_lists) == 0:
            return []
        return [scene for scene in scene_lists[0] if all(scene in scenes for scenes in scene_lists[1:])]

    def _get_member_display(self, item, scene):
        members_by_scene = self.options_by_item[item]["members_by_scene"]
        return ", ".join(members_by_scene.get(scene, []))

    def close(self):
        self.video_cap.release()


class RowEditDialog(tk.Toplevel):
    def __init__(self, master, scene_values, scene=""):
        super().__init__(master)
        self.title("Edit")
        self.resizable(False, False)
        self.result = None

        edit_frame = ttk.Frame(self)
        edit_frame.pack(padx=20, pady=(20, 10))

        scene_label = ttk.Label(edit_frame, text="Target scene:")
        scene_label.grid(row=0, column=0, padx=(0, 8), pady=5, sticky=tk.E)
        self.scene_combo = ttk.Combobox(edit_frame, state="readonly", width=24)
        self.scene_combo.grid(row=0, column=1, pady=5)
        self.scene_combo["values"] = [""] + scene_values
        self.scene_combo.set(scene)

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=(5, 20))
        ok_button = ttk.Button(button_frame, text="OK", command=self._ok)
        ok_button.pack(side=tk.LEFT, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self._cancel)
        cancel_button.pack(side=tk.LEFT, padx=5)

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.focus_set()

    def _ok(self):
        self.result = self.scene_combo.get()
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class TakeAndPartDialog(tk.Toplevel):
    def __init__(self, master, take="", part="", part_enabled=True):
        super().__init__(master)
        self.title("Take and Part")
        self.resizable(False, False)
        self.result = None

        edit_frame = ttk.Frame(self)
        edit_frame.pack(padx=20, pady=(20, 10))

        take_label = ttk.Label(edit_frame, text="Take:")
        take_label.grid(row=0, column=0, padx=(0, 8), pady=5, sticky=tk.E)
        self.take_entry = ttk.Entry(edit_frame, width=27)
        self.take_entry.grid(row=0, column=1, pady=5)
        self.take_entry.insert(0, take)

        part_label = ttk.Label(edit_frame, text="Part:")
        part_label.grid(row=1, column=0, padx=(0, 8), pady=5, sticky=tk.E)
        part_state = "readonly" if part_enabled else tk.DISABLED
        self.part_combo = ttk.Combobox(edit_frame, state=part_state, width=24)
        self.part_combo.grid(row=1, column=1, pady=5)
        self.part_combo["values"] = [str(value) for value in range(1, 10)]
        self.part_combo.set(part)
        self.part_enabled = part_enabled

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=(5, 20))
        ok_button = ttk.Button(button_frame, text="OK", command=self._ok)
        ok_button.pack(side=tk.LEFT, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self._cancel)
        cancel_button.pack(side=tk.LEFT, padx=5)

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.focus_set()

    def _ok(self):
        self.result = {
            "take": self.take_entry.get(),
            "part": self.part_combo.get() if self.part_enabled else None,
        }
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()
