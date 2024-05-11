import tkinter as tk
from tkinter import ttk

from gui_parts import IntEntry, TempFile


class App(ttk.Frame):
    """
    Trackファイルの一覧を表示するためのGUIです。
    """
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Preference")
        self.pack(padx=14, pady=14)

        # tempファイルからwidthとheightを取得
        tmp = TempFile()
        width, height, dpi = tmp.get_window_size()
        top_width, top_height = tmp.get_top_window_size()
        mp4_scale = tmp.get_mp4_setting()

        pref_frame = ttk.Frame(self)
        pref_frame.pack()
        self.top_height_entry = IntEntry(pref_frame, label="Top preview height:", default=top_height)
        self.top_height_entry.pack_vertical(pady=5, anchor=tk.W)
        graph_size_frame = ttk.Frame(pref_frame)
        graph_size_frame.pack(side=tk.TOP, anchor=tk.NW, pady=5)
        self.graph_width_entry = IntEntry(graph_size_frame, label="Graph size   width:", default=width)
        self.graph_width_entry.pack_horizontal(padx=5)
        self.graph_height_entry = IntEntry(graph_size_frame, label="height:", default=height)
        self.graph_height_entry.pack_horizontal(padx=5)
        self.dpi_entry = IntEntry(graph_size_frame, label="dpi:", default=dpi)
        self.dpi_entry.pack_horizontal(padx=5)

        mp4_frame = ttk.Frame(pref_frame)
        mp4_frame.pack(side=tk.TOP, anchor=tk.NW, pady=5)
        mp4_scale_label = ttk.Label(mp4_frame, text="Export mp4 scale:")
        mp4_scale_label.pack(side=tk.LEFT, padx=(10, 0))
        self.mp4_scale_entry = ttk.Entry(mp4_frame, width=5, validate="key", validatecommand=(self.register(self._validate_float), "%P"))
        self.mp4_scale_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.mp4_scale_entry.insert(tk.END, mp4_scale)

        save_btn = ttk.Button(pref_frame, text="Save", command=self.save)
        save_btn.pack(side=tk.TOP)

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
