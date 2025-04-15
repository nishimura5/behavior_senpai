# Behavior Senpai v.1.5.1

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

![ScreenShot](https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20v.1.4.0%20_%20Python%20senpai_files/bs_capture_120.jpg)

Behavior Senpai is an application that supports quantitative behavior observation in video observation methods. It converts video files into time-series coordinate data using keypoint detection AI, enabling quantitative analysis and visualization of human behavior.
Behavior Senpai is distinctive in that it permits the utilization of multiple AI models without the necessity for coding. 

 The following AI image processing frameworks/models are supported by Behavior Senpai:
- [YOLO11 Pose](https://docs.ultralytics.com/tasks/pose/)
- [YOLOv8 Pose](https://github.com/ultralytics/ultralytics/issues/1915)
- [MediaPipe Holistic](https://github.com/google/mediapipe/blob/master/docs/solutions/holistic.md)
- [RTMPose Halpe26 (MMPose)](https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose#26-keypoints)
- [RTMPose WholeBody133 (MMPose)](https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose#wholebody-2d-133-keypoints)

Behavior Senpai performs pose estimation of a person in a video using an AI model selected by the user, and outputs time-series coordinate data.
(These are variously referred to as "pose estimation", "markerless motion capture", "landmark detection", and so forth, depending on the intended purpose and application.)

BehaviorSenpai can import inference results (with .h5 extension) from [DeepLabCut](https://www.mackenziemathislab.org/deeplabcut).

Behavior Senpai is an open source software developed at [Faculty of Design, Kyushu University](https://www.design.kyushu-u.ac.jp/en/home/).

## Requirement

In order to use Behavior Senpai, you need a PC that meets the following performance requirements. The functionality has been confirmed on Windows 11 (23H2).

### When using CUDA

 - Disk space: 12GB or more
 - RAM: 16GB or more
 - Screen resolution: 1920x1080 or higher
 - GPU: RTX3060~ (and its [drivers](https://www.nvidia.com/download/index.aspx))

### Without CUDA

If you do not have a CUDA-compatible GPU, only MediaPipe Holistic can be used.

 - Disk space: 8GB or more
 - RAM: 16GB or more
 - Screen resolution: 1920x1080 or higher

## Usage

### Download

Download [BehaviorSenpai150.zip](https://github.com/nishimura5/behavior_senpai/releases/download/v1.5.0/BehaviorSenpai150.zip)

### Install

Running BehaviorSenpai.exe will start the application; if you want to use CUDA, check the "Enable features using CUDA" checkbox the first time you start the application and click the "OK" button.

BehaviorSenpai.exe is an application to automate the construction of the Python environment by [uv](https://docs.astral.sh/uv/) and the startup of Behavior Senpai itself.
The initial setup by BehaviorSenpai.exe takes some time. Please wait until the terminal (black screen) closes automatically.

<p align="center">
 <a href="https://youtu.be/0k8GA1DscKQ">
   <img width="30%" alt="How to install Behavior Senpai" src="https://img.youtube.com/vi/0k8GA1DscKQ/0.jpg">
 </a>
</p>

To uninstall Behavior Senpai or replace it with the latest version, delete the entire folder containing BehaviorSenpai.exe.

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

BehaviorSenpai saves calculated features based on Track file data to Feature files. Feature files are created in HDF5 format with the .feat extension.
Feature files store data calculated by [app_points_calc.py][app_points_calc], [app_trajplot.py][app_trajplot], and [app_feat_mix.py][app_feat_mix] in the format shown in the table below:

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

Additionally, data calculated by [app_dimredu.py][app_dimredu] is stored in the format shown in the table below. All these data are handled as Pandas DataFrames, with time-series data in 2-level-multi-index format, with the indices designated as "frame" and "member", respectively, and the columns including a "timestamp".

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
Nishimura, E. (2025). Behavior Senpai (Version 1.5) [Computer software]. Kyushu University, https://doi.org/10.48708/7160651
```

```
@misc{behavior-senpai-software,
  title = {Behavior Senpai},
  author = {Nishimura, Eigo},
  year = {2024},
  publisher = {Kyushu University},
  doi = {10.48708/7160651},
  note = {Available at: \url{https://hdl.handle.net/2324/7160651}},
}
```

### Related Documents
[Sample Videos for Behavioral Observation Using Keypoint Detection Technology](https://hdl.handle.net/2324/7172619)

[Quantitative Behavioral Observation Using Keypoint Detection Technology:
 Towards the Development of a New Behavioral Observation Method through Video Imagery](https://hdl.handle.net/2324/7170833)
