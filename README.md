# Video-Frame-Reducer
reducing duplicated frames from anime and other videos

このツールは、FFmpegを使用して動画ファイルを変換し、フレーム削減を行います。

ChatGPTで作ったぞ!

## 動作環境

- Python 3.6+
- PyQt5
- FFmpeg

## インストール手順

### Windows

1. **Pythonのインストール**
    - [公式サイト](https://www.python.org/downloads/windows/)からPythonをダウンロードし、インストールしてください。
    - インストール時に「Add Python to PATH」のチェックボックスをオンにしてください。

2. **FFmpegのインストール**
    - [FFmpeg公式サイト](https://ffmpeg.org/download.html#build-windows)からFFmpegをダウンロードしてください。
    - ダウンロードしたzipファイルを解凍し、`bin`フォルダのパスをシステム環境変数の`Path`に追加してください。

3. **依存パッケージのインストール**
    ```bash
    pip install PyQt5
    ```

4. **ファイル変換ツールのダウンロード**
    - このリポジトリをクローンするか、ZIPファイルとしてダウンロードして解凍してください。

5. **ツールの起動**
    ```bash
    python vfr.py
    ```

### macOS

1. **Pythonのインストール**
    - macOSにはPythonがプリインストールされていますが、最新バージョンを使用することをお勧めします。Homebrewを使用してインストールできます。
    ```bash
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    brew install python
    ```

2. **FFmpegのインストール**
    ```bash
    brew install ffmpeg
    ```

3. **依存パッケージのインストール**
    ```bash
    pip install PyQt5
    ```

4. **ファイル変換ツールのダウンロード**
    - このリポジトリをクローンするか、ZIPファイルとしてダウンロードして解凍してください。

5. **ツールの起動**
    ```bash
    python vfr.py
    ```

### Linux

1. **Pythonのインストール**
    - 多くのLinuxディストリビューションにはPythonがプリインストールされていますが、最新バージョンを使用することをお勧めします。
    ```bash
    sudo apt update
    sudo apt install python3 python3-pip
    ```

2. **FFmpegのインストール**
    ```bash
    sudo apt install ffmpeg
    ```

3. **依存パッケージのインストール**
    ```bash
    pip3 install PyQt5
    ```

4. **ファイル変換ツールのダウンロード**
    - このリポジトリをクローンするか、ZIPファイルとしてダウンロードして解凍してください。

5. **ツールの起動**
    ```bash
    python3 vfr.py
    ```

## 使用方法

1. ツールを起動します。
2. 「ファイル選択」ボタンをクリックして変換したいファイルを選択します。
3. 「変換開始」ボタンをクリックして変換を開始します。
4. ログボックスに変換の進行状況が表示されます。

## 注意事項

- 変換中にツールを閉じたり、強制終了したりしないでください。
- FFmpegの設定やコマンドに関する詳細は、[FFmpegの公式ドキュメント](https://ffmpeg.org/documentation.html)を参照してください。

## ライセンス

このプロジェクトはMITライセンスのもとで公開されています。詳細はLICENSEファイルを参照してください。
