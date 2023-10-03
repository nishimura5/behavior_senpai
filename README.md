# python-senpai

YOLOv8の推論結果をCSVファイルに保存し、Pandasで読み込んでSeabornで時系列データとしてグラフ描画するまでの一部始終を動画にしました。AIによる追跡や姿勢推定の出力を時系列データとして記録することで、行動の定量化が可能となり、人の行動を条件間や個人間で比較することができるようになります。

## 動画

以下の動画([YouTube](https://youtu.be/K-GwnzYpg5Q?si=3VkMu6M0bCmhuhMs))で、スクリプトのコーディングの一部始終を説明しているので併せてご覧ください。

<p align="center">
<a href="https://youtu.be/K-GwnzYpg5Q?si=3VkMu6M0bCmhuhMs"><img src="https://github-production-user-asset-6210df.s3.amazonaws.com/49755007/272127984-c4b6aa5b-11ca-4326-8e07-a704b14d6528.png" width="500"></a>
</p>

## スクリプト

 - [yolo_detector.py](src/yolo_detector.py): YOLOv8による推論結果をCSVファイルに出力
 - [yolo_drawer.py](src/yolo_drawer.py): CSVファイルを読み込んで推論結果を動画に描画
 - [yolo_plotter.py](src/yolo_plotter.py): CSVファイルを読み込んで推論結果を時系列グラフにプロット
