"""Standalone calculation entry point; never imports the GUI launcher."""

import faulthandler
import pickle
import sys
from pathlib import Path


def main():
    faulthandler.enable()
    # Running this file directly avoids Windows spawn re-importing launcher.py.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from behavior_senpai.keypoints_proc import umap

    with open(sys.argv[1], "rb") as stream:
        src_df, params = pickle.load(stream)
    result = umap(src_df, **params)
    result.to_pickle(sys.argv[2])


if __name__ == "__main__":
    main()
