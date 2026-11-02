# 1.7.0 リリース候補の検証記録

検証日: 2026-11-02（日本時間）。対象: `fix/dev170-data-protection` の作業ツリー。
先行するデータ保護・時間軸フィルター修正（`7039a5e`、`bf5d0c5`）を保持している。AGENTS.mdはリポジトリと確認した親ディレクトリに見当たらなかった。

## 判定

**レビュー可能な候補だが、現時点で一般公開は不可。**

指定されたscene復元・負数範囲の不具合とバージョン表記を修正し、既存Windows環境で全49テストが成功した。
一方、新規Windows CPU環境では11件がアサーション完了後の子プロセスのアクセス違反で失敗した。
正常起動や「unittestのOK表示」だけを根拠に、そのプロセスを成功とは判定していない。

## 環境構築・起動

既存`.venv`を変更せず、別の空の環境へインストールした。

```powershell
$env:UV_PROJECT_ENVIRONMENT = Join-Path $env:TEMP 'behavior-senpai-170-rc-env'
uv sync --no-dev --no-extra cuda
uv pip check --python "$env:UV_PROJECT_ENVIRONMENT/Scripts/python.exe"
```

- Windows / CPython 3.11.14 / uv 0.13.4。
- 70パッケージの依存整合性検証成功。`ttkthemes==3.2.2`のビルド成功をログで確認した。
- 新規環境の実ThemedTk（breeze）ランチャーを表示し、イベントループを実行して正常終了（exit 0）。設定ファイルだけを一時ディレクトリへ隔離し、VideoCapture生成は1回。これは配布用EXEのInstall画面の確認ではない。
- 新規環境の主要バージョン: NumPy 1.26.4、Pandas 3.0.3、SciPy 1.17.1、scikit-learn 1.7.2、umap-learn 0.5.7、opencv-contrib-python 4.11.0.86、MediaPipe 0.10.21、PyTables 3.10.2。
- 既存環境にはopencv-contrib-pythonとopencv-pythonの両方（4.11.0.86）が存在した。新規環境との差ではあるが、両方を重ねて入れることを解決策とはしていない。
- `uv.lock`はこのリポジトリでは追跡されず、`.gitignore`の`*.lock`対象。ローカルのlockは`uv sync`により1.7.0へ更新されたが、依存解決結果の固定方法は配布準備時に別途確認する。

[Issue #1](https://github.com/nishimura5/behavior_senpai/issues/1)はttkthemes **3.3.0**のビルドメタデータ問題。
本候補の指定は**3.2.2固定**であり、新規環境でビルド・起動を確認した。Issueのopen状態を本候補の未修正判定には用いていない。

## 自動回帰テスト

```powershell
.venv/Scripts/python.exe -X utf8 -m unittest discover -v -s tests
& "$env:TEMP/behavior-senpai-170-rc-env/Scripts/python.exe" -X utf8 -m unittest discover -v -s tests
```

| 環境 | 結果 | 実行時間 |
| --- | --- | --- |
| 既存Windows環境 | 49件成功、exit 0 | 143.621秒 |
| 新規Windows CPU環境 | 38件成功、11件失敗、exit 1 | 140.371秒 |

GCの無効化や、ネイティブ異常終了を無視する処理は使用していない。
ランチャーのGUIテストはケースごとの子プロセスで、実VideoCaptureを1回だけ生成する。2回目の生成はテストで検出して止める。

| 対象 | 確認内容と実行方法 |
| --- | --- |
| Feature copyのscene復元 | 実Treeviewと実RowEditDialog。単一・複数選択の保存失敗を注入し、各行の全表示値と保存ファイルのバイト列を照合。既存環境で成功。新規環境ではアサーション後の異常終了により不合格。 |
| 描画範囲 | `0-1`、`10.0-30.0`、`-1-1`、`-180-180`、`-10--2`、空白・符号・指数表記を検証。文字列不正・非有限・逆転・同値を拒否。実入力ダイアログと実描画軸の値も確認。両環境で成功。 |
| Track読み込み・プレビュー | 合成AVIと実PKLを読み、実Tkキャンバスへ表示。主要操作スモークは両環境で正常終了。 |
| Remove・間引き | 実Remove画面で低スコア点を除去し60→15fps。240フレームから60フレームへの変化と欠測値を確認。両環境の主要操作スモークで成功。 |
| Smooth・Member | 実画面で移動平均を適用し履歴を確認。memberを7→8へ改名し結果を確認。両環境の主要操作スモークで成功。 |
| Scene table | 実画面でシーンを追加し、attrsと保存結果を確認。両環境の主要操作スモークで成功。 |
| Points・Mix/Norm・CSV | 実画面で距離計算、描画、HDF5保存、CSV出力を行う。再読み込みでデータを照合。主要操作スモークは両環境で成功。 |
| Feature copy | 実PKL・HDF5。Points定義あり／なしの正常計算・定義・profile、無関係グループ保持、各失敗時の既存バイト保持と一時ファイル清掃。両環境でファイル処理テスト成功。ランチャー経由の一部テストは新規環境で終了時異常。 |
| フィルター | 60・30・15Hzの出力信号で通過成分の振幅誤差±2.5%以内、阻止成分2.5%未満。member分離、欠測、不規則時刻、分離シーン、短区間、index・timestamp保持、失敗時の保存保護。両環境で成功。 |
| UMAP | 実Tk画面・実ワーカー・実HDF5。n_neighbors=1で実際に失敗させてコントロール復旧後、5へ直して正常完了・保存。計算中に実画面を破棄し、プロセス終了・一時ディレクトリ削除を確認。両環境で成功。 |
| UMAPのcp932ログ | 実ワーカーのUTF-8進捗をstrict cp932の出力ストリームへ渡し、正常完了することを確認。両環境で成功。 |
| 保存・再読み込み | 実Trackの保存・読み込みと座標・attrsを照合。主要操作スモークは両環境で成功。 |

主要操作はユーザーの代わりにGUIコールバックをプログラムから呼び出す自動検証であり、人によるマウス・キーボードの受け入れテストではない。
既存の`test_dimredu_process_ui.py`にはワーカー・描画のモックを用いるテストがある。今回の`test_umap_real_ui.py`は実ワーカーと実描画を使用する。
確認メッセージの応答、保存エラーの注入、設定置き場の隔離にはモックを用いるが、数値計算・ファイル・VideoCaptureを代替オブジェクトで成功扱いにはしていない。

## 公開阻害要因: 新規環境のアクセス違反

新規環境の11件は、主要操作スモーク以外のランチャー子プロセスで、テスト本体のOK表示後に0xC0000005で終了した。
VideoCaptureを2回以上生成するという既知の制約違反はない。
次の最小コードでも、新規環境で`ONE_CAPTURE_RELEASED`の後、GC時のアクセス違反（exit -1073741819）を再現した。

```powershell
& "$env:TEMP/behavior-senpai-170-rc-env/Scripts/python.exe" -X utf8 -X faulthandler -c "import sys; sys.path.insert(0,'src'); from behavior_senpai.vcap import VideoCap; cap=VideoCap(); print('ONE_CAPTURE_CREATED',flush=True); cap.release(); print('ONE_CAPTURE_RELEASED',flush=True)"
```

原因・安全な対処は未確定。この記録はOpenCV本体・Python・アプリのどこに原因があるかを断定しない。
コードを大きく置き換えたり、GCを止めたりして通過させる変更は行っていない。導入先のクリーン環境で正常終了する根拠が必要。

詳細ログは検証端末の一時ディレクトリに保存した。

- `behavior-rc-setup.log` / `behavior-rc-startup.log`: 新規インストールと起動。
- `behavior-170-rc-existing-tests.log` / `behavior-170-rc-fresh-tests.log`: 全49件。
- `behavior-rc-fresh-diagnose.log`: ジャンプキャンセル単独ケースのOK後の異常終了。
- `behavior-rc-capture-minimal.log`: 1回生成のみの最小再現。

## 公開前に人が確認する項目

- [ ] 上記アクセス違反の原因・対処を確認し、クリーンWindows環境で全件が正常終了すること。
- [ ] 1.7.0として組み立てたZIP／EXEを別のWindows環境で展開し、Install、新規起動、再起動、更新を確認する。既存EXEを1.7.0として再認定していない。
- [ ] CUDAあり／なし、モデル重み取得と各対応AIモデルの推論を、実収録動画で確認する。今回の新規構築はCPU依存のみ。
- [ ] 実収録Trackの時刻の揺れ・欠測・長い動画・複数memberで、編集から保存・再読み込みまで確認する。
- [ ] 異なるDLC定義を続けてインポートした際の共有TOML上書きを確認し、利用手順とバックアップ方針を決める。
- [ ] macOSの導入・GUI・動画入出力を確認する。今回の端末では未確認。
- [ ] 高DPIや画面サイズ、ドラッグ・選択・ショートカットなどを人が確認する。
- [ ] リリースノート・残存制約・依存固定方法をレビューし、配布物に必要なファイルとバージョンが揃っていることを確認する。

本作業では公開、タグ作成、masterへのマージ、push、EXEの再ビルドは行っていない。
