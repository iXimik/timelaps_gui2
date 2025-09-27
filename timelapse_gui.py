# -*- coding: utf-8 -*-р
"""
Пастельно-стильный интерфейс для TimelapseApp
Слева preview, справа контролы.
"""
import sys
import os
import cv2
import time
import threading
import subprocess
import re
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QComboBox, QSlider, QCheckBox, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap


def get_working_cameras(max_tested=10):
    cams = []
    for i in range(max_tested):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                cams.append(i)
            cap.release()
    return cams


def get_supported_resolutions():
    # в т.ч. портретные
    return [(640, 360), (1280, 720), (1920, 1080), (720, 1280), (1080, 1920)]


class TimelapseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Timelapse GUI")
        self.setFixedSize(800, 500)

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_preview)
        self.capturing = False
        self.frame_list = []
        self.frame_dir = ""
        self.video_dir = ""
        self.camera_indexes = get_working_cameras()

        self.init_ui()
        self.restart_camera()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #E3FDFD; }
            QLabel { color: #333; font-size: 14px; }
            QPushButton { background-color: #A8E6CF; color: #05668D; border: none; border-radius: 8px; padding: 6px 12px; }
            QPushButton:hover { background-color: #79C7B7; }
            QPushButton:disabled { background-color: #CFCFCF; color: #888888; }
            QComboBox, QSlider::groove:horizontal, QCheckBox { background-color: #FFFFFF; border: 1px solid #A8E6CF; border-radius: 6px; padding: 4px; }
            QSlider::handle:horizontal { background-color: #FFD3B5; width: 12px; margin: -2px 0; border-radius: 6px; }
        """)
        main_layout = QHBoxLayout(self)

        # Preview
        preview_frame = QFrame()
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_label = QLabel("Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(480, 360)
        self.preview_label.setStyleSheet("border:2px solid #A8E6CF; background-color:#FFFFFF;")
        preview_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)
        main_layout.addWidget(preview_frame)

        # Controls
        ctrl_frame = QFrame()
        ctrl_layout = QVBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(20, 20, 20, 20)
        ctrl_layout.setSpacing(15)

        # Camera
        cam_h = QHBoxLayout()
        cam_h.addWidget(QLabel("Камера:"))
        self.camera_box = QComboBox()
        for idx in self.camera_indexes:
            self.camera_box.addItem(f"Камера {idx}", idx)
        self.camera_box.currentIndexChanged.connect(self.restart_camera)
        cam_h.addWidget(self.camera_box)
        ctrl_layout.addLayout(cam_h)

        # Resolution
        res_h = QHBoxLayout()
        res_h.addWidget(QLabel("Разрешение:"))
        self.resolution_box = QComboBox()
        for w, h in get_supported_resolutions():
            self.resolution_box.addItem(f"{w}x{h}", (w, h))
        res_h.addWidget(self.resolution_box)
        ctrl_layout.addLayout(res_h)

        # Aspect
        asp_h = QHBoxLayout()
        asp_h.addWidget(QLabel("Формат:"))
        self.aspect_ratio_box = QComboBox()
        self.aspect_ratio_box.addItems(["16:9", "9:16"])
        self.aspect_ratio_box.currentTextChanged.connect(self.update_preview_size)
        asp_h.addWidget(self.aspect_ratio_box)
        ctrl_layout.addLayout(asp_h)

        # FPS
        self.fps_label = QLabel("FPS: 25")
        ctrl_layout.addWidget(self.fps_label)
        self.fps_slider = QSlider(Qt.Horizontal)
        self.fps_slider.setRange(1, 60)
        self.fps_slider.setValue(25)
        self.fps_slider.valueChanged.connect(lambda v: self.fps_label.setText(f"FPS: {v}"))
        ctrl_layout.addWidget(self.fps_slider)

        # Interval
        self.interval_label = QLabel("Интервал (сек): 10")
        ctrl_layout.addWidget(self.interval_label)
        self.interval_slider = QSlider(Qt.Horizontal)
        self.interval_slider.setRange(1, 60)
        self.interval_slider.setValue(10)
        self.interval_slider.valueChanged.connect(lambda v: self.interval_label.setText(f"Интервал (сек): {v}"))
        ctrl_layout.addWidget(self.interval_slider)

        # Folders
        folder_h = QHBoxLayout()
        self.folder_button = QPushButton("Папка фото")
        self.folder_button.clicked.connect(self.select_frame_dir)
        self.video_button = QPushButton("Папка видео")
        self.video_button.clicked.connect(self.select_video_dir)
        folder_h.addWidget(self.folder_button)
        folder_h.addWidget(self.video_button)
        ctrl_layout.addLayout(folder_h)
        self.frame_dir_label = QLabel("Фото → (не выбрана)")
        ctrl_layout.addWidget(self.frame_dir_label)
        self.video_dir_label = QLabel("Видео → (не выбрана)")
        ctrl_layout.addWidget(self.video_dir_label)

        # Keep frames
        self.keep_frames_checkbox = QCheckBox("Сохранять фотографии")
        self.keep_frames_checkbox.setChecked(True)
        ctrl_layout.addWidget(self.keep_frames_checkbox)

        # Actions
        action_h = QHBoxLayout()
        self.start_btn = QPushButton("Старт")
        self.start_btn.clicked.connect(self.start_capture)
        self.stop_btn = QPushButton("Стоп")
        self.stop_btn.clicked.connect(self.stop_capture)
        self.stop_btn.setEnabled(False)
        self.make_video_btn = QPushButton("Сделать видео")
        self.make_video_btn.clicked.connect(self.make_video)
        action_h.addWidget(self.start_btn)
        action_h.addWidget(self.stop_btn)
        action_h.addWidget(self.make_video_btn)
        ctrl_layout.addLayout(action_h)

        # Snapshot
        self.photo_btn = QPushButton("Сделать фото")
        self.photo_btn.clicked.connect(self.take_photo)
        ctrl_layout.addWidget(self.photo_btn)

        main_layout.addWidget(ctrl_frame)

    def update_preview_size(self):
        if self.aspect_ratio_box.currentText() == "9:16":
            self.preview_label.setFixedSize(260, 480)
        else:
            self.preview_label.setFixedSize(480, 360)

    def restart_camera(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        idx = self.camera_box.currentData()
        self.cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        w, h = self.resolution_box.currentData()
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        self.timer.start(100)
        self.update_preview_size()

    def update_preview(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = self.process_aspect_ratio(frame)
        img = cv2.resize(frame, (self.preview_label.width(), self.preview_label.height()))
        qimg = QImage(img.data, img.shape[1], img.shape[0], img.shape[1]*3, QImage.Format_BGR888)
        self.preview_label.setPixmap(QPixmap.fromImage(qimg))

    def process_aspect_ratio(self, frame):
        num, den = map(int, self.aspect_ratio_box.currentText().split(':'))
        h, w = frame.shape[:2]
        t = num / den  # целевое W/H
        if w / h > t:
            # кадр «шире» — режем по ширине
            nw = int(h * t)
            x = (w - nw) // 2
            return frame[:, x:x + nw]
        else:
            # кадр «уже» — режем по высоте
            nh = int(w / t)
            y = (h - nh) // 2
            return frame[y:y + nh, :]

    def select_frame_dir(self):
        d = QFileDialog.getExistingDirectory(self, 'Папка фото')
        if d:
            self.frame_dir = d
            self.frame_dir_label.setText(f"Фото → {d}")

    def select_video_dir(self):
        d = QFileDialog.getExistingDirectory(self, 'Папка видео')
        if d:
            self.video_dir = d
            self.video_dir_label.setText(f"Видео → {d}")

    def start_capture(self):
        if not self.frame_dir:
            QMessageBox.warning(self, 'Внимание', 'Выберите папку для фото')
            return
        self.capturing = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        threading.Thread(target=self.capture_loop, daemon=True).start()

    def stop_capture(self):
        self.capturing = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def capture_loop(self):
        while self.capturing:
            ret, frame = self.cap.read()
            if not ret:
                continue
            frame = self.process_aspect_ratio(frame)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(self.frame_dir, f"frame_{ts}.jpg")
            cv2.imwrite(path, frame)
            self.frame_list.append(path)
            time.sleep(self.interval_slider.value())

    def _target_size(self):
        """Размер выходного видео под выбранный формат (чётные)."""
        w, h = self.resolution_box.currentData()
        ar = self.aspect_ratio_box.currentText()
        if ar == "9:16":
            if h < w:
                w, h = h, w  # портрет
            else:
                w, h = w, h
            # нормализуем до типового FullHD-портрета, если сильно отличаемся
            if (w, h) == (640, 360):
                w, h = 360, 640
            elif (w, h) == (1280, 720):
                w, h = 720, 1280
            elif (w, h) == (1920, 1080):
                w, h = 1080, 1920
        else:  # 16:9
            if h > w:
                w, h = h, w  # ландшафт
        # чётные (для yuv420p)
        w -= w % 2
        h -= h % 2
        return max(2, w), max(2, h)

    def make_video(self):
        if not self.video_dir or not self.frame_list:
            QMessageBox.warning(self, 'Ошибка', 'Нет кадров или папка видео не выбрана')
            return

        # список для concat-demuxer
        list_file = os.path.join(self.video_dir, 'frames.txt')
        fps = self.fps_slider.value()
        try:
            with open(list_file, 'w', encoding='utf-8') as f:
                for i, img in enumerate(self.frame_list):
                    img_path = Path(img).as_posix()
                    f.write(f"file '{img_path}'\n")
                    # длительность каждого кадра
                    if i < len(self.frame_list) - 1:
                        f.write(f"duration {1.0 / fps:.6f}\n")
                # последний кадр нужно повторить без duration
                f.write(f"file '{Path(self.frame_list[-1]).as_posix()}'\n")
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка записи списка кадров', str(e))
            return

        out = self.get_next_filename()
        out_w, out_h = self._target_size()

        # аккуратно вписываем без растяжения, заполняем поля и фиксируем SAR
        vf = f"fps={fps},scale={out_w}:{out_h}:force_original_aspect_ratio=decrease," \
             f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2,setsar=1"

        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', Path(list_file).as_posix(),
            '-vf', vf,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            out
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            QMessageBox.information(self, 'Готово', f"Видео: {out}")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, 'ffmpeg error', e.stderr.decode())
        finally:
            try:
                os.remove(list_file)
            except OSError:
                pass

        if not self.keep_frames_checkbox.isChecked():
            for img in self.frame_list:
                try:
                    os.remove(img)
                except OSError:
                    pass
            self.frame_list.clear()

    def take_photo(self):
        ret, frame = self.cap.read()
        if ret:
            frame = self.process_aspect_ratio(frame)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(self.frame_dir or os.getcwd(), f"photo_{ts}.jpg")
            cv2.imwrite(path, frame)
            QMessageBox.information(self, 'Фото', f"Сохранено: {path}")

    def get_next_filename(self, base_name='timelapse', ext='.mp4'):
        if not os.path.isdir(self.video_dir):
            return os.path.join(os.getcwd(), f"{base_name}_1{ext}")
        nums = []
        for fname in os.listdir(self.video_dir):
            m = re.search(rf"{base_name}_(\d+){re.escape(ext)}$", fname)
            if m:
                nums.append(int(m.group(1)))
        n = max(nums) + 1 if nums else 1
        return os.path.join(self.video_dir, f"{base_name}_{n}{ext}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = TimelapseApp()
    win.show()
    sys.exit(app.exec_())
