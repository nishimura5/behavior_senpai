import pandas as pd
import numpy as np


def calc_speed(src_df, step_frame):
    diff_df = src_df.groupby(level=['member', 'keypoint']).diff(step_frame)**2
    diff_df = pd.DataFrame(np.sqrt(diff_df['x'] + diff_df['y']), columns=[f'dt_{step_frame}'])
    return diff_df


if __name__ == "__main__":
    pd.set_option("display.min_rows", 500)
    pd.set_option("display.max_rows", 500)

    src_df = pd.read_pickle("trk/cup.pkl")
    diff_df = calc_dt(src_df, 1)
    print(diff_df)
