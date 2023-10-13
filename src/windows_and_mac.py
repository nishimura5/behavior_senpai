import os
import sys
import subprocess


def open_file(filepath):
    '''
    filepathにあるファイルを開く
    '''
    # Windows
    if sys.platform.startswith('win32'):
        subprocess.Popen(['start', filepath], shell=True)
    # Mac
    elif sys.platform.startswith('darwin'):
        subprocess.call(['open', filepath])


def go_to_folder(filepath, samedir):
    '''
    filepathと同じ階層にあるフォルダ(samedir)を開く
    なければfilepathがあるフォルダを開く
    '''
    tar_dir = os.path.join(os.path.dirname(filepath), samedir)
    if os.path.exists(tar_dir) is False:
        tar_dir = os.path.dirname(filepath)
    # Windows
    if sys.platform.startswith('win32'):
        subprocess.Popen(['explorer', tar_dir.replace('/', '\\')], shell=True)
    # Mac
    elif sys.platform.startswith('darwin'):
        subprocess.call(['open', tar_dir])

