import pandas as pd
import numpy as np

def calc_dt(src_df, step_frame):
    diff_df = src_df.groupby(level=['member', 'keypoint']).diff(step_frame)**2
    diff_df = pd.DataFrame(np.sqrt(diff_df['x'] + diff_df['y']), columns=['dt'])
    return diff_df



if __name__ == "__main__":
    pd.set_option("display.min_rows",500)
    pd.set_option("display.max_rows",500)

    src_df = pd.read_pickle("C:/Users/a5/Documents/project/python_senpai/src/trk/cup.pkl")
    diff_df = calc_dt(src_df, 1)
    print(diff_df)
