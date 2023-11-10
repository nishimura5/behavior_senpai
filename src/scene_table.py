import os
import tkinter as tk
from tkinter import ttk


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Scene table")
        self.pack(padx=10, pady=10)

        setting_frame = ttk.Frame(self)
        setting_frame.pack(pady=5)

        caption_time = tk.Label(setting_frame, text='time:')
        caption_time.pack(side=tk.LEFT, padx=(10, 0))
        self.time_min_entry = ttk.Entry(setting_frame, width=12)
        self.time_min_entry.pack(side=tk.LEFT)
        nyoro_time = tk.Label(setting_frame, text='～')
        nyoro_time.pack(side=tk.LEFT, padx=1)
        self.time_max_entry = ttk.Entry(setting_frame, width=12)
        self.time_max_entry.pack(side=tk.LEFT, padx=(0, 5))


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
