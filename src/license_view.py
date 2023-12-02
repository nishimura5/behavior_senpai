import tkinter as tk
from tkinter import ttk
import json


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Licenses")
        self.pack(padx=10, pady=10)

        text_frame = ttk.Frame(self)
        text_frame.pack(pady=5)

        self.lic_combo = ttk.Combobox(text_frame, state='readonly')
        # 選択をトリガにtextの内容切り替え
        self.lic_combo.bind('<<ComboboxSelected>>', self._change_text)
        self.lic_combo.pack(side=tk.TOP)
        self.text = tk.Text(text_frame, height=70, width=100)
        self.text.pack()

        # jsonファイルを読み込み
        with open('license.json', 'r') as f:
            json_data = json.load(f)
        
        self.lic_infos = {}
        for row in json_data:
            self.lic_infos[f"{row['Name']}({row['Version']})"] = json.dumps(row, indent=4).replace('\\n', '\n')

        self.lic_combo['values'] = tuple(self.lic_infos.keys())

    def _change_text(self, event):
        self.text.delete(1.0, tk.END)
        self.text.insert(1.0, self.lic_infos[self.lic_combo.get()])


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
