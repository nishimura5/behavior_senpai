# Behavior Senpai v.1.1.0

[pyproject]: https://github.com/nishimura5/python_senpai/blob/master/pyproject.toml
[app_detect]: https://github.com/nishimura5/python_senpai/blob/master/src/app_detect.py
[app_track_list]: https://github.com/nishimura5/python_senpai/blob/master/src/app_track_list.py
[app_2point_calc]: https://github.com/nishimura5/python_senpai/blob/master/src/app_2point_calc.py
[app_3point_calc]: https://github.com/nishimura5/python_senpai/blob/master/src/app_3point_calc.py
[gui_parts]: https://github.com/nishimura5/python_senpai/blob/master/src/gui_parts.py
[detector_proc]: https://github.com/nishimura5/python_senpai/blob/master/src/detector_proc.py

![ScreenShot](https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20_%20Python%20senpai_files/bs_capture_110.jpg)

Behavior Senpai is an application that supports quantitative behavior observation in video observation methods. It converts human behavior captured by video cameras into time-series coordinate data using keypoint detection AI, enabling quantitative analysis and visualization of human behavior.

Behavior Senpai features multiple AI models that can be used in the same interface with no code. Behavior Senpai is unique in that it allows multiple AI models to be used in the same interface with no code.

Behavior Senpai supports the following three AI image processing frameworks/models

 - [YOLOv8 Pose](https://github.com/ultralytics/ultralytics/issues/1915)
 - [MediaPipe Holistic](https://github.com/google/mediapipe/blob/master/docs/solutions/holistic.md)
 - [RTMPose Body8-Halpe26 (MMPose)](https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose#26-keypoints)

Behavior Senpai performs posture estimation of a person in a video using a user-selected AI model and outputs time-series coordinate data.

<p align="center">
  <img width="60%" alt="What is Behavior Senpai" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20_%20Python%20senpai_files/what_is_behavior_senpai.png">
</p>

## Requirement

Behavior Senpai has been developed and tested on Windows11(23H2).

### If using CUDA

 - Free space: 10GB or more
 - Installed RAM: 16GB or more
 - GPU: RTX2060 or higher (CUDA: 12.1)
 - [Rye](https://rye-up.com)
 - [.NET 8.0](https://dotnet.microsoft.com/download/dotnet/8.0)

### Without CUDA

If a CUDA-compatible GPU is not installed, only MediaPipe Holistic can be used.

 - Free space: 8GB or more
 - Installed RAM: 16GB or more
 - [Rye](https://rye-up.com)
 - [.NET 8.0](https://dotnet.microsoft.com/download/dotnet/8.0)

## Usage

### Windows

Launching BehaviorSenpai.exe starts the application. If using CUDA, check "Enable features using CUDA" upon first launch and then click "OK".

To uninstall or replace with the latest version, simply delete the folder containing BehaviorSenpai.exe.

### Mac

On Mac, instead of the CPython downloaded by Rye, download or build Python separately using pyenv or a similar tool and manually add it to the toolchain. For example:

 - pyenv install 3.11.6
 - Obtain the path to python using `pyenv which python`
 - Open the .python-version file and change it to "pyenv@3.11.6"
 - rye toolchain register --name=pyenv /path/to/pyenv/python3.11
 - rye fetch 3.11.6
 - git clone https://github.com/nishimura5/behavior_senpai.git
 - cd behavior_senpai
 - rye sync
 - . ./launcher.sh

Installation is complete with these steps.

## Keypoints

The IDs for keypoints handled by Behavior Senpai are the same as those in each dataset. For YOLOv8, it complies with COCO; for RTMPose, with Halpe26. The IDs for each keypoint are as follows:

<p align="center">
  <img width="60%" alt="What is Behavior Senpai" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20_%20Python%20senpai_files/keypoints_body_110.png">
</p>

The IDs for facial keypoints (landmarks) in MediaPipe Holistic are as follows. For a complete list of all IDs, refer [here](https://storage.googleapis.com/mediapipe-assets/documentation/mediapipe_face_landmark_fullsize.png).

<p align="center

">
  <img width="60%" alt="What is Behavior Senpai" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20_%20Python%20senpai_files/keypoints_face_110.png">
</p>

<p align="center">
  <img width="60%" alt="What is Behavior Senpai" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20_%20Python%20senpai_files/keypoints_eyemouth_110.png">
</p>

The IDs for hand keypoints (landmarks) in MediaPipe Holistic are as follows:

<p align="center">
  <img width="60%" alt="What is Behavior Senpai" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20_%20Python%20senpai_files/keypoints_hands_110.png">
</p>

## Interface

> [!IMPORTANT]
Behavior Senpai handles files in Pickle format. Due to security risks associated with Pickle format, only open files from trusted sources (e.g., avoid opening files from unknown sources available on the internet). For details, refer [here](https://docs.python.org/3/library/pickle.html).

### Track file

The time-series coordinate data resulting from keypoint detection by app_detect.py is saved as a [Pickle-serialized Pandas DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_pickle.html). Behavior Senpai refers to these as Track files. The file extension is '.pkl'. Track files are saved in the "trk" folder generated in the same directory as the video file on which keypoint detection was performed.

Track files hold time-series coordinate data with a 3-level-multi-index. The index names are 'frame', 'member', and 'keypoint' from level 0 onwards. 'Frame' is an integer starting from 0, corresponding to the video frame number. 'Member' and 'keypoint' are the IDs of keypoints detected by the model. Track files always include three columns: 'x', 'y', 'timestamp', where x,y are in pixels and timestamp is in milliseconds.

Example of a DataFrame stored in a Track file, which might also include other columns such as 'z' or 'conf' depending on the AI model's specifications:

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

### Calculated Track file

Data processed by [app_2point_calc.py][app_2point_calc] or [app_3point_calc.py][app_3point_calc] is saved in the same Pickle-serialized Pandas DataFrame format as Track files and stored in the "calc" folder. The file extension is '.pkl', the same as for Track files.

Calculated Track files hold data with a 2-level-multi-index, with index names 'frame' and 'member' from level 0 onwards. Column names correspond to the calculations performed, but 'timestamp' is always included.

### Attributes of Track file

The [attrs property](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.attrs.html) of the DataFrame stored in Track and Calculated Track files records information such as the original video file name, its frame size, and the name of the AI model used for keypoint detection.

To load a Track file and check the contents recorded in attrs, the Python code

 is as follows. The attrs property is of dictionary type:

```
trk_df = pd.read_pickle("path/to/track_file.pkl")
print(trk_df.attrs)
```

Main contents of attrs include, but are not limited to:

#### model

The name of the AI image processing framework/model used for keypoint detection. Addition to attrs is done by [app_detector.py][app_detect] ([detector_proc.py][detector_proc]).

 - YOLOv8 x-pose-p6
 - MediaPipe Holistic
 - MMPose RTMPose-x

#### frame_size

The frame size of the video on which keypoint detection was performed is recorded as a tuple (width, height) in pixels. Addition to attrs is done by [app_detector.py][app_detect] ([detector_proc.py][detector_proc]).

#### video_name

The file name of the video on which keypoint detection was performed is recorded. Addition to attrs is done by [app_detector.py][app_detect] ([detector_proc.py][detector_proc]).

#### next, prev

Long videos captured by a video camera may be split during recording due to camera specifications. Since Track files are paired with video files, they are also split. 'Next' and 'prev' record the sequence of split Track files. Addition to attrs is done by [app_track_list.py][app_track_list].

### Annotated Video file

Behavior Senpai can output videos in mp4 format with detected keypoints drawn on them.

### Folder Structure

This section explains the default locations for data output by Behavior Senpai. Track files are saved in the "trk" folder, Calculated Track files in the "calc" folder, and videos with keypoints drawn are saved in the "mp4" folder. If a Track file is edited and overwritten, the old Track file is saved in the "backup" folder (only one backup is kept). These folders are automatically generated at the time of file saving.

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

The application's settings and the path of the most recently loaded Track file are saved as a Pickle-serialized dictionary. The file name is "temp.pkl". If this file does not exist, the application automatically generates it (using default values). To reset the settings, delete the temp.pkl file. The Temporary file is managed by [gui_parts.py][gui_parts].

## Citation

Please acknowledge and cite the use of this software and its authors when results are used in publications or published elsewhere.

```
Nishimura, E. (2024). Behavior Senpai (Version 1.1.0) [Computer software]. Kyushu University, https://doi.org/10.48708/7160651
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