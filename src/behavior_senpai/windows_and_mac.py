import datetime
import os
import shutil
import subprocess
import sys
import tkinter as tk


def open_file(filepath):
    """
    filepathにあるファイルを開く
    filepathがディレクトリ（フォルダ）だったらそれを開く
    """
    # Windows
    if sys.platform.startswith("win32"):
        if os.path.isdir(filepath) is True:
            subprocess.Popen(["explorer", filepath.replace("/", "\\")], shell=True)
        else:
            subprocess.Popen(["start", filepath], shell=True)
    # Mac
    elif sys.platform.startswith("darwin"):
        subprocess.call(["open", filepath])


def go_to_folder(filepath, samedir):
    """
    filepathと同じ階層にあるフォルダ(samedir)を開く
    なければfilepathがあるフォルダを開く
    """
    if os.path.isdir(filepath) is True:
        tar_dir = os.path.join(filepath, samedir)
    else:
        tar_dir = os.path.join(os.path.dirname(filepath), samedir)
    if os.path.exists(tar_dir) is False:
        tar_dir = os.path.dirname(filepath)
    # Windows
    if sys.platform.startswith("win32"):
        subprocess.Popen(["explorer", tar_dir.replace("/", "\\")], shell=True)
    # Mac
    elif sys.platform.startswith("darwin"):
        subprocess.call(["open", tar_dir])


def set_app_icon(root):
    """
    rootにアイコンを設定する
    """
    if sys.platform.startswith("win32"):
        root.iconbitmap(default="./src/img/icon.ico")
    elif sys.platform.startswith("darwin"):
        img = tk.Image("photo", file="./src/img/icon.png")
        root.tk.call("wm", "iconphoto", root._w, img)


def file_types(types):
    """
    return types if platform is not darwin
    On Mac, filedialog.askopenfilename() and filedialog.asksaveasfilename() do not support filetypes
    """
    if sys.platform.startswith("darwin"):
        return []
    else:
        return types


def move_to_videos(filepath, folder_name=""):
    """
    Move the file to the Videos folder.
    """
    datetime_str = datetime.datetime.now().strftime("%Y_%m_%d")
    if sys.platform.startswith("win32"):
        videos_dir = os.path.join(os.path.expanduser("~"), "Videos")
    elif sys.platform.startswith("darwin"):
        videos_dir = os.path.join(os.path.expanduser("~"), "Movies")

    if os.path.exists(videos_dir) is False:
        print(f"{videos_dir} is not found")
        return filepath

    if folder_name != "":
        videos_dir = os.path.join(videos_dir, f"{folder_name}_{datetime_str}")

    os.makedirs(videos_dir, exist_ok=True)

    filename = os.path.basename(filepath)
    new_filepath = os.path.join(videos_dir, filename)

    if os.path.exists(new_filepath):
        print(f"{new_filepath} is already exists")
        return filepath

    print(f"Moving {filepath} to {new_filepath}")
    shutil.copy(filepath, new_filepath)
    if os.path.getsize(filepath) == os.path.getsize(new_filepath):
        os.remove(filepath)
    else:
        print(f"copy error: {filepath} and {new_filepath} size is different")
        os.remove(new_filepath)
        new_filepath = filepath
    return new_filepath
