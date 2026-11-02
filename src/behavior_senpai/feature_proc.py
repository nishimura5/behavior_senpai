import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt


class FilterInputError(ValueError):
    """An input cannot safely be treated as a uniformly sampled single-member signal."""


def get_calc_codes():
    """key = display name, value = code"""
    return {
        "No normalize": "non",
        "Z-score": "zscore",
        "MinMax": "minmax",
        "/180": "/180",
        "Threshold75%": "thresh75",
        "Threshold50%": "thresh50",
        "Threshold25%": "thresh25",
        "Bandpassfilter": "bandpass",
        "Highpassfilter": "highpass",
        "Lowpassfilter": "lowpass",
    }


def calc(tar_sr, calc_code, *, timestamps=None, sampling_frequency=None, scene_ranges=None):
    """Filter using milliseconds or an explicitly supplied Hz rate; never infer from row numbers.

    Each selected scene is independent. Missing values and timing gaps within a scene
    are rejected, not dropped or interpolated. Non-filter operations retain their behavior.
    """
    ret_sr = None
    if calc_code == "minmax":
        ret_sr = (tar_sr - tar_sr.min()) / (tar_sr.max() - tar_sr.min())
    elif calc_code == "zscore":
        ret_sr = (tar_sr - tar_sr.mean()) / tar_sr.std()
    elif calc_code == "/180":
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
    elif calc_code in ("bandpass", "highpass", "lowpass"):
        ret_sr = _filter_series(tar_sr, calc_code, timestamps, sampling_frequency, scene_ranges)
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


def _positive_frequency(fs):
    try:
        fs = float(fs)
    except (TypeError, ValueError) as error:
        raise FilterInputError("Sampling frequency must be supplied explicitly in Hz, or inferred from timestamps in milliseconds.") from error
    if not np.isfinite(fs) or fs <= 0:
        raise FilterInputError("Sampling frequency must be finite and greater than zero (Hz).")
    return fs


def sampling_frequency_from_timestamps(timestamps):
    """Return effective Hz for a finite, increasing, uniform millisecond time axis.

    Maximum deviation from the median interval: 1% plus 1e-6 ms roundoff.
    This intentionally rejects missing frames, timing gaps and nonuniform thinning.
    """
    try:
        times = np.asarray(timestamps, dtype=float)
    except (TypeError, ValueError) as error:
        raise FilterInputError("Timestamps must be numeric milliseconds.") from error
    if times.ndim != 1 or not np.isfinite(times).all():
        raise FilterInputError("Timestamps must be finite numbers in milliseconds; missing times are not supported.")
    if len(times) < 2:
        raise FilterInputError("At least two timestamps are required to determine sampling frequency.")
    intervals = np.diff(times)
    if np.any(intervals <= 0):
        raise FilterInputError("Timestamps must be strictly increasing for each member; duplicate or reversed times are not supported.")
    interval = np.median(intervals)
    if not np.allclose(intervals, interval, rtol=0.01, atol=1e-6):
        raise FilterInputError("Irregular timestamps or a timing gap within a scene: intervals must agree within 1%. No interpolation is performed.")
    return 1000.0 / interval


def _scene_intervals(scene_ranges):
    """Merge overlapping ranges only; separated scenes must never share filter state."""
    merged = []
    for start, end in sorted(scene_ranges):
        if not np.isfinite([start, end]).all() or start > end:
            raise FilterInputError("Scene ranges must have finite start <= end times in milliseconds.")
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def _filter_series(series, code, timestamps, fs, scene_ranges):
    if isinstance(series.index, pd.MultiIndex):
        member_level = "member" if "member" in series.index.names else 1
        if series.index.get_level_values(member_level).nunique(dropna=False) != 1:
            raise FilterInputError("Filter one member at a time; samples from different members must not be mixed.")
    if fs is not None:
        fs = _positive_frequency(fs)
    if timestamps is None:
        if fs is None:
            raise FilterInputError(
                "Filtering requires timestamps in milliseconds or an explicit sampling_frequency in Hz; there is no 60 Hz default."
            )
        if scene_ranges is not None:
            raise FilterInputError("Scene selection requires timestamps in milliseconds.")
        times = None
        segments = [np.arange(len(series))]
    else:
        if isinstance(timestamps, pd.Series) and not timestamps.index.equals(series.index):
            raise FilterInputError("Timestamp index must exactly match the feature index.")
        try:
            times = np.asarray(timestamps, dtype=float)
        except (TypeError, ValueError) as error:
            raise FilterInputError("Timestamps must be numeric milliseconds.") from error
        if times.ndim != 1 or len(times) != len(series) or not np.isfinite(times).all():
            raise FilterInputError("Every feature sample must have a finite timestamp in milliseconds.")
        if np.any(np.diff(times) <= 0):
            raise FilterInputError("Timestamps must be strictly increasing for each member; duplicate or reversed times are not supported.")
        segments = [np.arange(len(series))] if scene_ranges is None else [
            np.flatnonzero((times >= start) & (times <= end)) for start, end in _scene_intervals(scene_ranges)
        ]
    result = pd.Series(np.nan, index=series.index, name=series.name)
    functions = {"bandpass": lambda x, rate: bandpass_filter(x, 0.2, 2., rate),
                 "highpass": lambda x, rate: highpass_filter(x, 0.2, rate),
                 "lowpass": lambda x, rate: lowpass_filter(x, 0.4, rate)}
    if not any(len(segment) for segment in segments):
        raise FilterInputError("No samples are available in the selected scenes.")
    for segment in segments:
        if not len(segment):
            continue
        rate = sampling_frequency_from_timestamps(times[segment]) if times is not None else fs
        if fs is not None and not np.isclose(rate, fs, rtol=0.01):
            raise FilterInputError(f"Explicit sampling frequency {fs:g} Hz disagrees with timestamps ({rate:g} Hz).")
        try:
            result.iloc[segment] = functions[code](series.iloc[segment], rate)
        except FilterInputError as error:
            start = f" at {times[segment[0]]:g} ms" if times is not None else ""
            raise FilterInputError(f"{code}, segment{start}: {error}") from error
    return result


def _apply_filter(values, cutoff, fs, btype, order):
    fs = _positive_frequency(fs)
    cuts = np.atleast_1d(cutoff).astype(float)
    if not np.isfinite(cuts).all() or np.any(cuts <= 0) or np.any(cuts >= fs / 2) or np.any(np.diff(cuts) <= 0):
        raise FilterInputError(f"Cutoff {cutoff} Hz must be positive, ordered and below Nyquist {fs / 2:g} Hz (sampling {fs:g} Hz).")
    try:
        values = np.asarray(values, dtype=float)
    except (ValueError, TypeError) as error:
        raise FilterInputError("Filter samples must be numeric; missing values are not supported within a scene.") from error
    if values.ndim != 1 or not np.isfinite(values).all():
        raise FilterInputError("Missing or infinite feature values within a scene are not supported. No samples are dropped or interpolated.")
    # Second-order sections avoid numerical instability for low cutoffs at high sample rates.
    sos = butter(order, cutoff, btype=btype, fs=fs, output="sos")
    padlen = 3 * (2 * len(sos) + 1 - min((sos[:, 2] == 0).sum(), (sos[:, 5] == 0).sum()))
    if len(values) <= padlen:
        raise FilterInputError(f"Too few samples in a continuous scene: need at least {padlen + 1}, got {len(values)} (sampling {fs:g} Hz).")
    return sosfiltfilt(sos, values, padlen=padlen)


def bandpass_filter(tar_sr, lowcut, highcut, fs, order=5):
    return _apply_filter(tar_sr, [lowcut, highcut], fs, "bandpass", order)


def highpass_filter(tar_sr, lowcut, fs, order=5):
    return _apply_filter(tar_sr, lowcut, fs, "highpass", order)


def lowpass_filter(tar_sr, highcut, fs, order=5):
    return _apply_filter(tar_sr, highcut, fs, "lowpass", order)
