# Timelapse GUI

## 📸 Описание (Русский)

**Timelapse GUI** — это настольное приложение на Python (PyQt5), позволяющее снимать timelapse-видео с веб-камеры.  
Программа сохраняет кадры с заданным интервалом, а затем собирает их в видео при помощи **FFmpeg**.  
Поддерживаются форматы **16:9** и **9:16** (портретная и ландшафтная ориентации) без искажений и растяжений.

### ✨ Возможности
- Выбор камеры (автоматическое определение доступных).
- Настройка разрешения (включая портретные режимы).
- Поддержка соотношений сторон **16:9** и **9:16**.
- Задание FPS итогового видео.
- Настройка интервала съёмки (секунды).
- Предпросмотр изображения в реальном времени.
- Сохранение отдельных фото.
- Выбор папки для кадров и итогового видео.
- Опция «Сохранять фотографии» (или удалять после сборки).
- Автоматическая сборка timelapse-видео с помощью FFmpeg.

### 🛠 Требования
- Python 3.8+
- [PyQt5](https://pypi.org/project/PyQt5/)
- [OpenCV](https://pypi.org/project/opencv-python/)
- [FFmpeg](https://ffmpeg.org/) (должен быть установлен и доступен в `PATH`)

Установка зависимостей:
bash
pip install PyQt5 opencv-python
📂 Структура проекта

timelapse_gui.py — основной код приложения.

Папка photo/ — кадры timelapse (если включена опция сохранения).

Папка video/ — итоговые ролики.

📸 Description (English)

Timelapse GUI is a desktop application written in Python (PyQt5) for creating timelapse videos using a webcam.
The program captures frames at a user-defined interval and compiles them into a video using FFmpeg.
It supports 16:9 and 9:16 aspect ratios without stretching or distortion.

✨ Features

Camera selection (auto-detects available devices).

Resolution settings (including portrait modes).

Aspect ratio support: 16:9 and 9:16.

Adjustable FPS for the final video.

Custom capture interval (seconds).

Live preview window.

Save snapshots manually.

Choose folders for photos and video output.

Option to keep or delete frames after rendering.

Automatic timelapse video creation with FFmpeg.

🛠 Requirements

Python 3.8+

PyQt5

OpenCV

FFmpeg
 (must be installed and available in PATH)

Install dependencies:

pip install PyQt5 opencv-python

▶ Run
python timelapse_gui.py

📂 Project structure

timelapse_gui.py — main application code.

photo/ — captured frames (if saving is enabled).

video/ — rendered timelapse videos.

---
