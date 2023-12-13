import os
from tkinter import filedialog


def save_pkl(dst_dir, file_name, dst_df, proc_history=None):
    if proc_history is not None:
        if 'proc_history' not in dst_df.attrs.keys():
            dst_df.attrs['proc_history'] = ['vector']
        else:
            dst_df.attrs['proc_history'].append('vector')
    os.makedirs(dst_dir, exist_ok=True)
    file_name = filedialog.asksaveasfilename(
        title="Save as",
        filetypes=[("pickle", ".pkl")],
        initialdir=dst_dir,
        initialfile=file_name,
        defaultextension="pkl"
    )
    dst_df.to_pickle(file_name)
    print("export() done.")
