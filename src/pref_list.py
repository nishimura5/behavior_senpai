import tkinter as tk
from tkinter import ttk

from gui_parts import TempFile


class App(ttk.Frame):
    """
    Trackファイルの一覧を表示するためのGUIです。
    """
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Preference")
        self.pack(padx=14, pady=14)

        pref_frame = ttk.Frame(self)
        pref_frame.pack()
        top_window_size_frame = ttk.Frame(pref_frame)
        top_window_size_frame.pack(side=tk.TOP, anchor=tk.NW, pady=(0, 5))
        top_height_label = ttk.Label(top_window_size_frame, text="Top preview height:")
        top_height_label.pack(side=tk.LEFT, padx=(10, 0))
        self.top_height_entry = ttk.Entry(top_window_size_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.top_height_entry.pack(side=tk.LEFT, padx=(0, 5))

        graph_size_frame = ttk.Frame(pref_frame)
        graph_size_frame.pack(side=tk.TOP, anchor=tk.NW, pady=5)
        graph_width_label = ttk.Label(graph_size_frame, text="Graph size   width:")
        graph_width_label.pack(side=tk.LEFT, padx=(10, 0))
        self.graph_width_entry = ttk.Entry(graph_size_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.graph_width_entry.pack(side=tk.LEFT, padx=(0, 5))
        graph_height_label = ttk.Label(graph_size_frame, text="height:")
        graph_height_label.pack(side=tk.LEFT)
        self.graph_height_entry = ttk.Entry(graph_size_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.graph_height_entry.pack(side=tk.LEFT, padx=(0, 5))
        dpi_label = ttk.Label(graph_size_frame, text="dpi:")
        dpi_label.pack(side=tk.LEFT)
        self.dpi_entry = ttk.Entry(graph_size_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.dpi_entry.pack(side=tk.LEFT, padx=(0, 5))

        mp4_frame = ttk.Frame(pref_frame)
        mp4_frame.pack(side=tk.TOP, anchor=tk.NW, pady=5)
        mp4_scale_label = ttk.Label(mp4_frame, text="Export mp4 scale:")
        mp4_scale_label.pack(side=tk.LEFT, padx=(10, 0))
        self.mp4_scale_entry = ttk.Entry(mp4_frame, width=5, validate="key", validatecommand=(self.register(self._validate_float), "%P"))
        self.mp4_scale_entry.pack(side=tk.LEFT, padx=(0, 5))

        save_btn = ttk.Button(pref_frame, text="Save", command=self.save)
        save_btn.pack(side=tk.TOP)

        # tempファイルからwidthとheightを取得
        tmp = TempFile()
        width, height, dpi = tmp.get_window_size()
        top_width, top_height = tmp.get_top_window_size()
        mp4_scale = tmp.get_mp4_setting()
        self.top_height_entry.insert(tk.END, str(top_height))
        self.graph_width_entry.insert(tk.END, str(width))
        self.graph_height_entry.insert(tk.END, str(height))
        self.dpi_entry.insert(tk.END, str(dpi))
        self.mp4_scale_entry.insert(tk.END, str(mp4_scale))

    def save(self):
        tmp = TempFile()
        data = tmp.load()
        data['top_height'] = self.top_height_entry.get()
        data['width'] = self.graph_width_entry.get()
        data['height'] = self.graph_height_entry.get()
        data['dpi'] = self.dpi_entry.get()
        data['mp4_scale'] = self.mp4_scale_entry.get()
        tmp.save(data)
        print("saved")

    def _validate(self, text):
        return (text.isdigit() or text == "")

    def _validate_float(self, text):
        return (text.replace(".", "").isdigit() or text == "")


def quit(root):
    root.quit()
    root.destroy()


def main():
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", lambda: quit(root))
    app.mainloop()


if __name__ == "__main__":
    main()
