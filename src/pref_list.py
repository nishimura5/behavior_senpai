import tkinter as tk
from tkinter import ttk

from gui_parts import TempFile


class App(ttk.Frame):
    """
    Trackファイルの一覧を表示するためのGUIです。
    """
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Preference List")
        self.pack(padx=10, pady=10)

        pref_frame = ttk.Frame(self)
        pref_frame.pack()
        window_size_frame = ttk.Frame(pref_frame)
        window_size_frame.pack(side=tk.TOP, pady=5)
        width_label = ttk.Label(window_size_frame, text="width:")
        width_label.pack(side=tk.LEFT, padx=(10, 0))
        self.width_entry = ttk.Entry(window_size_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.width_entry.pack(side=tk.LEFT, padx=(0, 5))
        height_label = ttk.Label(window_size_frame, text="height:")
        height_label.pack(side=tk.LEFT)
        self.height_entry = ttk.Entry(window_size_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.height_entry.pack(side=tk.LEFT, padx=(0, 5))
        dpi_label = ttk.Label(window_size_frame, text="dpi:")
        dpi_label.pack(side=tk.LEFT)
        self.dpi_entry = ttk.Entry(window_size_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.dpi_entry.pack(side=tk.LEFT, padx=(0, 5))

        mp4_frame = ttk.Frame(pref_frame)
        mp4_frame.pack(side=tk.TOP, pady=5)
        mp4_scale_label = ttk.Label(mp4_frame, text="export mp4 scale:")
        mp4_scale_label.pack(side=tk.LEFT, padx=(10, 0))
        self.mp4_scale_entry = ttk.Entry(mp4_frame, width=5, validate="key", validatecommand=(self.register(self._validate_float), "%P"))
        self.mp4_scale_entry.pack(side=tk.LEFT, padx=(0, 5))
 
        save_btn = ttk.Button(pref_frame, text="Save", command=self.save)
        save_btn.pack(side=tk.TOP)

        # tempファイルからwidthとheightを取得
        tmp = TempFile()
        width, height, dpi = tmp.get_window_size()
        mp4_scale = tmp.get_mp4_setting()
        self.width_entry.insert(tk.END, str(width))
        self.height_entry.insert(tk.END, str(height))
        self.dpi_entry.insert(tk.END, str(dpi))
        self.mp4_scale_entry.insert(tk.END, str(mp4_scale))

    def save(self):
        tmp = TempFile()
        data = tmp.load()
        data['width'] = self.width_entry.get()
        data['height'] = self.height_entry.get()
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
