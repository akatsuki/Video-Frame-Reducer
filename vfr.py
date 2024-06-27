import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTableWidget,
                             QTableWidgetItem, QMessageBox, QProgressBar, QLabel, QTextEdit, QAbstractItemView, QHeaderView)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
import subprocess
import re
import time

class Worker(QThread):
    log_signal = pyqtSignal(str)
    done_signal = pyqtSignal()
    progress_signal = pyqtSignal(int)
    total_progress_signal = pyqtSignal(int)
    current_file_signal = pyqtSignal(str)
    remaining_files_signal = pyqtSignal(str)
    file_done_signal = pyqtSignal(int, int, float)
    update_status_signal = pyqtSignal(int, str)
    update_progress_signal = pyqtSignal(int, float)

    def __init__(self, input_files, output_files, file_sizes):
        super().__init__()
        self.input_files = input_files
        self.output_files = output_files
        self.file_sizes = file_sizes
        self.total_size = sum(self.file_sizes)
        self.processed_size = 0
        self.total_files = len(input_files)
        self.current_file_index = 0
        self.stop_requested = False
        self.start_time = None
        self.ffmpeg_process = None
        print("Worker initialized")

    def run(self):
        try:
            for i, (input_file, output_file, file_size) in enumerate(zip(self.input_files, self.output_files, self.file_sizes)):
                if self.stop_requested:
                    self.log_signal.emit("変換がユーザーによって中止されました。")
                    break
                self.update_status_signal.emit(i, "⏳")
                self.current_file_signal.emit(input_file)
                self.remaining_files_signal.emit(f"残りのファイル数: {self.total_files - i - 1}")
                self.log_signal.emit(f"変換中: {input_file}...\n")
                self.start_time = time.time()
                self.convert_file(input_file, output_file, i)
                elapsed_time = time.time() - self.start_time
                new_size = os.path.getsize(output_file)
                compression_ratio = ((file_size - new_size) / file_size) * 100
                self.processed_size += file_size
                self.progress_signal.emit(int((self.processed_size / self.total_size) * 100))
                self.total_progress_signal.emit(int(((i + 1) / self.total_files) * 100))
                self.file_done_signal.emit(i, new_size, compression_ratio)
                self.update_status_signal.emit(i, "✅")
                self.log_signal.emit(f"変換完了: {input_file} -> {output_file} ({elapsed_time:.2f}秒)\n")
                self.compare_frames(input_file, output_file)
            self.done_signal.emit()
        except Exception as e:
            self.log_signal.emit(f"エラーが発生しました: {str(e)}")

    def convert_file(self, input_file, output_file, file_index):
        try:
            command = [
                'ffmpeg', '-i', input_file, '-vf', 'mpdecimate', '-vsync', 'vfr', '-y', output_file
            ]
            self.ffmpeg_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            duration = None
            time_pattern = re.compile(r'time=(\d+:\d+:\d+\.\d+)')
            duration_pattern = re.compile(r'Duration: (\d+:\d+:\d+\.\d+)')
            
            while True:
                stderr_line = self.ffmpeg_process.stderr.readline()
                if stderr_line == '' and self.ffmpeg_process.poll() is not None:
                    break
                if stderr_line:
                    self.log_signal.emit(stderr_line.strip())
                    if not duration:
                        duration_match = duration_pattern.search(stderr_line)
                        if duration_match:
                            duration = self.ffmpeg_time_to_seconds(duration_match.group(1))
                    else:
                        time_match = time_pattern.search(stderr_line)
                        if time_match:
                            elapsed_time = self.ffmpeg_time_to_seconds(time_match.group(1))
                            progress = int((elapsed_time / duration) * 100)
                            self.update_progress_signal.emit(progress, elapsed_time)
            self.ffmpeg_process.wait()
            if self.ffmpeg_process.returncode != 0:
                self.log_signal.emit(f"変換失敗: {input_file}")
            else:
                self.log_signal.emit(f"変換成功: {input_file}")
        except subprocess.CalledProcessError as e:
            self.log_signal.emit(f"変換失敗: {input_file}\nエラー: {e}\n")

    def ffmpeg_time_to_seconds(self, time_str):
        h, m, s = map(float, time_str.split(':'))
        return h * 3600 + m * 60 + s

    def stop(self):
        self.stop_requested = True
        if self.ffmpeg_process is not None:
            self.ffmpeg_process.terminate()
            self.log_signal.emit("FFmpegプロセスが停止されました。")

    def compare_frames(self, input_file, output_file):
        try:
            input_frames = self.get_frame_count(input_file)
            output_frames = self.get_frame_count(output_file)
            frames_reduced = input_frames - output_frames
            reduction_percentage = (frames_reduced / input_frames) * 100
            self.log_signal.emit(f"元ファイルフレーム数: {input_frames}, 書き出し済みファイルフレーム数: {output_frames}")
            self.log_signal.emit(f"削減できたフレーム数: {frames_reduced} ({reduction_percentage:.2f}%)\n")
        except Exception as e:
            self.log_signal.emit(f"フレーム比較中にエラーが発生しました: {str(e)}")

    def get_frame_count(self, file_path):
        command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries', 'stream=nb_read_frames', '-of', 'default=nokey=1:noprint_wrappers=1', file_path]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return int(result.stdout.strip())

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        print("Initializing UI...")
        self.setWindowTitle('ファイル変換ツール')
        self.setGeometry(100, 100, 800, 600)
        self.create_widgets()
        self.create_layout()
        self.setAcceptDrops(True)
        self.show()
        print("UI Initialized")

    def create_widgets(self):
        print("Creating widgets...")
        self.select_button = QPushButton('ファイル選択')
        self.select_button.setToolTip('変換するファイルを選択します')
        self.select_button.clicked.connect(self.select_files)

        self.file_list = QTableWidget(0, 4)
        self.file_list.setHorizontalHeaderLabels(['', 'ファイル名', '新しいサイズ', '削減率'])
        self.file_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # ファイル名のカラムを可変に設定
        self.file_list.setColumnWidth(0, 30)  # ステータス: 2文字分
        self.file_list.setColumnWidth(2, 100)  # 新しいサイズ: 5文字分
        self.file_list.setColumnWidth(3, 100)  # 削減率: 7文字分
        self.file_list.horizontalHeaderItem(0).setTextAlignment(Qt.AlignCenter)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.current_progress_bar = QProgressBar()
        self.current_progress_bar.setValue(0)

        self.total_progress_bar = QProgressBar()
        self.total_progress_bar.setValue(0)

        self.time_remaining_label = QLabel('残り時間: 未計測')
        self.percent_label = QLabel('進行状況: 0%')
        self.current_file_label = QLabel('現在のファイル: なし')
        self.remaining_files_label = QLabel('残りのファイル数: 0')

        self.start_button = QPushButton('変換開始')
        self.start_button.setToolTip('選択されたファイルの変換を開始します')
        self.start_button.clicked.connect(self.start_conversion)

        self.stop_button = QPushButton('変換停止')
        self.stop_button.setToolTip('進行中の変換を停止します')
        self.stop_button.clicked.connect(self.stop_conversion)
        print("Widgets created")

    def create_layout(self):
        print("Creating layout...")
        layout = QVBoxLayout()
        layout.addWidget(self.select_button)
        layout.addWidget(self.file_list)
        layout.addWidget(self.log_box)
        layout.addWidget(self.current_progress_bar)
        layout.addWidget(self.total_progress_bar)
        layout.addWidget(self.time_remaining_label)
        layout.addWidget(self.percent_label)
        layout.addWidget(self.current_file_label)
        layout.addWidget(self.remaining_files_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)
        print("Layout created")

    def resizeEvent(self, event):
        self.update_file_column_widths()
        self.update_current_file_label()
        super().resizeEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self.file_list.setRowCount(0)
            for url in urls:
                file = url.toLocalFile()
                row_position = self.file_list.rowCount()
                self.file_list.insertRow(row_position)
                item = QTableWidgetItem("🕒")
                item.setTextAlignment(Qt.AlignCenter)
                self.file_list.setItem(row_position, 0, item)
                item = QTableWidgetItem(os.path.basename(file))
                item.setData(Qt.UserRole, file)  # フルアドレスを保存
                self.file_list.setItem(row_position, 1, item)
                self.file_list.setItem(row_position, 2, QTableWidgetItem("未変換"))
                self.file_list.setItem(row_position, 3, QTableWidgetItem("0%"))
            self.reset_progress()
            self.update_file_column_widths()

    def select_files(self):
        print("Selecting files...")
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, "ファイルを選択", "", "All Files (*);;Video Files (*.mp4 *.avi)", options=options)
        if files:
            self.file_list.setRowCount(0)
            for file in files:
                row_position = self.file_list.rowCount()
                self.file_list.insertRow(row_position)
                item = QTableWidgetItem("🕒")
                item.setTextAlignment(Qt.AlignCenter)
                self.file_list.setItem(row_position, 0, item)
                item = QTableWidgetItem(os.path.basename(file))
                item.setData(Qt.UserRole, file)  # フルアドレスを保存
                self.file_list.setItem(row_position, 1, item)
                self.file_list.setItem(row_position, 2, QTableWidgetItem("未変換"))
                self.file_list.setItem(row_position, 3, QTableWidgetItem("0%"))
            self.reset_progress()
            self.update_file_column_widths()
        print("Files selected")

    def elide_text(self, text, width):
        fm = self.file_list.fontMetrics()
        elided_text = fm.elidedText(text, Qt.ElideMiddle, width)
        return elided_text

    def reset_progress(self):
        self.current_progress_bar.setValue(0)
        self.total_progress_bar.setValue(0)
        self.time_remaining_label.setText('残り時間: 未計測')
        self.percent_label.setText('進行状況: 0%')
        self.current_file_label.setText('現在のファイル: なし')
        self.remaining_files_label.setText('残りのファイル数: 0')
        self.log_box.clear()

    def start_conversion(self):
        try:
            print("Starting conversion...")
            input_files = [self.file_list.item(row, 1).data(Qt.UserRole) for row in range(self.file_list.rowCount())]
            output_files = [self.add_suffix(file) for file in input_files]
            file_sizes = [os.path.getsize(file) for file in input_files]
            self.worker = Worker(input_files, output_files, file_sizes)
            self.worker.log_signal.connect(self.log_message)
            self.worker.progress_signal.connect(self.update_current_progress)
            self.worker.total_progress_signal.connect(self.update_total_progress)
            self.worker.current_file_signal.connect(self.update_current_file)
            self.worker.remaining_files_signal.connect(self.update_remaining_files)
            self.worker.file_done_signal.connect(self.mark_file_done)
            self.worker.update_status_signal.connect(self.update_file_status)
            self.worker.update_progress_signal.connect(self.update_progress)
            self.worker.done_signal.connect(self.conversion_done)
            self.worker.start()
            self.start_button.setText("変換中...")
            print("Conversion started")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"エラーが発生しました: {str(e)}")
            print(f"Error starting conversion: {str(e)}")

    def add_suffix(self, filepath):
        base, ext = os.path.splitext(filepath)
        return f"{base}_converted{ext}"

    def stop_conversion(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            print("Conversion stopped by user")

    def log_message(self, message):
        self.log_box.append(message)
        self.log_box.ensureCursorVisible()

    def update_current_progress(self, value):
        self.current_progress_bar.setValue(value)

    def update_total_progress(self, value):
        self.total_progress_bar.setValue(value)
        self.percent_label.setText(f'進行状況: {value}%')

    def update_current_file(self, current_file):
        self.current_file_label.setText(f"現在のファイル: {self.elide_text(os.path.basename(current_file), self.current_file_label.width())}")
        self.current_file_label.setToolTip(current_file)

    def update_remaining_files(self, remaining_files):
        self.remaining_files_label.setText(f"残りのファイル数: {remaining_files}")

    def mark_file_done(self, index, new_size, compression_ratio):
        self.file_list.setItem(index, 0, QTableWidgetItem("✅"))
        self.file_list.item(index, 0).setTextAlignment(Qt.AlignCenter)
        self.file_list.setItem(index, 2, QTableWidgetItem(f"{new_size / (1024 * 1024):.2f} MB"))
        self.file_list.setItem(index, 3, QTableWidgetItem(f"{compression_ratio:.2f}%"))
        self.scroll_to_current_file(index + 1)

    def update_file_status(self, index, status):
        self.file_list.setItem(index, 0, QTableWidgetItem(status))
        self.file_list.item(index, 0).setTextAlignment(Qt.AlignCenter)
        self.scroll_to_current_file(index)

    def update_progress(self, progress, elapsed_time):
        self.current_progress_bar.setValue(progress)
        self.percent_label.setText(f'進行状況: {progress}%')
        if progress > 0:
            remaining_time = elapsed_time * (100 - progress) / progress
            self.time_remaining_label.setText(f'残り時間: {remaining_time:.2f}秒')

    def scroll_to_current_file(self, index):
        self.file_list.scrollToItem(self.file_list.item(index, 1), QAbstractItemView.PositionAtCenter)

    def update_file_column_widths(self):
        self.file_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.file_list.setColumnWidth(2, 100)
        self.file_list.setColumnWidth(3, 100)

    def update_current_file_label(self):
        current_text = self.current_file_label.text().replace("現在のファイル: ", "")
        self.current_file_label.setText(f"現在のファイル: {self.elide_text(current_text, self.current_file_label.width())}")

    def conversion_done(self):
        QMessageBox.information(self, "完了", "全てのファイルの変換が完了しました。")
        self.start_button.setText("変換開始")
        print("Conversion done")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    print("Application initialized")
    ex = App()
    ex.show()
    print("Application running")
    sys.exit(app.exec_())
