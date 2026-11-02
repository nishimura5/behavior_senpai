import os
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from app_area_filter import thin_by_timestamp
from app_feature_copy import App as FeatureCopy
from behavior_senpai import feature_proc


def signal_frame(fs, duration=120, member="7", offset_ms=0., scale=1.):
    t = np.arange(int(duration * fs)) / fs
    index = pd.MultiIndex.from_arrays([np.arange(len(t)), [member] * len(t)], names=["frame", "member"])
    return pd.DataFrame({"wave": scale * (np.sin(2 * np.pi * .7 * t) + np.sin(2 * np.pi * 4 * t)),
                         "timestamp": offset_ms + t * 1000.}, index=index)


def amplitudes(values, seconds, frequencies):
    mask = (seconds >= 25) & (seconds < seconds.max() - 25)
    t = seconds[mask]
    columns = [np.ones(len(t))]
    for frequency in frequencies:
        columns.extend([np.sin(2 * np.pi * frequency * t), np.cos(2 * np.pi * frequency * t)])
    fit = np.linalg.lstsq(np.column_stack(columns), np.asarray(values)[mask], rcond=None)[0]
    return [np.hypot(fit[i], fit[i + 1]) for i in range(1, len(fit), 2)]


class FilterTimeaxisTests(unittest.TestCase):
    def test_physical_frequency_response_at_60_30_15_hz(self):
        cases = {"bandpass": ([.05, .7, 4.], 1), "highpass": ([.02, .8], 1), "lowpass": ([.08, 2.5], 0)}
        for fs in [60, 30, 15]:
            for code, (frequencies, passed) in cases.items():
                with self.subTest(fs=fs, code=code):
                    frame = signal_frame(fs)
                    seconds = frame["timestamp"].to_numpy() / 1000.
                    wave = sum(np.sin(2 * np.pi * f * seconds) for f in frequencies)
                    series = pd.Series(wave, index=frame.index, name="test")
                    result = feature_proc.calc(series, code, timestamps=frame["timestamp"])
                    gains = amplitudes(result, seconds, frequencies)
                    self.assertAlmostEqual(gains[passed], 1., delta=.025, msg=str(gains))
                    for i, gain in enumerate(gains):
                        if i != passed:
                            self.assertLess(gain, .025, str(gains))
                    pd.testing.assert_index_equal(result.index, series.index)
                    self.assertEqual(result.name, series.name)
                    explicit = feature_proc.calc(series, code, sampling_frequency=fs)
                    np.testing.assert_allclose(result, explicit, atol=1e-7)

    def test_60_to_15_thinning_changes_actual_filter_output(self):
        frame = signal_frame(60)
        track = frame.rename(columns={"wave": "x"})
        track["y"] = 1.
        track["keypoint"] = 0
        track = track.set_index("keypoint", append=True)
        track.attrs["fps"] = 60  # Stale metadata must never override actual timestamps.
        thinned = thin_by_timestamp(track, 15)
        self.assertAlmostEqual(feature_proc.sampling_frequency_from_timestamps(thinned["timestamp"]), 15.)
        np.testing.assert_array_equal(thinned.index.get_level_values("frame"), np.arange(0, len(track), 4))
        pd.testing.assert_series_equal(thinned["timestamp"], track.loc[thinned.index, "timestamp"])
        self.assertEqual(thinned.attrs, track.attrs)
        result = feature_proc.calc(thinned["x"], "bandpass", timestamps=thinned["timestamp"])
        gains = amplitudes(result, thinned["timestamp"].to_numpy() / 1000., [.7, 4.])
        self.assertAlmostEqual(gains[0], 1., delta=.025)
        self.assertLess(gains[1], .025)
        wrong = feature_proc.calc(thinned["x"], "bandpass", sampling_frequency=60.)
        self.assertGreater(np.max(np.abs(result - wrong)), .5)

    def test_members_are_thinned_and_filtered_independently(self):
        a, b = signal_frame(60, member="a"), signal_frame(30, member="b", offset_ms=5., scale=3.)
        combined = pd.concat([a, b]).sort_index()
        thinned = thin_by_timestamp(combined, 15)
        unnamed = combined.copy()
        unnamed.index = unnamed.index.set_names([None, None])
        unnamed_result = thin_by_timestamp(unnamed, 15)
        pd.testing.assert_frame_equal(unnamed_result, thinned.rename_axis([None, None]))
        for member in ["a", "b"]:
            group = thinned.loc[thinned.index.get_level_values("member") == member]
            self.assertAlmostEqual(feature_proc.sampling_frequency_from_timestamps(group["timestamp"]), 15.)
        with self.assertRaisesRegex(feature_proc.FilterInputError, "one member"):
            feature_proc.calc(combined["wave"], "bandpass", timestamps=combined["timestamp"])
        definitions = [["filtered", "source", "wave", " ", " ", "Bandpassfilter"]]
        for member, scale in [("a", 1.), ("b", 3.)]:
            result, _ = FeatureCopy._calculate_mixnorm(combined, member, [(0., 120000.)], definitions)
            gains = amplitudes(result["filtered"], result["timestamp"].to_numpy() / 1000., [.7, 4.])
            self.assertAlmostEqual(gains[0], scale, delta=.025 * scale)
            self.assertLess(gains[1], .025 * scale)
            expected = combined.loc[combined.index.get_level_values("member") == member, "timestamp"]
            pd.testing.assert_series_equal(result["timestamp"], expected)

    def test_separated_scenes_never_share_samples_or_filter_state(self):
        frame = signal_frame(15, duration=240)
        ranges = [(0., 79999.), (160000., 239999.)]
        # Missing values outside the selected scenes are allowed; selected samples are not dropped.
        frame.loc[frame["timestamp"].between(80000., 159999.), "wave"] = np.nan
        result = feature_proc.calc(frame["wave"], "bandpass", timestamps=frame["timestamp"], scene_ranges=ranges)
        for start, end in ranges:
            part = frame.loc[frame["timestamp"].between(start, end)]
            expected = feature_proc.calc(part["wave"], "bandpass", timestamps=part["timestamp"])
            np.testing.assert_allclose(result.loc[part.index], expected)
        self.assertTrue(result.loc[frame["timestamp"].between(80000., 159999.)].isna().all())
        with self.assertRaisesRegex(feature_proc.FilterInputError, "Missing"):
            feature_proc.calc(frame["wave"], "bandpass", timestamps=frame["timestamp"])
        selected = frame.loc[~frame["wave"].isna()]
        with self.assertRaisesRegex(feature_proc.FilterInputError, "gap"):
            feature_proc.calc(selected["wave"], "bandpass", timestamps=selected["timestamp"])
        # CSV's preselected rows also filter each scene independently.
        actual = feature_proc.calc(selected["wave"], "bandpass", timestamps=selected["timestamp"], scene_ranges=ranges)
        np.testing.assert_allclose(actual, result.loc[selected.index])

    def test_invalid_time_values_and_missing_samples_are_rejected(self):
        frame = signal_frame(15, duration=10)
        for kind in ["duplicate", "reversed", "irregular", "missing-time", "missing-value", "infinite", "missing-row"]:
            with self.subTest(kind=kind):
                bad = frame.copy()
                if kind == "duplicate":
                    bad.iloc[10, 1] = bad.iloc[9, 1]
                elif kind == "reversed":
                    bad.iloc[10, 1] = bad.iloc[9, 1] - 1
                elif kind == "irregular":
                    bad.iloc[10, 1] += 5
                elif kind == "missing-time":
                    bad.iloc[10, 1] = np.nan
                elif kind == "missing-value":
                    bad.iloc[10, 0] = np.nan
                elif kind == "infinite":
                    bad.iloc[10, 0] = np.inf
                else:
                    bad = bad.drop(bad.index[10])
                with self.assertRaises(feature_proc.FilterInputError):
                    feature_proc.calc(bad["wave"], "bandpass", timestamps=bad["timestamp"])

    def test_insufficient_samples_nyquist_and_legacy_calls(self):
        frame = signal_frame(15, duration=10)
        with self.assertRaisesRegex(feature_proc.FilterInputError, "no 60 Hz default"):
            feature_proc.calc(frame["wave"], "bandpass")
        for code, count in [("bandpass", 33), ("highpass", 18), ("lowpass", 18)]:
            with self.subTest(code=code):
                short = frame.iloc[:count]
                with self.assertRaisesRegex(feature_proc.FilterInputError, "Too few samples"):
                    feature_proc.calc(short["wave"], code, timestamps=short["timestamp"])
                with self.assertRaisesRegex(feature_proc.FilterInputError, "Too few samples"):
                    feature_proc.calc(frame["wave"], code, timestamps=frame["timestamp"], scene_ranges=[(0., 200.)])
        for code, rate in [("bandpass", 4.), ("highpass", .4), ("lowpass", .8)]:
            with self.subTest(code=code):
                with self.assertRaisesRegex(feature_proc.FilterInputError, "Nyquist"):
                    feature_proc.calc(frame["wave"], code, sampling_frequency=rate)
        with self.assertRaisesRegex(feature_proc.FilterInputError, "disagrees"):
            feature_proc.calc(frame["wave"], "bandpass", timestamps=frame["timestamp"], sampling_frequency=60.)
        with self.assertRaisesRegex(feature_proc.FilterInputError, "index"):
            feature_proc.calc(frame["wave"], "bandpass", timestamps=frame["timestamp"].iloc[::-1])

    def test_small_clock_roundoff_is_allowed_but_nonuniform_thinning_is_rejected(self):
        frame = signal_frame(60)
        rounded = frame["timestamp"] + np.tile([0., .01], len(frame) // 2)
        result = feature_proc.calc(frame["wave"], "bandpass", timestamps=rounded)
        gains = amplitudes(result, frame["timestamp"].to_numpy() / 1000., [.7, 4.])
        self.assertAlmostEqual(gains[0], 1., delta=.025)
        self.assertLess(gains[1], .025)
        # 30 -> 20 fps keeps alternating one/two-frame intervals; no resampling is implied.
        uneven = thin_by_timestamp(signal_frame(30), 20)
        with self.assertRaisesRegex(feature_proc.FilterInputError, "Irregular"):
            feature_proc.calc(uneven["wave"], "bandpass", timestamps=uneven["timestamp"])

    def test_nonfilter_operations_retain_nan_index_and_existing_results(self):
        values = pd.Series([2., np.nan, 5., 9.], name="sample")
        expected = {"minmax": (values - values.min()) / (values.max() - values.min()),
                    "zscore": (values - values.mean()) / values.std(), "/180": values / 180.,
                    "thresh25": (values > values.quantile(.25)).astype(int),
                    "thresh50": (values > values.median()).astype(int),
                    "thresh75": (values > values.quantile(.75)).astype(int), "non": values}
        for code, result in expected.items():
            pd.testing.assert_series_equal(feature_proc.calc(values, code), result)
        df = pd.DataFrame({"a": values, "b": values * 2})
        for op in ["+", "-", "*", "/", " "]:
            result = feature_proc.arithmetic_operations(df, op, "a", "b")
            expected = {"+": df.a + df.b, "-": df.a - df.b, "*": df.a * df.b, "/": df.a / df.b, " ": df.a}[op]
            pd.testing.assert_series_equal(result, expected)


if __name__ == "__main__":
    unittest.main()
