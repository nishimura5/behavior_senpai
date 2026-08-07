import ctypes
import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd

import export_mp4
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

        columns = ("pkl_name", "take", "scene")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("pkl_name", text="pkl_name", command=lambda: self._sort_tree("pkl_name"))
        self.tree.heading("take", text="take", command=lambda: self._sort_tree("take"))
        self.tree.heading("scene", text="scene")
        self.tree.column("pkl_name", width=320, minwidth=160)
        self.tree.column("take", width=140, minwidth=80)
        self.tree.column("scene", width=180, minwidth=100)

        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        y_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        x_scrollbar.grid(row=1, column=0, sticky=tk.EW)

        self.context_menu = tk.Menu(self, tearoff=False)
        self.context_menu.add_command(label="Edit", command=self._edit_selected)
        self.context_menu.add_command(label="Export MP4", command=self._export_selected_mp4)
        right_click = "<Button-2>" if sys.platform.startswith("darwin") else "<Button-3>"
        self.tree.bind(right_click, self._show_context_menu)

        self._load_folder()

    def _load_folder(self):
        for pkl_name in self._get_pkl_names():
            metadata = self._get_metadata(os.path.join(self.pkl_dir, pkl_name))
            saved_values = self.saved_values.get(pkl_name, {})
            if not isinstance(saved_values, dict):
                saved_values = {}
            saved_scene = saved_values.get("scene", "")
            scene = "" if saved_scene is None else str(saved_scene)
            item = self.tree.insert("", tk.END, values=(pkl_name, metadata["take"], scene))
            self.options_by_item[item] = {
                "scenes": metadata["scenes"],
            }

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
            pkl_name, _take, scene = self.tree.item(item)["values"]
            saved_values[str(pkl_name)] = {
                "scene": str(scene),
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
            pkl_name, _take, scene = self.tree.item(item)["values"]
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

        descriptions = cls._as_list(scene_table.get("description", []))
        members = cls._as_list(scene_table.get("member", []))
        scene_members = []
        for index, description in enumerate(descriptions):
            if str(description) != scene or index >= len(members):
                continue
            member = str(members[index])
            if member != "" and member not in scene_members:
                scene_members.append(member)
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
        metadata = {"take": "", "scenes": []}
        try:
            src_df = pd.read_pickle(pkl_path)
        except Exception as error:
            print(f"Could not load {pkl_path}: {error}")
            return metadata

        attrs = getattr(src_df, "attrs", {})
        metadata["take"] = attrs.get("take", "")

        scene_table = attrs.get("scene_table", {})
        if isinstance(scene_table, dict):
            metadata["scenes"] = cls._unique_strings(scene_table.get("description", []))
        return metadata

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
        dialog = RowEditDialog(
            self,
            scene_values=scene_values,
            scene=scene,
        )
        self.wait_window(dialog)
        if dialog.result is None:
            return

        scene = dialog.result
        previous_values = {item: list(self.tree.item(item)["values"]) for item in selected}
        changed_items = [item for item in selected if scene != self.tree.set(item, "scene")]
        if len(changed_items) == 0:
            return

        for item in changed_items:
            self.tree.set(item, "scene", scene)
        try:
            self._save_feat_copy()
        except OSError as error:
            for item, values in previous_values.items():
                self.tree.item(item, values=values)
            messagebox.showerror("Feature copy", f"Could not save feat_copy.\n{error}", parent=self)

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

        scene_label = ttk.Label(edit_frame, text="Scene:")
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
