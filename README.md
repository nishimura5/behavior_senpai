# Behavior Senpai v.1.4.0

[pyproject]: https://github.com/nishimura5/behavior_senpai/blob/master/pyproject.toml
[app_detect]: https://github.com/nishimura5/behavior_senpai/blob/master/src/app_detect.py
[app_track_list]: https://github.com/nishimura5/behavior_senpai/blob/master/src/app_track_list.py
[app_2point_calc]: https://github.com/nishimura5/behavior_senpai/blob/master/src/app_2point_calc.py
[app_3point_calc]: https://github.com/nishimura5/behavior_senpai/blob/master/src/app_3point_calc.py
[gui_parts]: https://github.com/nishimura5/behavior_senpai/blob/master/src/gui_parts.py
[detector_proc]: https://github.com/nishimura5/behavior_senpai/blob/master/src/detector_proc.py

![ScreenShot](https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20v.1.2.0%20_%20Python%20senpai_files/bs_capture_120.jpg)

Behavior Senpai is an application that supports quantitative behavior observation in video observation methods. It converts video files into time-series coordinate data using keypoint detection AI, enabling quantitative analysis and visualization of human behavior.
Behavior Senpai is distinctive in that it permits the utilization of multiple AI models without the necessity for coding. 

 The following AI image processing frameworks/models are supported by Behavior Senpai:
- [YOLO11 Pose](https://docs.ultralytics.com/tasks/pose/)
- [MediaPipe Holistic](https://github.com/google/mediapipe/blob/master/docs/solutions/holistic.md)
- [RTMPose Halpe26 (MMPose)](https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose#26-keypoints)
- [RTMPose WholeBody133 (MMPose)](https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose#wholebody-2d-133-keypoints)

Behavior Senpai performs pose estimation of a person in a video using an AI model selected by the user, and outputs time-series coordinate data.
(These are variously referred to as "pose estimation", "markerless motion capture", "landmark detection", and so forth, depending on the intended purpose and application.)

<p align="center">
  <img width="60%" alt="What is Behavior Senpai" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20v.1.1.0%20_%20Python%20senpai_files/what_is_behavior_senpai.png">
</p>

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

The ID of keypoints handled by Behavior Senpai is the same as the ID of each dataset.
YOLO11 (and YOLOv8) complies with COCO and RTMPose complies with Halpe26.
The IDs of each keypoints are as follows.

<p align="center">
  <img width="60%" alt="Keypoints of body (YOLO11 and MMPose)" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20v.1.1.0%20_%20Python%20senpai_files/keypoints_body_110.png">
</p>

The IDs of the keypoints (landmarks) of the faces in MediaPipe Holistic are as follows. See [here](https://storage.googleapis.com/mediapipe-assets/documentation/mediapipe_face_landmark_fullsize.png) for a document with all IDs.

<p align="center">
  <img width="60%" alt="Keypoints of face (Mediapipe Holistic)" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20v.1.1.0%20_%20Python%20senpai_files/keypoints_face_110.png">
</p>

<p align="center">
  <img width="60%" alt="Keypoints of parts of face (Mediapipe Holistic)" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20v.1.1.0%20_%20Python%20senpai_files/keypoints_eyemouth_110.png">
</p>

The IDs of the keypoints (landmarks) of the hands in MediaPipe Holistic are as follows

<p align="center">
  <img width="60%" alt="Keypoints of hands (Mediapipe Holistic)" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20v.1.1.0%20_%20Python%20senpai_files/keypoints_hands_110.png">
</p>

## Interface

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

In Behavior Senpai, the data obtained by calculating the positional relationship of multiple keypoints is referred to as a feature. The data processed by [app_2point_calc.py][app_2point_calc] or [app_3point_calc.py][app_3point_calc] is stored in a pickled format. The data processed by [app_3point_calc][app_3point_calc] is saved as a "Feature file" in the "calc" folder. The file extension is ".feat.pkl". The Feature file holds time-series data in 2-level-multi-index format, with the indices designated as "frame" and "member", respectively, and the columns including a "timestamp". It should be noted that the data in the Track file is only the result of keypoint detection, while the data in the Feature file are features that are deeply related to the purpose of behavior observation.

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

#### Column name definition

The feature files processed by [app_2point_calc.py][app_2point_calc] and [app_3point_calc.py][app_3point_calc] have rules for columns names (to enable parsing).
The format of columns names in the DataFrame in the feature file, except for timestamp, is as follows.

```
{calc_code}({target keypoints})
```

\{calc_code\} contains the following strings, depending on the calculation.

- x: x
- y: y
- component_x and component_y: x or y component of one vector
- norm: norm of one vector
- plus_x and plus_y: the sum of two vectors
- cross: cross product of two vectors
- dot: inner product of two vectors
- norms: product of the norms of two vectors
- sin: cross / norms
- cos: dot / norms

\{target keypoints\} contains the IDs of the keypoints to be calculated.
In the case of a calculation for a single vector, such as 'component' or 'norm', a hyphenated set of keypoint IDs is written with the starting point of the vector on the left, such as '1-2'.
For calculations on two vectors such as 'plus' and 'cross', a comma-separated set of keypoint IDs is written, such as '1-2,1-3'.

As a concrete example, a column name meaning the outer product of two vectors starting from keypoint=2 at three keypoints1,2,3 would be written as follows.

```
cross(2-1,2-3)
```

### Category file

The category file contains boolean data indicating the presence of specific behaviors for each member at each frame. It includes frame and member identifiers, a class column for internal use, boolean columns for each category (e.g., cat_1, cat_2), and a timestamp. True values represent the occurrence of a behavior for a given member at a specific frame.The file extension is ".bc.pkl". 

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

### Attributes of Track (or Feature) file

The [attrs property](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.attrs.html) of the DataFrame stored in Track file (and Feature files) records information such as the original video file name, its frame size, and the name of the AI model used for keypoint detection.

To load a Track file and check the contents recorded in attrs, the Python code

 is as follows. The attrs property is of dictionary type:

```
trk_df = pd.read_pickle("path/to/track_file.pkl")
print(trk_df.attrs)
```

Main contents of attrs include, but are not limited to:

#### model

The name of the AI image processing framework/model used for keypoint detection. Addition to attrs is done by [app_detector.py][app_detect] ([detector_proc.py][detector_proc]).

 - YOLO11 x-pose
 - MediaPipe Holistic
 - MMPose RTMPose-x

#### frame_size

The frame size of the video on which keypoint detection was performed is recorded as a tuple (width, height) in pixels. Addition to attrs is done by [app_detector.py][app_detect] ([detector_proc.py][detector_proc]).

#### video_name

The file name of the video on which keypoint detection was performed is recorded. Addition to attrs is done by [app_detector.py][app_detect] ([detector_proc.py][detector_proc]).

#### created

Dates and times when the Track file was created are recorded in the format "%Y-%m-%d %H-%M-%S". Additions to attrs are made in [app_detector.py][app_detect] ([detector_proc.py][detector_proc]).

#### next, prev

Long videos captured by a video camera may be split during recording due to camera specifications. Since Track files are paired with video files, they are also split. 'next' and 'prev' record the sequence of split Track files. Addition to attrs is done by [app_track_list.py][app_track_list].

### Security Considerations

As mentioned above, Behavior Senpai handles pickle format files, and because of the security risks associated with pickle format files, please only open files that you trust (e.g., do not open files from unknown sources that are available on the Internet). (For example, do not try to open files of unknown origin published on the Internet). See [here](https://docs.python.org/3/library/pickle.html) for more information.

### Annotated Video file

Behavior Senpai can output videos in mp4 format with detected keypoints drawn on them.

### Folder Structure

This section explains the default locations for data output by Behavior Senpai. Track files are saved in the "trk" folder, Feature files in the "calc" folder, and videos with keypoints drawn are saved in the "mp4" folder. If a Track file is edited and overwritten, the old Track file is saved in the "backup" folder (only one backup is kept). These folders are automatically generated at the time of file saving.

Below is an example of the folder structure when there are files named "ABC.MP4" and "XYZ.MOV" in a folder. Output file names include suffixes according to the model or type of calculation. To avoid file read/write failures, use alphanumeric characters for folder and file names, especially when the file path contains Japanese characters.

```
├── ABC.MP4
├── XYZ.MOV
├── calc
│   └── XYZ_2p.pkl
├── mp4
│   └── ABC_mediapipe.mp4
└── trk
    ├── ABC.pkl
    ├── XYZ.pkl
    └── backup
        └── ABC.pkl
```

When Behavior Senpai loads a Track file, if a video file exists in the parent folder, it also loads that video file. The file name of the video to be loaded is referred from the "video_name" value in Attributes of Track file. If the video file is not found, a black background is used as a substitute.

### Temporary file

The application's settings and the path of the most recently loaded Track file are saved as a Pickled dictionary. The file name is "temp.pkl". If this file does not exist, the application automatically generates it (using default values). To reset the settings, delete the "temp.pkl" file. The Temporary file is managed by [gui_parts.py][gui_parts].

## Citation

Please acknowledge and cite the use of this software and its authors when results are used in publications or published elsewhere.

```
Nishimura, E. (2024). Behavior Senpai (Version 1.4.0) [Computer software]. Kyushu University, https://doi.org/10.48708/7160651
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
