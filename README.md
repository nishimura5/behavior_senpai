# Behavior Senpai v.1.2.0

[pyproject]: https://github.com/nishimura5/python_senpai/blob/master/pyproject.toml
[app_detect]: https://github.com/nishimura5/python_senpai/blob/master/src/app_detect.py
[app_track_list]: https://github.com/nishimura5/python_senpai/blob/master/src/app_track_list.py
[app_2point_calc]: https://github.com/nishimura5/python_senpai/blob/master/src/app_2point_calc.py
[app_3point_calc]: https://github.com/nishimura5/python_senpai/blob/master/src/app_3point_calc.py
[gui_parts]: https://github.com/nishimura5/python_senpai/blob/master/src/gui_parts.py
[detector_proc]: https://github.com/nishimura5/python_senpai/blob/master/src/detector_proc.py

![ScreenShot](https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20v.1.2.0%20_%20Python%20senpai_files/bs_capture_120.jpg)

Behavior Senpai(ビヘイビア センパイ)は、ビデオ観察法における定量的行動観察を支援するアプリケーションです。ビデオカメラで撮影した人の行動をkeypoint検出AIを使用して時系列座標データ化し、人の行動の定量的な分析や可視化を可能にします。

近年進展の著しいAI画像処理技術を行動観察に応用するにあたり、環境構築や調査比較、機能実装のためのコストが大きな課題となっていました。Behavior Senpaiは複数のAIモデルをノーコードで非情報系の研究者にも使用できるようにした点が特長です。

Behavior Senpaiは以下の3種類のAI画像処理フレームワーク/モデルをサポートしています。

 - [YOLOv8 Pose](https://github.com/ultralytics/ultralytics/issues/1915)
 - [MediaPipe Holistic](https://github.com/google/mediapipe/blob/master/docs/solutions/holistic.md)
 - [RTMPose Body8-Halpe26 (MMPose)](https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose#26-keypoints)

Behavior Senpaiは、ユーザーが選択したAIモデルによって動画内の人の姿勢推定を行い、時系列座標データを出力します。（これらはpose estimation、markerless motioin capture、landmark detectionなど、目的や用途によって様々な呼ばれ方をされています。）

<p align="center">
  <img width="60%" alt="What is Behavior Senpai" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20v.1.1.0%20_%20Python%20senpai_files/what_is_behavior_senpai.png">
</p>

Behavior Senpaiは[九州大学芸術工学部](https://www.design.kyushu-u.ac.jp/en/home/)で開発されたオープンソースのソフトウェアです。

## Requirement

Behavior Senpaiを使用するには以下の性能を満たすPCが必要です。動作確認はWindows11(23H2)でおこなっています。

### CUDAを使用する場合

 - 空き容量: 12GB～
 - 搭載RAM: 16GB～
 - 画面解像度： 1920x1080〜
 - GPU: RTX2060～ (CUDA: 12.1)

### CUDAを使用しない場合

CUDA対応GPUを搭載していない場合はMediaPipe Holisticのみが使用可能です。

 - 空き容量: 8GB～
 - 搭載RAM: 16GB～
 - 画面解像度： 1920x1080〜

## Usage

BehaviorSenpai.exeを実行するとアプリケーションが起動します。CUDAを使用する場合は初回起動時に「Enable features using CUDA」にチェックを入れてから「OK」ボタンをクリックしてください。

BehaviorSenpai.exeは、[Rye](https://rye-up.com)によるPython環境の構築とBehavior Senpai本体の起動を自動化するためのアプリケーションです。
BehaviorSenpai.exeによる初回起動時のセットアップには時間がかかります。ターミナル(黒い画面)が自動的に閉じるまでお待ちください。

Behavior Senpaiをアンインストールする場合、または最新版に差し替える場合にはBehaviorSenpai.exeが入ったフォルダを丸ごと削除してください。そのほか、Ryeのアンインストールには以下をターミナルから実行してください。

```
rye self uninstall
```

## Keypoints

Behavior Senpaiで取り扱うkeypointsのIDは各datasetのIDと同じです。YOLOv8ではCOCO、RTMPoseではHalpe26に準拠します。各keypointsのIDは以下のとおりです。

<p align="center">
  <img width="60%" alt="Keypoints of body (YOLOv8 and MMPose)" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20v.1.1.0%20_%20Python%20senpai_files/keypoints_body_110.png">
</p>

MediaPipe Holisticにおける顔のkeypoints(landmarks)のIDは以下のとおりです。すべてのIDが記載された資料は[こちら](https://storage.googleapis.com/mediapipe-assets/documentation/mediapipe_face_landmark_fullsize.png)を参照してください。

<p align="center">
  <img width="60%" alt="Keypoints of face (Mediapipe Holistic)" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20v.1.1.0%20_%20Python%20senpai_files/keypoints_face_110.png">
</p>

<p align="center">
  <img width="60%" alt="Keypoints of parts of face (Mediapipe Holistic)" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20v.1.1.0%20_%20Python%20senpai_files/keypoints_eyemouth_110.png">
</p>

MediaPipe Holisticにおける手のkeypoints(landmarks)のIDは以下のとおりです。

<p align="center">
  <img width="60%" alt="Keypoints of hands (Mediapipe Holistic)" src="https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20v.1.1.0%20_%20Python%20senpai_files/keypoints_hands_110.png">
</p>

## Interface

### Track file

app_detect.pyでキーポイント検出を行った結果としての時系列座標データは、[Pickle化されたPandasのDataFrame型](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_pickle.html)で保存されます。Behavior SenpaiはこれをTrack fileと呼んでいます。ファイル拡張子は'.pkl'です。Track fileはキーポイント検出を行った動画ファイルと同じディレクトリに生成される"trk"フォルダに保存されます。

Track fileは3-level-multi-indexで時系列座標データを保持しています。indexの名称はlevel 0から順に'frame', 'member', 'keypoint'です。frameは0から始まる整数で、動画のフレーム番号と対応しています。memberとkeypointはモデルが検出したkeypointsのIDです。Track fileには必ず'x', 'y', 'timestamp'の3つのcolumnsが含まれています。x,yの単位はpx、timestampの単位はミリ秒です。

Track fileに格納されているDataFrameの例を以下に示します。なおcolumnsにはAIモデルの仕様に応じて、そのほかに、'z'や'conf'といったcolumnが含まれることがあります。

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

Behavior Senpaiでは複数のキーポイントの位置関係の計算によって得られるデータをFeatureと呼びます。[app_2point_calc.py][app_2point_calc]や[app_3point_calc.py][app_3point_calc]で処理されたデータはFeature fileとして、(Track fileと同じく)Pickle化されたPandasのDataFrame型で"calc"フォルダに保存されます。ファイル拡張子はTrack fileと同様'.pkl'です。

Feature fileは2-level-multi-indexでデータを保持しています。indexの名称はlevel 0から順に'frame', 'member'です。columnsには必ず'timestamp'が含まれます。

Track fileのデータがあくまでもkeypointの検出結果にすぎないのに対して、Feature fileのデータは行動観察の目的に深く関連する特徴量である点に留意する必要があります。

#### Column name definition

[app_2point_calc.py][app_2point_calc]や[app_3point_calc.py][app_3point_calc]で処理されたFeature fileは（parseが可能なように）columnsの名称に規則を有しています。Feature file内のDataFrameにおける'timestamp'以外のcolumnsの名称のフォーマットは以下のとおりです。

```
{calc_code}({target keypoints}){suffix like _x or _y}
```

\{calc_code\}には計算の内容に応じて以下の文字列が入ります。

- component: 1つのベクトルのx成分とy成分(suffixに'_x'と'_y')
- norm: 1つのベクトルのnorm
- plus: 2つのベクトルの和(suffixに'_x'と'_y')
- cross: 2つのベクトルの外積
- dot: 2つのベクトルの内積
- norms: 2つのベクトルのnormの積

\{target keypoints\}には計算の対象となるkeypointのIDが入ります。'component'や'norm'のように1つのベクトルに対する計算の場合は、'1-2'のように、ベクトルの起点を左側としてハイフンで結合されたkeypointのIDのセットが記述されます。また'plus'や'cross'のような2つのベクトルに対する計算では'1-2,1-3'のように、カンマで区切られた複数のkeypointのIDのセットが記述されます。

具体例として、3つのkeypoint1,2,3における、keypoint=2を起点とした2ベクトルの外積を意味するカラム名は以下のように記述されます。

```
cross(2-1,2-3)
```


### Attributes of Track file

Track fileやFeature fileに格納されたDataFrameの[attrsプロパティ](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.attrs.html)には、元の動画ファイルのファイル名やそのフレームサイズ、キーポイント検出に使用したAIモデルの名称等が記録されています。

Track fileを読み込み、attrsに記録された内容を確認するためのPythonコードは以下のとおりです。attrsプロパティはdictionary型です。

```
trk_df = pd.read_pickle("path/to/track_file.pkl")
print(trk_df.attrs)
```

主なattrsの内容は以下のとおりです。このほかにも適宜追加されます。

#### model

キーポイント検出に使用したAI画像処理フレームワーク/モデルの名称が記録されています。attrsへの追加は[app_detector.py][app_detect]（[detector_proc.py][detector_proc]）で行われます。

 - YOLOv8 x-pose-p6
 - MediaPipe Holistic
 - MMPose RTMPose-x

#### frame_size

キーポイント検出を行った動画のフレームサイズがtuple型(width, height)で記録されています。単位はpxです。attrsへの追加は[app_detector.py][app_detect]（[detector_proc.py][detector_proc]）で行われます。

#### video_name

キーポイント検出を行った動画のファイル名が記録されています。attrsへの追加は[app_detector.py][app_detect]（[detector_proc.py][detector_proc]）で行われます。

#### created

Track fileが作成された日時が"%Y-%m-%d %H-%M-%S"のフォーマットで記録されています。attrsへの追加は[app_detector.py][app_detect]（[detector_proc.py][detector_proc]）で行われます。

#### next, prev

ビデオカメラで撮影した長時間の動画ファイルは、カメラの仕様で録画時に分割されることがあります。Track fileは動画ファイルと対になっているためTrack fileも分かれてしまいます。nextとprevは分かれているTrack fileの前後関係を記録するためのものです。attrsへの追加は[app_track_list.py][app_track_list]で行われます。

### Security Considerations

上記のとおり、Behavior SenpaiはPickle形式のファイルを取り扱います。Pickle形式にはセキュリティ上のリスクが存在するため、信頼できるファイルだけを開くようにしてください（たとえば、インターネット上に公開されている出典が不明なファイルを開こうとしないでください）。詳細は[こちら](https://docs.python.org/3/library/pickle.html)を参照してください。

### Annotated Video file

Behavior Senpaiは、検出したkeypointを描画してmp4形式の動画に出力することができます。

### Folder Structure

この節ではBehavior Senpaiが出力するデータのデフォルトの保存場所について説明します。Behavior Senpaiは"trk"フォルダにTrack fileを、"calc"フォルダにFeature fileを保存します。キーポイントを描画した動画は"mp4"フォルダに保存します。Track fileを編集し上書きすると、古いTrack fileは（ひとつだけ）"backup"フォルダに保存されます。それぞれのフォルダはファイル保存時に自動生成されます。

以下は、あるフォルダに"ABC.MP4"というファイルと"XYZ.MOV"というファイルがあった場合の一例です。出力ファイルのファイル名にはモデルや計算種別に応じたsuffixが付きます。動画のファイルパスに日本語が使用されているとファイルの読み書きに失敗するため、フォルダやファイルの名称には半角英数を使用してください。

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

Behavior SenpaiがTrack fileを読み込む際、親フォルダに動画が存在する場合はその動画ファイルを同時に読み込みます。読み込む動画のファイル名はAttributes of Track fileの"video_name"の値が参照されます。動画ファイルが見つからなかった場合は黒色の背景で代替されます。

### Temporary file

アプリケーションの設定値や直近で読み込まれたTrack fileのパスは、Pickle化されたdictionary型で保存されます。ファイル名は"temp.pkl"です。このファイルが存在しない場合はアプリケーションが(初期値を用いて)自動生成します。設定値を初期化する際はこのtemp.pklファイルを削除してください。
Temporaryファイルは[gui_parts.py][gui_parts]が管理しています。

## Citation

結果が出版物や他の場所で使用される場合は以下の内容にて引用してください。

```
Nishimura, E. (2024). Behavior Senpai (Version 1.2.0) [Computer software]. Kyushu University, https://doi.org/10.48708/7160651
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

[キーポイント検出技術を用いた定量的行動観察 : ビデオ映像による新しい行動観察手法の開発に向けて](https://hdl.handle.net/2324/7170833)
