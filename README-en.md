# python-senpai

python-senpai is an application for behavioral analysis and observation. It is also a project for learning Python coding and data analysis through development. It is designed so that those who have mastered the basics of Python (around if statements, for loops, list comprehensions, classes, etc.) can use it as a foothold to challenge the development of practical applications. In particular, you can learn how to use the following libraries:

 -  MultiIndex in Pandas
 - Time series data plotting with Matplotlib
 - VideoCapture in OpenCV (cv2)

## Requirement 

python-senpai was developed and tested in a Python environment built with [Rye](https://rye-up.com) on Windows 11 (22H2). Please refer to [pyproject.toml](pyproject.toml) etc. for the libraries used.

Currently, we have confirmed that importing matplotlib.backends.backend_tkagg fails when building the environment with Rye on macOS. Therefore, we have provided a branch for when backend_tkagg import fails. The code concerned is [trajectory_plotter.py](src/trajectory_plotter.py) and [recurrence_plotter.py](src/recurrence_plotter.py).

## Usage

If using rye, clone this repository and then run the following to build the environment:

```
rye sync
```

To enable CUDA, uncomment the relevant section in [pyproject.toml](pyproject.toml) beforehand.

Since only libraries that can be installed with pip are used, the environment can also be built using methods other than rye (like Anaconda).

After building the environment, run [launcher.py](src/launcher.py) to start the application.

```
rye run python src/launcher.py 
```

When running inferences on multiple video files sequentially using MediaPipe (and YOLO?), there is an issue where it crashes after the 2nd run due to a memory access violation. Therefore, [detector_proc.py](src/detector_proc.py) is executed using subprocess.

## Scripts

This repository contains the following applications:
 - video_to_keypoints.py: Pose estimation using YOLOv8 and MediaPipe Holistic and saving the results to a PKL file
 - keypoints_to_figure.py: Application to graph the data from the PKL file output by the above application

### Graph Drawing
The functionality and structure of the application is explained in the video below ([YouTube](https://youtu.be/c38UHrECGJA?si=k946YKvBmVXjrG8v)), so please watch it as well.
<p align="center">
<a href="https://youtu.be/c38UHrECGJA?si=k946YKvBmVXjrG8v"><img src="http://img.youtube.com/vi/c38UHrECGJA/mqdefault.jpg" width="300"></a>
</p>

 - [keypoints_to_figure.py](src/keypoints_to_figure.py): Graph drawing application (wrapper below) 
 - [trajectory_plotter.py](src/trajectory_plotter.py): Graphing data from PKL files
 - [keypoints_proc.py](src/keypoints_proc.py): Various calculations on time series coordinate data

### Pose Estimation
The functionality and structure of the application is explained in the video below ([YouTube](https://youtu.be/hE8ZoA8gETU?si=iDzTC7EPSqV6PfcA)), so please watch it as well.
<p align="center">
<a href="https://youtu.be/hE8ZoA8gETU?si=iDzTC7EPSqV6PfcA"><img src="http://img.youtube.com/vi/hE8ZoA8gETU/mqdefault.jpg" width="300"></a>
</p>

 - [video_to_keypoints.py](src/video_to_keypoints.py): Pose estimation application (wrapper below)
 - [yolo_detector.py](src/yolo_detector.py): Inference with YOLOv8 
 - [mediapipe_detector.py](src/mediapipe_detector.py): Inference with MediaPipe Holistic
 - [windows_and_mac.py](src/windows_and_mac.py): Opening video files and folders (for Windows and Mac)
 - [roi_cap.py](src/roi_cap.py): ROI feature

### Other
 - [mediapipe_drawer.py](src/mediapipe_drawer.py): Read PKL file and draw MediaPipe Holistic inference results on video
 - [yolo_drawer.py](src/yolo_drawer.py): Read PKL file and draw YOLOv8 inference results on video
