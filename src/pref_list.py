import tkinter as tk
from tkinter import ttk

from gui_parts import TempFile


class App(ttk.Frame):
    """
    Trackファイルの一覧を表示するためのGUIです。
    """
    def __init__(self, master):
        super().__init__(master)
        master.title("Preference List")
        self.pack(padx=10, pady=10)

        entry_frame = ttk.Frame(self)
        entry_frame.pack(pady=5)
        width_label = ttk.Label(entry_frame, text="width:")
        width_label.pack(side=tk.LEFT, padx=(10, 0))
        self.width_entry = ttk.Entry(entry_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.width_entry.pack(side=tk.LEFT, padx=(0, 5))
        height_label = ttk.Label(entry_frame, text="height:")
        height_label.pack(side=tk.LEFT)
        self.height_entry = ttk.Entry(entry_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.height_entry.pack(side=tk.LEFT, padx=(0, 5))
        dpi_label = ttk.Label(entry_frame, text="dpi:")
        dpi_label.pack(side=tk.LEFT)
        self.dpi_entry = ttk.Entry(entry_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.dpi_entry.pack(side=tk.LEFT, padx=(0, 5))

        save_btn = ttk.Button(entry_frame, text="Save", command=self.save)
        save_btn.pack(side=tk.LEFT)

        # tempファイルからwidthとheightを取得
        tmp = TempFile()
        width, height, dpi = tmp.get_window_size()
        self.width_entry.insert(tk.END, str(width))
        self.height_entry.insert(tk.END, str(height))
        self.dpi_entry.insert(tk.END, str(dpi))

    def save(self):
        tmp = TempFile()
        data = tmp.load()
        data['width'] = self.width_entry.get()
        data['height'] = self.height_entry.get()
        data['dpi'] = self.dpi_entry.get()
        tmp.save(data)

    def _validate(self, text):
        return (text.isdigit() or text == "")


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
