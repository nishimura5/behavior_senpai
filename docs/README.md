# Behavior Senpai v.1.6.0

[pyproject]: https://github.com/nishimura5/behavior_senpai/blob/master/pyproject.toml
[app_detect]: https://github.com/nishimura5/behavior_senpai/blob/master/src/app_detect.py
[app_track_list]: https://github.com/nishimura5/behavior_senpai/blob/master/src/app_track_list.py
[app_trajplot]: https://github.com/nishimura5/behavior_senpai/blob/master/src/app_trajplot.py
[app_points_calc]: https://github.com/nishimura5/behavior_senpai/blob/master/src/app_points_calc.py
[app_feat_mix]: https://github.com/nishimura5/behavior_senpai/blob/master/src/app_feat_mix.py
[app_dimredu]: https://github.com/nishimura5/behavior_senpai/blob/master/src/app_dimredu.py
[gui_parts]: https://github.com/nishimura5/behavior_senpai/blob/master/src/gui_parts.py
[detector_proc]: https://github.com/nishimura5/behavior_senpai/blob/master/src/detector_proc.py
[keypoint_toml]: https://github.com/nishimura5/behavior_senpai/tree/master/src/keypoint

![ScreenShot](https://www.design.kyushu-u.ac.jp/~eigo/behavior_senpai_files/bs_capture_120.jpg)

Behavior Senpai is an application that supports quantitative behavior observation in video observation methods. It converts video files into time-series coordinate data using keypoint detection AI, enabling quantitative analysis and visualization of human behavior.
Behavior Senpai is distinctive in that it permits the utilization of multiple AI models without the necessity for coding. 

 The following AI image processing frameworks/models are supported by Behavior Senpai:
- [YOLO11 Pose](https://docs.ultralytics.com/tasks/pose/)
- [YOLOv8 Pose](https://github.com/ultralytics/ultralytics/issues/1915)
- [MediaPipe Holistic](https://github.com/google/mediapipe/blob/master/docs/solutions/holistic.md)
- [RTMPose Halpe26 (MMPose)](https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose#26-keypoints)
- [RTMW WholeBody133 (MMPose)](https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose#wholebody-2d-133-keypoints)

Behavior Senpai performs pose estimation of a person in a video using an AI model selected by the user, and outputs time-series coordinate data.
(These are variously referred to as "pose estimation", "markerless motion capture", "landmark detection", and so forth, depending on the intended purpose and application.)

Behavior Senpai can import inference results (with .h5 extension) from [DeepLabCut](https://www.mackenziemathislab.org/deeplabcut).

Behavior Senpai is an open source software developed at [Faculty of Design, Kyushu University](https://www.design.kyushu-u.ac.jp/en/home/).

## Install

### Download
Download [BehaviorSenpai160.zip](https://github.com/nishimura5/behavior_senpai/releases/download/v1.6.0/BehaviorSenpai160.zip)

Extract the ZIP file and move the `BehaviorSenpai160` folder to your desired working directory.

### Windows

1. Run `BehaviorSenpai.exe` to start the application
2. Click the "Install" button

**First-time setup:**
- `uv` will be automatically installed if not present
- (Optional) Check "Enable CUDA support" if you want to use MMPose and YOLO
- The initial setup may take several minutes

**Subsequent launches:**
- Simply run `BehaviorSenpai.exe` to start the application

### macOS

1. Install Python 3.11 from [python.org](https://www.python.org/downloads/macos/)
2. Open Terminal and run the following commands:
```bash
   cd your/directory/BehaviorSenpai160
   zsh behavior_senpai_mac.sh
```

**First-time setup:**
- `uv` will be automatically installed if not present
- The initial setup may take several minutes

**Subsequent launches:**
- Run the same command to start the application

## Usage

## Keypoints

### YOLO11 and YOLOv8

<p align="center">
  <img width="24%" alt="Keypoints of body in YOLO" src="https://github.com/nishimura5/behavior_senpai/blob/master/src/img/body_coco.png">
</p>

### RTMPose Halpe26

<p align="center">
  <img width="24%" alt="Keypoints of body in RTMPose Halpe26" src="https://github.com/nishimura5/behavior_senpai/blob/master/src/img/body_halpe26.png">
</p>

### RTMPose WholeBody133

<p align="center">
  <img width="50%" alt="Keypoints of body and hands in RTMPose WholeBody133" src="https://github.com/nishimura5/behavior_senpai/blob/master/src/img/body_wholebody133.png">
</p>

<p align="center">
  <img width="60%" alt="Keypoints of face in RTMPose WholeBody133" src="https://github.com/nishimura5/behavior_senpai/blob/master/src/img/face_wholebody133.png">
</p>

### MediaPipe Holistic

See [here](https://storage.googleapis.com/mediapipe-assets/documentation/mediapipe_face_landmark_fullsize.png) for a document with all IDs.

<p align="center">
  <img width="60%" alt="Keypoints of face in Mediapipe Holistic" src="https://github.com/nishimura5/behavior_senpai/blob/master/src/img/facemesh.png">
</p>
<p align="center">
  <img width="60%" alt="Keypoints of face in Mediapipe Holistic" src="https://github.com/nishimura5/behavior_senpai/blob/master/src/img/facemesh2.png">
</p>

<p align="center">
  <img width="50%" alt="Keypoints of hands in Mediapipe Holistic" src="https://github.com/nishimura5/behavior_senpai/blob/master/src/img/hands.png">
</p>

## Interface

### Folder structure of data

```
observation_jan31     <------- Root directory
├── ABC_cond1.MP4
├── ABC_cond2.MP4
├── XYZ_cond1.MOV
├── XYZ_cond2.MOV
├── calc
│   ├── case1         <------- calc_case subdirectory
│   │   ├── ABC_cond1.feat
│   │   └── XYZ_cond1.feat
│   └── case2
│       └── XYZ_cond_1.feat
└── trk
    ├── ABC_cond1.pkl
    ├── ABC_cond2.pkl
    ├── XYZ_cond1.pkl
    ├── XYZ_cond2.pkl
    └── backup
        └── ABC_cond1.pkl
```

#### Root directory

Each root directory (e.g., "observation_jan31") represents a single series of experiments and serves as the base level of the project's file organization. You can create multiple root directories for different experimental series, and they can be located anywhere on your computer where you have appropriate access permissions. When Behavior Senpai processes videos in a root directory, it automatically creates two essential subdirectories within it: trk/ and calc/. These subdirectory names are fixed and must not be modified under any circumstances.

#### Generated files

Behavior Senpai first generates tracking files (.pkl) from the video files and stores them in the trk directory. These files preserve the video's base name. After tracking files are generated, users can define calc_case names (e.g., "case1", "case2") within Behavior Senpai. Feature files are then stored in these user-defined calc_case subdirectories, inheriting the base name of their source video.

#### Operational guidelines

All videos from a given experimental series should be placed directly in their corresponding root directory. Creating subdirectories for different experimental conditions or participants is not recommended. When naming video files, we recommend either keeping the original camera-generated file names (such as GX010001.MP4) or using custom names that are meaningful for your project management. It is crucial not to rename video files after processing has begun, as all generated files inherit the base name of the source video. Renaming source videos after processing will break these file relationships.

### Track file

The time-series coordinate data resulting from keypoint detection in app_detect.py is stored in a [Pickled Pandas DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_pickle.html). This data is referred to by Behavior Senpai as a "Track file". The Track file is saved in the "trk" folder, which is created in the same directory as the video file where the keypoint detection was performed.
The Track file holds time-series coordinate data in a 3-level-multi-index format. The indexes are designated as "frame" "member", and "keypoint", starting from level 0. "Frame" is an integer, starting from 0, corresponding to the frame number of the video. "Member" and "keypoint" are the identifiers of keypoints detected by the model. The Track file always contains three columns: "x," "y," and "timestamp." "X" and "y" are in pixels, while "timestamp" is in milliseconds.

An illustrative example of a DataFrame stored in the Track file is presented below. It should be noted that the columns may include additional columns such as 'z' and 'conf', contingent on the specifications of the AI model.

|  |  |  | x | y | timestamp |
| - | - | - | - | - | - |
| frame | member | keypoint |  |  |  |
| 0 | 1 | 0 | 1365.023560 | 634.258484 | 0.0 |
|  |  | 1 | 1383.346191 | 610.686951 | 0.0 |
|  |  | 2 | 1342.362061 | 621.434998 | 0.0 |
|  |  | ... | ... | ... | ... |
|  |  | 16 | 1417.897583 | 893.739258 | 0.0 |
|  | 2 | 0 | 2201.367920 | 846.174194 | 0.0 |
|  |  | 1 | 2270.834473 | 1034.986328 | 0.0 |
|  |  | ... | ... | ... | ... |
|  |  | 16 | 2328.100098 | 653.919312 | 0.0 |
| 1 | 1 | 0 | 1365.023560 | 634.258484 | 33.333333 |
|  |  | 1 | 1383.346191 | 610.686951 | 33.333333 |
|  |  | ... | ... | ... | ... |

### Feature file

Behavior Senpai saves features calculated from Track file data in an HDF5 container with the custom `.feat` extension. A Feature file is written with `pandas.HDFStore` (PyTables) in `table` format. The extension is different from `.h5`, but the file itself is a standard HDF5 file containing Pandas objects.

A single Feature file can contain results from several tools. Saving a result replaces the corresponding HDF5 key while preserving the other keys in the file.

#### HDF5 key layout

```text
/
|-- profile
|-- points/
|   |-- df
|   `-- source_cols
|-- traj/
|   `-- df
|-- mixnorm/
|   |-- df
|   `-- source_cols
`-- dimredu/
    |-- df
    |-- source_cols
    |-- params
    `-- features
```

The keys present depend on which tools have been saved. Consumers should inspect the available keys instead of assuming that every key exists.

| HDF5 key | Created by | Contents |
| -------- | ---------- | -------- |
| `/profile` | [app_points_calc.py][app_points_calc] or [app_trajplot.py][app_trajplot] | Source Track file identity. |
| `/points/df` | [app_points_calc.py][app_points_calc] | Features calculated from two or three keypoints. |
| `/points/source_cols` | [app_points_calc.py][app_points_calc] | Definitions used to calculate `/points/df`. |
| `/traj/df` | [app_trajplot.py][app_trajplot] | Coordinates and speed for the selected keypoints. |
| `/mixnorm/df` | [app_feat_mix.py][app_feat_mix] | Features produced by arithmetic operations and normalization. |
| `/mixnorm/source_cols` | [app_feat_mix.py][app_feat_mix] | Definitions used to calculate `/mixnorm/df`. This key can exist before `/mixnorm/df` is saved. |
| `/dimredu/df` | [app_dimredu.py][app_dimredu] | Manually assigned class IDs and class membership flags. |
| `/dimredu/source_cols` | [app_dimredu.py][app_dimredu] | Feature columns selected as input for dimensional reduction. |
| `/dimredu/params` | [app_dimredu.py][app_dimredu] | Dimensional-reduction parameters. |
| `/dimredu/features` | [app_dimredu.py][app_dimredu] | Ordered class names. |

#### Common time-series schema

The `df` keys use a two-level Pandas MultiIndex named `frame` and `member`.

| Field | Description |
| ----- | ----------- |
| `frame` (index level 0) | Zero-based frame number in the source video. |
| `member` (index level 1) | Tracked member ID. Behavior Senpai writes current Feature files with string member IDs. |
| `timestamp` | Position in the source video, in milliseconds. |
| Other columns | Tool-dependent feature values. Missing or incalculable values are stored as `NaN`. |

`/points/df`, `/traj/df`, and `/mixnorm/df` normally contain one row for each available `(frame, member)` pair. `/dimredu/df` contains only the member and frames used for dimensional reduction and may therefore be thinned.

An example of `/points/df` or `/mixnorm/df` is shown below:

|       |        | feat_1   | feat_2   | timestamp |
| ----- | ------ | -------- | -------- | --------- |
| frame | member |          |          |           |
| 0     | 1      | NaN      | 0.050946 | 0.000000  |
| 0     | 2      | 0.065052 | 0.049657 | 0.000000  |
| 1     | 1      | NaN      | 0.064225 | 16.683333 |
| 1     | 2      | 0.050946 | 0.050946 | 16.683333 |
| 2     | 1      | NaN      | 0.065145 | 33.366667 |
| 2     | 2      | 0.061077 | 0.068058 | 33.366667 |
| 3     | 1      | NaN      | 0.049712 | 50.050000 |
| 3     | 2      | 0.052715 | 0.055282 | 50.050000 |
|       | ...    | ...      | ...      | ...       |

#### Profile schema

`/profile` is a two-column DataFrame containing file-level properties.

| Column | Description |
| ------ | ----------- |
| `key` | Property name. Currently `track_name`. |
| `value` | Property value. For `track_name`, this is the source Track filename including its `.pkl` extension. |

The `track_name` value is also used to prevent results from a different Track file from being written to `/mixnorm`.

#### Point-calculation metadata

`/points/source_cols` contains one row per calculation definition.

| Column | Description |
| ------ | ----------- |
| `code` | Calculation type selected in the Points Calculation tool, such as distance, angle, or vector operation. |
| `member` | Member to which the calculation applies. |
| `point_a` | Keypoint ID for point A, stored as a string. |
| `point_b` | Keypoint ID for point B, stored as a string. |
| `point_c` | Keypoint ID for point C, stored as a string. It is empty or the string `None` when the calculation uses only two points. |

One calculation definition can generate more than one column in `/points/df`; for example, a direction calculation generates sine and cosine columns.

#### Feature Mixer metadata

`/mixnorm/source_cols` contains one row per mixed or normalized output feature.

| Column | Description |
| ------ | ----------- |
| `name` | Output column name in `/mixnorm/df`. |
| `member` | Member to which the calculation applies. |
| `col_a` | First input column name. |
| `op` | Arithmetic operator: `+`, `-`, `*`, `/`, or a single space when no second operand is used. |
| `col_b` | Second input column name, or a single space when unused. |
| `normalize` | Normalization or filter selected in the GUI. |

Current `normalize` values are `No normalize`, `Z-score`, `MinMax`, `/180`, `Threshold75%`, `Threshold50%`, `Threshold25%`, `Bandpassfilter`, `Highpassfilter`, and `Lowpassfilter`.

#### Dimensional-reduction data and metadata

`/dimredu/df` has the common `(frame, member)` index and the following columns. The UMAP coordinates used by the GUI are not saved.

| Column | Description |
| ------ | ----------- |
| `class` | Zero-based numeric class ID. Frames without a UMAP result can contain `NaN`. |
| `<class name>` | Boolean membership flag. A column is created for each class that is assigned to at least one frame. |
| `timestamp` | Position in the source video, in milliseconds. |

For example:

|       |        | class | cat_1 | cat_2 | timestamp |
| ----- | ------ | ----- | ----- | ----- | --------- |
| frame | member |       |       |       |           |
| 0     | 1      | 0.0   | True  | False | 0.000000  |
| 0     | 2      | 1.0   | False | True  | 0.000000  |
| 1     | 1      | 0.0   | True  | False | 16.683333 |
| 1     | 2      | 1.0   | False | True  | 16.683333 |
| 2     | 1      | 0.0   | True  | False | 33.366667 |
| 2     | 2      | 1.0   | False | True  | 33.366667 |
| 3     | 1      | 0.0   | True  | False | 50.050000 |
| 3     | 2      | 1.0   | False | True  | 50.050000 |
|       | ...    | ...   | ...   | ...   | ...       |

The related metadata keys have these schemas:

| HDF5 key | Columns | Description |
| -------- | ------- | ----------- |
| `/dimredu/source_cols` | `code` | Input feature column names. |
| `/dimredu/params` | `key`, `value` | `n_neighbors`, `min_dist`, `random`, and `thinning`. All values are stored as strings; `random` contains the seed mode (`random` or `fixed`). |
| `/dimredu/features` | `feat` | Ordered class names. The row number is the class ID used in `/dimredu/df`. |

#### Reading a Feature file

The following example reads the physical datasets directly. The leading slash in a key is optional when passing it to Pandas, but it is included here to match `HDFStore.keys()`.

```python
import pandas as pd

feature_path = "calc/case1/ABC_cond1.feat"

with pd.HDFStore(feature_path, mode="r") as store:
    print(store.keys())

    profile_df = store["/profile"]
    profile = dict(zip(profile_df["key"], profile_df["value"]))

    points_df = store["/points/df"] if "/points/df" in store else None
    mixnorm_df = store["/mixnorm/df"] if "/mixnorm/df" in store else None
    dimredu_df = store["/dimredu/df"] if "/dimredu/df" in store else None
```

Behavior Senpai's `DataFrameStorage.load_points_df()` presents a combined view: when both `/points/df` and `/traj/df` exist, it removes `timestamp` from the trajectory table and joins the two tables by `(frame, member)`. `load_mixnorm_df()` returns `/mixnorm/df` when it exists and otherwise falls back to that combined points/trajectory view.

Feature files currently do not store a schema-version field or the source Track DataFrame's `attrs`. External tools should use `/profile` for the source filename, tolerate absent optional keys, and inspect column names and data types when reading files produced by different Behavior Senpai versions.

### Security considerations

As mentioned above, Behavior Senpai handles pickle format files, and because of the security risks associated with pickle format files, please only open files that you trust (e.g., do not open files from unknown sources that are available on the Internet). (For example, do not try to open files of unknown origin published on the Internet). See [here](https://docs.python.org/3/library/pickle.html) for more information.

### Keypoint definition file

This document describes the TOML configuration file that is generated to [keypoint folder][keypoint_toml] when importing DeepLabCut's keypoint detection results (.h5 files) into Behavior Senpai application.

#### [keypoints] Section
Defines the mapping between keypoint names and their IDs, along with display colors for visualization. While keypoint names are used in the configuration file, Behavior Senpai's GUI displays only the numeric IDs. When importing results from DeepLabCut, keypoint names in the .h5 file are automatically converted to corresponding IDs within Behavior Senpai.

#### [draw] Section
Specifies the rules for drawing keypoints when displaying on screen or generating video output. This section controls which elements are visible and how they are rendered in the visualization.

#### [bones] Section
Defines the rules for drawing lines between keypoints when displaying on screen or generating video output. These lines typically represent connections between detected keypoints to visualize the overall structure.

### Annotated Video file

Behavior Senpai can output videos in mp4 format with detected keypoints drawn on them.

### Temporary file

The application's settings and the path of the most recently loaded Track file are saved as a Pickled dictionary. The file name is "temp.pkl". If this file does not exist, the application automatically generates it (using default values). To reset the settings, delete the "temp.pkl" file. The Temporary file is managed by [gui_parts.py][gui_parts].

## Citation

Please acknowledge and cite the use of this software and its authors when results are used in publications or published elsewhere.

```
Nishimura, E. (2025). Behavior Senpai (Version 1.6) [Computer software]. Kyushu University, https://doi.org/10.48708/7160651
```

```
@misc{behavior-senpai-software,
  title = {Behavior Senpai},
  author = {Nishimura, Eigo},
  year = {2025},
  publisher = {Kyushu University},
  doi = {10.48708/7160651},
  note = {Available at: \url{https://hdl.handle.net/2324/7160651}},
}
```

### Related Documents
[Nishimura, E. Feature-based behavior coding for efficient exploratory analysis using pose estimation. Behav Res 57, 167 (2025). https://doi.org/10.3758/s13428-025-02702-6](https://link.springer.com/article/10.3758/s13428-025-02702-6)

[Sample Videos for Behavioral Observation Using Keypoint Detection Technology](https://hdl.handle.net/2324/7172619)

[Quantitative Behavioral Observation Using Keypoint Detection Technology:
 Towards the Development of a New Behavioral Observation Method through Video Imagery (Japanese article)](https://hdl.handle.net/2324/7170833)
