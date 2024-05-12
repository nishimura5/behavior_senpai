import json
import os
import sys
import tkinter as tk
from tkinter import ttk


class App(ttk.Frame):
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Licenses")
        self.pack(padx=10, pady=10)

        text_frame = ttk.Frame(self)
        text_frame.pack(pady=5)

        self.lic_combo = ttk.Combobox(text_frame, state='readonly', width=100)
        # 選択をトリガにtextの内容切り替え
        self.lic_combo.bind('<<ComboboxSelected>>', self._change_text)
        self.lic_combo.pack(side=tk.TOP, pady=5)
        self.text = tk.Text(text_frame, height=70, width=100)
        self.text.pack()

        # jsonファイルを読み込み
        data_dir = self._find_data_dir()
        with open(os.path.join(data_dir, 'license.json'), 'r') as f:
            json_data = json.load(f)

        self.lic_infos = {}
        for row in json_data:
            self.lic_infos[f"{row['Name']}({row['Version']})"] = json.dumps(row, indent=4).replace('\\n', '\n')

        self.lic_combo['values'] = tuple(self.lic_infos.keys())
        self.lic_combo.current(0)
        self.text.delete(1.0, tk.END)
        self.text.insert(1.0, self.lic_infos[self.lic_combo.get()])

    def _change_text(self, event):
        self.text.delete(1.0, tk.END)
        self.text.insert(1.0, self.lic_infos[self.lic_combo.get()])

    def _find_data_dir(self):
        if getattr(sys, "frozen", False):
            # The application is frozen
            datadir = os.path.dirname(sys.executable)
        else:
            # The application is not frozen
            # Change this bit to match where you store your data files:
            datadir = os.path.dirname(__file__)
        return datadir


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
