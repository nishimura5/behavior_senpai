import pandas as pd
from scipy.signal import butter, filtfilt


def get_calc_codes():
    """key = display name, value = code"""
    return {
        "No normalize": "non",
        "Z-score": "zscore",
        "MinMax": "minmax",
        "0-180": "0-180",
        "Threshold75%": "thresh75",
        "Threshold50%": "thresh50",
        "Threshold25%": "thresh25",
        "Bandpassfilter": "bandpass",
        "Highpassfilter": "highpass",
        "Lowpassfilter": "lowpass",
    }


def calc(tar_sr, calc_code):
    ret_sr = None
    if calc_code == "minmax":
        ret_sr = (tar_sr - tar_sr.min()) / (tar_sr.max() - tar_sr.min())
    elif calc_code == "zscore":
        ret_sr = (tar_sr - tar_sr.mean()) / tar_sr.std()
    elif calc_code == "0-180":
        ret_sr = tar_sr / 180
    elif calc_code == "thresh50":
        ret_sr = tar_sr > tar_sr.median()
        ret_sr = ret_sr.astype(int)
    elif calc_code == "thresh75":
        ret_sr = tar_sr > tar_sr.quantile(0.75)
        ret_sr = ret_sr.astype(int)
    elif calc_code == "thresh25":
        ret_sr = tar_sr > tar_sr.quantile(0.25)
        ret_sr = ret_sr.astype(int)
    elif calc_code == "bandpass":
        valid_sr = tar_sr.dropna()
        ret_sr = bandpass_filter(valid_sr, 0.2, 2, 60)
        ret_sr = pd.Series(ret_sr, index=valid_sr.index)
        ret_sr = ret_sr.reindex(tar_sr.index)
    elif calc_code == "highpass":
        valid_sr = tar_sr.dropna()
        ret_sr = highpass_filter(valid_sr, 0.2, 60)
        ret_sr = pd.Series(ret_sr, index=valid_sr.index)
        ret_sr = ret_sr.reindex(tar_sr.index)
    elif calc_code == "lowpass":
        valid_sr = tar_sr.dropna()
        ret_sr = lowpass_filter(valid_sr, 0.4, 60)
        ret_sr = pd.Series(ret_sr, index=valid_sr.index)
        ret_sr = ret_sr.reindex(tar_sr.index)
    else:
        ret_sr = tar_sr
    return ret_sr


def arithmetic_operations(tar_df, op, col_a, col_b):
    data_a = tar_df[col_a]
    if op == "+":
        data_b = tar_df[col_b]
        new_sr = data_a + data_b
    elif op == "-":
        data_b = tar_df[col_b]
        new_sr = data_a - data_b
    elif op == "*":
        data_b = tar_df[col_b]
        new_sr = data_a * data_b
    elif op == "/":
        data_b = tar_df[col_b]
        new_sr = data_a / data_b
    elif op == " ":
        new_sr = data_a
    else:
        print("invalid operation")
        None
    return new_sr


def bandpass_filter(tar_sr, lowcut, highcut, fs, order=5):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype="band")
    return filtfilt(b, a, tar_sr)


def highpass_filter(tar_sr, lowcut, fs, order=5):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    b, a = butter(order, low, btype="high")
    return filtfilt(b, a, tar_sr)


def lowpass_filter(tar_sr, highcut, fs, order=5):
    nyquist = 0.5 * fs
    high = highcut / nyquist
    b, a = butter(order, high, btype="low")
    return filtfilt(b, a, tar_sr)
