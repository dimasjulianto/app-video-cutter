# gui.py
import json
import logging
import os
import subprocess
import sys
import time
import webbrowser

from datetime import datetime

from cutting_video import cut_video
from gpu_utils import GPUDetector
from PyQt6.QtCore import QObject, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPixmap, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
                            QDialogButtonBox, QFileDialog, QGridLayout,
                            QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                            QMainWindow, QMessageBox, QProgressBar,
                            QPushButton, QScrollArea, QSlider, QTextBrowser,
                            QTextEdit, QVBoxLayout, QWidget)

# Konfigurasi Logging
logging.basicConfig(
    level=logging.DEBUG,  # Ubah level logging ke DEBUG untuk lebih banyak informasi
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format log
)

class WelcomeDialog(QDialog):
    dialog_closed = pyqtSignal(bool)  # Emit sinyal saat dialog ditutup

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Advanced Video Cutter")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setMinimumHeight(570)

        layout = QVBoxLayout()

        # Judul
        title_label = QLabel("Advanced Video Cutter")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2196F3;
                margin: 8px;
            }
        """
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Versi
        version_label = QLabel("Version 1.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #666;")
        layout.addWidget(version_label)

        # Terms of Use menggunakan QTextBrowser sebagai pengganti QTextEdit
        self.terms_text = QTextBrowser()
        self.terms_text.setOpenExternalLinks(True)  # Mengaktifkan link eksternal
        self.terms_text.setHtml(
            """
            <h3>Terms of Use</h3>
            <p>Welcome to Advanced Video Cutter! Before using this application, please read and agree to the following terms:</p>
            
            <ol>
                <li><b>Usage Agreement:</b> This software is provided as-is, without any warranties.</li>
                <li><b>Responsibility:</b> Users are responsible for ensuring they have the right to process the videos.</li>
                <li><b>Performance:</b> Processing speed depends on your hardware capabilities.</li>
                <li><b>System Requirements:</b>
                    <ul>
                        <li>Windows 10 or later</li>
                        <li>4GB RAM minimum</li>
                        <li>GPU with hardware encoding support (recommended)</li>
                    </ul>
                </li>
            </ol>
            
            <p><b>Features:</b></p>
            <ul>
                <li>Automatic video cutting with customizable intervals</li>
                <li>GPU acceleration support</li>
                <li>Multi-threading capabilities</li>
                <li>Progress tracking and logging</li>
            </ul>
            
            <p>Support or donations, please visit: 
            <a href="https://saweria.co/dcidstream" style="color: #2196F3; text-decoration: underline;">
                Saweria - DcidStream
            </a></p>
            <p>Author Dimas Julianto, social media: 
            <a href="https://facebook.com/dimasjulianto" style="color: #2196F3; text-decoration: underline;">
                Facebook - Dimas Julianto
            </a></p>
        """
        )
        layout.addWidget(self.terms_text)

        # Checkbox untuk agreement
        self.agree_checkbox = QCheckBox("I have read and agree to the Terms of Use")
        layout.addWidget(self.agree_checkbox)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Disable OK button until checkbox is checked
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)
        self.agree_checkbox.stateChanged.connect(self.enable_ok_button)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def enable_ok_button(self, state):
        self.ok_button.setEnabled(state == Qt.CheckState.Checked.value)
    def reject(self):
        """Cegah pengguna menutup dialog tanpa menyetujui."""
        QMessageBox.warning(
            self,
            "Action Required",
            "You must agree to the Terms of Use to proceed.",
            QMessageBox.StandardButton.Ok,
        )

    def accept(self):
        super().accept()
        self.dialog_closed.emit(True)  # Emit sinyal saat pengguna menerima dialog

class LogFormatter(logging.Formatter):
    """Custom formatter that includes colors based on log level"""

    COLORS = {
        logging.DEBUG: QColor(128, 128, 128),  # Gray
        logging.INFO: QColor(0, 128, 0),  # Green
        logging.WARNING: QColor(255, 165, 0),  # Orange
        logging.ERROR: QColor(255, 0, 0),  # Red
        logging.CRITICAL: QColor(139, 0, 0),  # Dark Red
    }

    def format(self, record):
        return f"{datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} - {record.levelname} - {record.getMessage()}"


class GUILogger(logging.Handler):
    """Enhanced GUI Logger with color support and auto-scroll"""

    def __init__(self, log_widget):
        super().__init__()
        self.log_widget = log_widget
        self.formatter = LogFormatter()

    def emit(self, record):
        msg = self.formatter.format(record)
        color = LogFormatter.COLORS.get(record.levelno, QColor(0, 0, 0))

        # Create text format with the appropriate color
        fmt = QTextCharFormat()
        fmt.setForeground(color)

        # Get cursor and preserve its position
        cursor = self.log_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Insert the text with the format
        cursor.insertText(msg + "\n", fmt)

        # Auto-scroll to bottom
        self.log_widget.setTextCursor(cursor)
        self.log_widget.ensureCursorVisible()


class VideoProcessSignals(QObject):
    progress = pyqtSignal(int, int, str)  # Untuk log dan status
    progress_percent = pyqtSignal(int)  # Untuk progress bar
    status_update = pyqtSignal(str)  # Untuk status pesan
    finished = pyqtSignal(bool)  # Untuk selesai atau gagal
    error = pyqtSignal(str)  # Untuk menangkap error


class GpuDetectionThread(QThread):
    detected_gpus = pyqtSignal(list)

    def run(self):
        try:
            gpu_detector = GPUDetector()
            detected_gpus = gpu_detector.detect_gpus()
            for gpu in detected_gpus:
                logging.info(f"Found {gpu['type']} GPU: {gpu['name']}")
            self.detected_gpus.emit(detected_gpus)
        except Exception as e:
            logging.error(f"Error detecting GPUs: {str(e)}")
            self.detected_gpus.emit([])  # Kirim daftar kosong jika terjadi error


class VideoCutterApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Inisialisasi UI utama
        self.initUI()
        self.setup_logging()

        # Tampilkan aplikasi utama
        self.show()
        self.center_window()

        # Tampilkan WelcomeDialog
        self.show_welcome_dialog()

        self.worker = None
        self.load_cache()
        self.last_input_dir = None
        self.last_output_dir = None

    def center_window(self):
        """Tempatkan aplikasi utama di tengah layar."""
        screen_geometry = QApplication.primaryScreen().geometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

    def enable_ok_button(self, state):
        logging.info(f"Checkbox state changed: {state}")
        self.ok_button.setEnabled(state == Qt.CheckState.Checked.value)

    def show_welcome_dialog(self):
        """Tampilkan WelcomeDialog secara non-blokir."""
        self.welcome_dialog = WelcomeDialog(self)
        self.welcome_dialog.setModal(False)  # Set dialog menjadi non-modal
        self.welcome_dialog.dialog_closed.connect(self.handle_welcome_dialog_close)
        self.welcome_dialog.show()

    def handle_welcome_dialog_close(self, accepted):
        logging.info(f"Welcome to Advance Video Cutting v1.0: {accepted}")
        if accepted:
            logging.info("User accepted. Starting GPU detection.")
            self.start_gpu_detection()  # Mulai deteksi GPU
        else:
            logging.info("User rejected. Exiting application.")
            # Tampilkan dialog konfirmasi keluar
            self.confirm_exit()

    def confirm_exit(self):
        """Tampilkan dialog konfirmasi keluar hanya sekali"""
        reply = QMessageBox.question(
            self,
            "Exit",
            "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            QApplication.quit()
        else:
            logging.info("User canceled exit.")


    def start_gpu_detection(self):
        """Mulai proses deteksi GPU di latar belakang."""
        logging.info("Starting GPU detection thread.")
        self.gpu_thread = GpuDetectionThread()
        self.gpu_thread.detected_gpus.connect(self.show_gpu_info)
        self.gpu_thread.start()

    def show_gpu_info(self, gpu_info):
        """Tampilkan informasi GPU setelah selesai deteksi."""
        if gpu_info:
            message = "\n".join([f"{gpu['name']} ({gpu['type']})" for gpu in gpu_info])
            QMessageBox.information(
                self,
                "Detected GPUs",
                f"The following GPUs were detected:\n\n{message}",
                QMessageBox.StandardButton.Ok,
            )
        else:
            QMessageBox.warning(
                self,
                "GPU Detection",
                "No GPUs were detected or an error occurred.",
                QMessageBox.StandardButton.Ok,
            )

    def get_gpu_info(self):
        """Ambil informasi GPU menggunakan GPUDetector."""
        try:
            self.gpu_detector = GPUDetector()
            detected_gpus = self.gpu_detector.detect_gpus()
            for gpu in detected_gpus:
                logging.info(f"Found {gpu['type']} GPU: {gpu['name']}")
            return detected_gpus
        except Exception as e:
            logging.error(f"Error detecting GPUs: {str(e)}")
            return []

    def run(self):
        """Run video cutting process"""
        try:
            from cutting_video import cut_video

            def progress_callback(current, total, message):
                if not self.is_running:
                    # Gunakan return untuk keluar dengan bersih tanpa raise exception
                    return False
                progress_percentage = int((current / total) * 100)
                self.signals.progress.emit(current, total, message)
                self.signals.progress_percent.emit(progress_percentage)
                self.signals.status_update.emit(message)
                return True

            # Pass encoder to cut_video function
            if self.is_running:  # Cek sebelum memulai proses
                cut_video(
                    self.input_video,
                    self.output_dir,
                    max_workers=self.threads,
                    clip_duration=self.clip_duration,
                    skip_duration=self.skip_duration,
                    encoder=self.encoder,
                    progress_callback=progress_callback,
                )
                if self.is_running:  # Cek lagi setelah proses selesai
                    self.signals.finished.emit(True)
                else:
                    self.signals.status_update.emit("Process cancelled by user")
            else:
                self.signals.status_update.emit("Process cancelled before starting")
                
        except Exception as e:
            if not self.is_running:
                self.signals.status_update.emit("Process cancelled by user")
            else:
                self.signals.error.emit(str(e))
            self.signals.finished.emit(False)

    def stop(self):
        """Hentikan proses worker dengan bersih"""
        self.is_running = False
        self.signals.status_update.emit("Cancelling process...")

    def save_cache(self):
        """Simpan input video dan output folder ke cache."""
        try:
            cache_data = {
                "last_input_video": (
                    self.input_video if isinstance(self.input_video, str) else None
                ),
                "last_output_folder": (
                    self.output_folder if isinstance(self.output_folder, str) else None
                ),
                "last_input_dir": (
                    self.last_input_dir
                    if isinstance(self.last_input_dir, str)
                    else None
                ),
                "last_output_dir": (
                    self.last_output_dir
                    if isinstance(self.last_output_dir, str)
                    else None
                ),
            }

            with open("cache.json", "w") as cache_file:
                json.dump(cache_data, cache_file)

            # Set file as hidden in Windows
            if os.name == "nt":  # Windows systems
                import ctypes

                FILE_ATTRIBUTE_HIDDEN = 0x02
                ret = ctypes.windll.kernel32.SetFileAttributesW(
                    "cache.json", FILE_ATTRIBUTE_HIDDEN
                )
                if ret == 0:  # If SetFileAttributesW fails
                    raise ctypes.WinError()
                logging.info("Cache file set as hidden")
        except Exception as e:
            logging.error(f"Failed to save cache: {str(e)}")

    def load_cache(self):
        """Muat input video dan output folder dari cache."""
        cache_file_path = "cache.json"
        if os.path.exists(cache_file_path):
            try:
                # Set file as hidden when loading if it's not already
                if os.name == "nt":
                    import ctypes

                    if not bool(os.stat(cache_file_path).st_file_attributes & 0x02):
                        FILE_ATTRIBUTE_HIDDEN = 0x02
                        ctypes.windll.kernel32.SetFileAttributesW(
                            cache_file_path, FILE_ATTRIBUTE_HIDDEN
                        )

                with open(cache_file_path, "r") as cache_file:
                    cache_data = json.load(cache_file)

                    # Validasi dan set data cache
                    self.input_video = cache_data.get("last_input_video", None)
                    self.output_folder = cache_data.get("last_output_folder", None)

                    # Validasi direktori input/output
                    last_input_dir = cache_data.get("last_input_dir", None)
                    self.last_input_dir = (
                        last_input_dir if isinstance(last_input_dir, str) else None
                    )

                    last_output_dir = cache_data.get("last_output_dir", None)
                    self.last_output_dir = (
                        last_output_dir if isinstance(last_output_dir, str) else None
                    )

                    # Update label jika ada data
                    if (
                        hasattr(self, "input_label")
                        and self.input_video
                        and isinstance(self.input_video, str)
                    ):
                        self.input_label.setText(
                            f"Input Video: {os.path.basename(self.input_video)}"
                        )
                    if (
                        hasattr(self, "output_label")
                        and self.output_folder
                        and isinstance(self.output_folder, str)
                    ):
                        self.output_label.setText(
                            f"Output Folder: {os.path.basename(self.output_folder)}"
                        )
            except Exception as e:
                logging.error(f"Failed to load cache: {str(e)}")

    def clear_cache(self):
        """Hapus file cache secara manual melalui GUI."""
        cache_file_path = "cache.json"
        try:
            if os.path.exists(cache_file_path):
                os.remove(cache_file_path)
                QMessageBox.information(
                    self, "Success", "Cache file has been successfully deleted."
                )
                logging.info("Cache file successfully deleted via GUI.")
            else:
                QMessageBox.warning(self, "Warning", "No cache file found to delete.")
                logging.warning("Attempted to delete cache, but no cache file found.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete cache file: {e}")
            logging.error(f"Failed to delete cache file: {e}")

    def setup_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Add GUI handler
        gui_handler = GUILogger(self.log_widget)
        logger.addHandler(gui_handler)

    def initUI(self):
        self.setWindowTitle("Advanced Video Cutter")
        self.setGeometry(
            100, 100, 700, 850
        )  # Lebar ditingkatkan untuk ruang sisi kanan

        # Layout Utama
        self.layout = QVBoxLayout()

        # Header
        header = QLabel("Advanced Video Cutter v1.0")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(header)

        # Grid Layout untuk Input, Output, dan Pengaturan
        grid_layout = QGridLayout()

        # Input Section
        input_group = QGroupBox("Input Settings")
        input_layout = QVBoxLayout()
        self.input_label = QLabel("Input Video: None")
        input_layout.addWidget(self.input_label)
        self.select_input_btn = QPushButton("Select Video")
        self.select_input_btn.clicked.connect(self.select_input_video)
        input_layout.addWidget(self.select_input_btn)
        input_group.setLayout(input_layout)
        grid_layout.addWidget(input_group, 0, 0)

        # Output Section
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()

        # Masukkan nama video
        self.title_label = QLabel("Video Title:")
        output_layout.addWidget(self.title_label)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter video title...")
        output_layout.addWidget(self.title_input)

        # Output folder
        self.output_label = QLabel("Output Folder: None")
        output_layout.addWidget(self.output_label)

        self.select_output_btn = QPushButton("Select Output Folder")
        self.select_output_btn.clicked.connect(self.select_output_folder)
        output_layout.addWidget(self.select_output_btn)

        output_group.setLayout(output_layout)
        grid_layout.addWidget(output_group, 0, 1)

        # Customize Settings
        settings_group = QGroupBox("Customize Settings")
        settings_layout = QVBoxLayout()

        self.threads_label = QLabel("Processing Threads: 4")
        self.threads_slider = QSlider(Qt.Orientation.Horizontal)
        self.threads_slider.setMinimum(1)
        self.threads_slider.setMaximum(16)
        self.threads_slider.setValue(4)
        self.threads_slider.valueChanged.connect(self.update_threads_label)
        settings_layout.addWidget(self.threads_label)
        settings_layout.addWidget(self.threads_slider)

        self.clip_duration_label = QLabel("Clip Duration: 3 seconds")
        self.clip_duration_slider = QSlider(Qt.Orientation.Horizontal)
        self.clip_duration_slider.setMinimum(1)
        self.clip_duration_slider.setMaximum(30)
        self.clip_duration_slider.setValue(3)
        self.clip_duration_slider.valueChanged.connect(self.update_clip_duration_label)
        settings_layout.addWidget(self.clip_duration_label)
        settings_layout.addWidget(self.clip_duration_slider)

        self.skip_duration_label = QLabel("Skip Duration: 10 seconds")
        self.skip_duration_slider = QSlider(Qt.Orientation.Horizontal)
        self.skip_duration_slider.setMinimum(1)
        self.skip_duration_slider.setMaximum(60)
        self.skip_duration_slider.setValue(10)
        self.skip_duration_slider.valueChanged.connect(self.update_skip_duration_label)
        settings_layout.addWidget(self.skip_duration_label)
        settings_layout.addWidget(self.skip_duration_slider)

        settings_group.setLayout(settings_layout)
        grid_layout.addWidget(settings_group, 1, 0, 1, 2)

        # GPU Settings
        gpu_group = QGroupBox("GPU Settings")
        gpu_layout = QVBoxLayout()

        # Deteksi GPU yang tersedia
        self.gpu_detector = GPUDetector()
        self.available_gpus = self.gpu_detector.detect_gpus()

        # Dropdown untuk memilih GPU
        self.gpu_combo = QComboBox()

        # Tambahkan GPU yang terdeteksi ke dalam dropdown
        for gpu in self.available_gpus:
            self.gpu_combo.addItem(f"{gpu['name']} ({gpu['type']})")

        # Pilih GPU yang direkomendasikan
        recommended_gpu = self.gpu_detector.get_recommended_gpu()
        if recommended_gpu:
            try:
                # Cari indeks GPU yang direkomendasikan
                for i, gpu in enumerate(self.available_gpus):
                    if (
                        gpu["name"] == recommended_gpu["name"]
                        and gpu["type"] == recommended_gpu["type"]
                        and gpu["encoder"] == recommended_gpu["encoder"]
                    ):
                        self.gpu_combo.setCurrentIndex(i)
                        break
            except Exception as e:
                logging.error(f"Error setting recommended GPU: {str(e)}")
                if self.gpu_combo.count() > 0:
                    self.gpu_combo.setCurrentIndex(0)

        gpu_layout.addWidget(QLabel("Select GPU:"))
        gpu_layout.addWidget(self.gpu_combo)

        # Tambahkan peringatan jika bukan NVIDIA GPU
        self.gpu_warning = QLabel("")
        self.gpu_warning.setStyleSheet("color: orange;")
        gpu_layout.addWidget(self.gpu_warning)

        # Perbarui peringatan berdasarkan GPU yang dipilih
        self.gpu_combo.currentIndexChanged.connect(self.on_gpu_changed)
        self.on_gpu_changed()  # Panggil sekali untuk mengatur peringatan awal

        gpu_group.setLayout(gpu_layout)
        grid_layout.addWidget(gpu_group, 2, 0, 1, 2)  # Tambahkan ke grid layout

        # Tambahkan Grid Layout ke Layout Utama
        self.layout.addLayout(grid_layout)

        # Progress Bar
        self.progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)
        self.progress_group.setLayout(progress_layout)
        self.layout.addWidget(self.progress_group)

        # Tombol Aksi
        button_layout = QHBoxLayout()

        # Tombol Start Cutting
        self.start_btn = QPushButton("Start Cutting")
        self.start_btn.clicked.connect(self.start_cutting)
        self.start_btn.setMinimumHeight(40)
        button_layout.addWidget(self.start_btn)

        # Tombol Cancel
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_cutting)
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setEnabled(False)  # Disabled by default
        button_layout.addWidget(self.cancel_btn)

        # Tombol Open Folder
        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.open_folder_btn.setMinimumHeight(40)
        button_layout.addWidget(self.open_folder_btn)

        # Tombol Next Video
        self.reset_button = QPushButton("Next Video")
        self.reset_button.clicked.connect(self.reset_form)
        self.reset_button.setMinimumHeight(40)
        button_layout.addWidget(self.reset_button)

        # Tombol Clear Cache
        self.clear_cache_btn = QPushButton("Clear Cache")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        self.clear_cache_btn.setMinimumHeight(40)
        button_layout.addWidget(self.clear_cache_btn)

        # Tambahkan Tombol Aksi ke Layout Utama
        self.layout.addLayout(button_layout)

        # Process Log
        log_group = QGroupBox("Info Log")
        log_layout = QVBoxLayout()
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setStyleSheet(
            """
            QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 5px;
            }
        """
        )
        log_layout.addWidget(self.log_widget)
        log_group.setLayout(log_layout)
        self.layout.addWidget(log_group)

        # Set Layout Utama
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        # Initialize variables
        self.input_video = None
        self.output_folder = None

    def cancel_cutting(self):
        """Handle cancel button click"""
        try:
            if self.worker and self.worker.isRunning():
                reply = QMessageBox.question(
                    self,
                    "Confirm Cancel",
                    "Are you sure you want to cancel the current process?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if reply == QMessageBox.StandardButton.Yes:
                    logging.info("Cancelling video cutting process...")
                    self.worker.stop()
                    self.worker.wait()  # Wait for thread to finish
                    self.status_label.setText("Process cancelled by user")
                    self.enable_controls(True)
                    logging.info("Video cutting process cancelled")

        except Exception as e:
            logging.error(f"Error during cancellation: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error during cancellation: {str(e)}")

    def on_gpu_changed(self):
        """Handle GPU selection change"""
        current_gpu = self.available_gpus[self.gpu_combo.currentIndex()]
        if current_gpu["type"] != "NVIDIA":
            self.gpu_warning.setText(
                "Warning: Non-NVIDIA GPUs might have limited performance"
            )
        else:
            self.gpu_warning.setText("")

    def open_donate_link(self):
        """Open a web page for donations."""
        import webbrowser

        donate_url = "https://saweria.co/dcidstream"  # Ganti dengan URL donasi Anda
        webbrowser.open(donate_url)

    def open_output_folder(self):
        """Open the output folder for the currently selected video title."""
        if not self.output_folder:
            QMessageBox.warning(self, "Error", "Output folder is not selected.")
            return

        # Ambil nama folder berdasarkan input video title
        video_title = self.title_input.text().strip()
        if not video_title:
            QMessageBox.warning(self, "Error", "Please enter a video title.")
            return

        # Gabungkan path output folder dengan nama video
        target_folder = os.path.join(self.output_folder, video_title)

        # Periksa apakah folder ada
        if os.path.exists(target_folder):
            # Membuka folder di file explorer sesuai OS
            if os.name == "nt":  # Windows
                os.startfile(target_folder)
            elif os.name == "posix":  # macOS atau Linux
                subprocess.run(["xdg-open", target_folder])
            else:
                QMessageBox.warning(self, "Error", "Cannot open folder on this OS.")
        else:
            QMessageBox.warning(
                self, "Error", f"The folder '{target_folder}' does not exist."
            )

    def update_threads_label(self):
        self.threads_label.setText(f"Processing Threads: {self.threads_slider.value()}")

    def update_clip_duration_label(self):
        self.clip_duration_label.setText(
            f"Clip Duration: {self.clip_duration_slider.value()} seconds"
        )

    def update_skip_duration_label(self):
        self.skip_duration_label.setText(
            f"Skip Duration: {self.skip_duration_slider.value()} seconds"
        )

    def select_input_video(self):
        initial_dir = self.last_input_dir if self.last_input_dir else ""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Input Video",
            initial_dir,
            "Video Files (*.mp4 *.mkv *.avi *.mov *.wmv);;All Files (*.*)",
        )
        if file_path:
            self.input_video = file_path
            self.input_label.setText(f"Input Video: {os.path.basename(file_path)}")
            logging.info(f"Selected input video: {file_path}")
            # Update last input directory
            self.last_input_dir = os.path.dirname(file_path)

    def select_output_folder(self):
        initial_dir = self.last_output_dir if self.last_output_dir else ""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", initial_dir
        )
        if folder_path:
            self.output_folder = folder_path
            self.output_label.setText(f"Output Folder: {os.path.basename(folder_path)}")
            logging.info(f"Selected output folder: {folder_path}")
            # Update last output directory
            self.last_output_dir = folder_path

    def reset_form(self):
        try:
            # Stop any running process
            if self.worker:
                self.worker.stop()
                self.worker.wait()
                self.worker = None

            # Reset input/output
            self.input_video = None
            self.input_label.setText("Input Video: None")

            # Pertahankan output folder
            if self.output_folder:
                self.output_label.setText(
                    f"Output Folder: {os.path.basename(self.output_folder)}"
                )
            else:
                self.output_label.setText("Output Folder: None")
            self.title_input.clear()

            # Reset sliders
            self.threads_slider.setValue(4)
            self.clip_duration_slider.setValue(3)
            self.skip_duration_slider.setValue(10)

            # Reset progress and status
            self.progress_bar.setValue(0)
            self.status_label.setText("Ready")

            # Clear log
            self.log_widget.clear()
            logging.info("Form reset - Ready for new video processing")

            # Re-enable all controls
            self.enable_controls(True)

            # Cleanup resources
            from cutting_video import cleanup_resources

            cleanup_resources()

        except Exception as e:
            logging.error(f"Error during reset: {str(e)}")
            QMessageBox.warning(self, "Reset Error", f"Error during reset: {str(e)}")

    def enable_controls(self, enabled=True):
        """Enable or disable all controls"""
        self.select_input_btn.setEnabled(enabled)
        self.select_output_btn.setEnabled(enabled)
        self.title_input.setEnabled(enabled)
        self.threads_slider.setEnabled(enabled)
        self.clip_duration_slider.setEnabled(enabled)
        self.skip_duration_slider.setEnabled(enabled)
        self.start_btn.setEnabled(enabled)
        # Toggle cancel button opposite to other controls
        self.cancel_btn.setEnabled(not enabled)
        # Keep reset button always enabled
        self.reset_button.setEnabled(True)

    def start_cutting(self):
        if not self.input_video or not self.output_folder:
            QMessageBox.warning(
                self, "Error", "Please select both input video and output folder."
            )
            return

        video_title = self.title_input.text().strip()
        if not video_title:
            QMessageBox.warning(self, "Error", "Please enter a video title.")
            return

        try:
            # Get selected GPU
            selected_gpu = self.available_gpus[self.gpu_combo.currentIndex()]
            logging.info(f"Using {selected_gpu['name']} for video processing")

            # Disable controls
            self.enable_controls(False)

            # Clear log and reset progress
            self.log_widget.clear()
            self.progress_bar.setValue(0)

            # Create output directory
            output_dir = os.path.join(self.output_folder, video_title)
            os.makedirs(output_dir, exist_ok=True)

            # Create and setup worker thread with GPU info
            self.worker = VideoCutterWorker(
                self.input_video,
                output_dir,
                self.threads_slider.value(),
                self.clip_duration_slider.value(),
                self.skip_duration_slider.value(),
                selected_gpu["encoder"],  # Pass encoder to worker
            )

            # Connect signals
            self.worker.signals.progress.connect(self.handle_progress)
            self.worker.signals.progress_percent.connect(self.update_progress)
            self.worker.signals.status_update.connect(self.update_status)
            self.worker.signals.finished.connect(self.process_finished)
            self.worker.signals.error.connect(self.handle_error)

            # Start processing
            self.worker.start()

        except Exception as e:
            logging.error(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            self.enable_controls(True)

    def handle_progress(self, current, total, message):
        progress_percentage = int((current / total) * 100)
        self.update_progress(progress_percentage)
        self.update_status(message)

    def handle_error(self, error_message):
        """Handle errors from the worker thread"""
        if "Process stopped by user" in error_message:
            # Ini adalah pemberhentian yang disengaja, bukan error
            logging.info("Video cutting process cancelled by user")
            self.status_label.setText("Process cancelled by user")
        else:
            # Ini adalah error yang sebenarnya
            logging.error(f"Error in worker thread: {error_message}")
            QMessageBox.critical(
                self, "Error", f"An error occurred during processing: {error_message}"
            )
        self.enable_controls(True)

    def update_log(self, message):
        """Update log with thread-safe handling"""
        logging.info(message)

    def update_progress(self, value):
        """Update progress bar dengan thread-safe handling"""
        self.progress_bar.setValue(value)

    def update_status(self, status):
        """Update status label dengan thread-safe handling"""
        self.status_label.setText(status)

    def process_finished(self, success):
        """Handle completion of video processing"""
        # Re-enable all controls
        self.enable_controls(True)

        if success:
            self.status_label.setText("Processing Complete!")
            output_path = os.path.join(
                self.output_folder, self.title_input.text().strip()
            )
            QMessageBox.information(
                self,
                "Success",
                f"Video cutting completed successfully!\n\nOutput saved to: {output_path}",
            )
        else:
            self.status_label.setText("Processing Failed!")

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            logging.info("User confirmed exit.")
            self.save_cache()
            event.accept()  # Mengizinkan aplikasi untuk menutup
        else:
            logging.info("User canceled exit.")
            event.ignore()  # Membatalkan proses keluar

    def cut_video(self):
        """Execute video cutting in main thread"""
        try:
            from cutting_video import cut_video

            # Setup progress monitoring
            def progress_callback(current_clip, total_clips, status_message):
                progress = int((current_clip / total_clips) * 100)
                self.progress_bar.setValue(progress)
                self.status_label.setText(status_message)
                logging.info(f"Progress: {progress}% - {status_message}")

            output_dir = os.path.join(
                self.output_folder, self.title_input.text().strip()
            )

            # Start cutting process with progress callback
            cut_video(
                self.input_video,
                output_dir,
                max_workers=self.threads_slider.value(),
                clip_duration=self.clip_duration_slider.value(),
                skip_duration=self.skip_duration_slider.value(),
                progress_callback=progress_callback,
            )

            # Update final status
            self.progress_bar.setValue(100)
            logging.info("Video cutting completed successfully!")
            self.worker.finished.emit(True)

        except Exception as e:
            logging.error(f"Error during video cutting: {str(e)}")
            self.worker.finished.emit(False)
            raise

    def process_finished(self, success):
        """Handle completion of video processing"""
        # Re-enable all controls
        self.enable_controls(True)

        if success:
            self.status_label.setText("Processing Complete! Ready for next video.")
            QMessageBox.information(
                self,
                "Success",
                f"Video cutting completed successfully!\n\nOutput saved to: {os.path.join(self.output_folder, self.title_input.text().strip())}",
            )
        else:
            self.status_label.setText("Processing Failed!")
            QMessageBox.critical(
                self,
                "Notice",
                "Canceled video cutting process. Please check the log for details.",
            )


class VideoCutterWorker(QThread):
    def __init__(
        self, input_video, output_dir, threads, clip_duration, skip_duration, encoder
    ):
        super().__init__()
        self.input_video = input_video
        self.output_dir = output_dir
        self.threads = threads
        self.clip_duration = clip_duration
        self.skip_duration = skip_duration
        self.encoder = encoder
        self.signals = VideoProcessSignals()
        self.is_running = True

    def run(self):
        """Run video cutting process"""
        try:
            from cutting_video import cut_video

            def progress_callback(current, total, message):
                if not self.is_running:
                    raise Exception("Process stopped by user")
                progress_percentage = int((current / total) * 100)
                self.signals.progress.emit(current, total, message)
                self.signals.progress_percent.emit(progress_percentage)
                self.signals.status_update.emit(message)

            # Pass encoder to cut_video function
            cut_video(
                self.input_video,
                self.output_dir,
                max_workers=self.threads,
                clip_duration=self.clip_duration,
                skip_duration=self.skip_duration,
                encoder=self.encoder,  # Add encoder parameter
                progress_callback=progress_callback,
            )
            self.signals.finished.emit(True)
        except Exception as e:
            self.signals.error.emit(str(e))
            self.signals.finished.emit(False)

    # Update start_cutting method in VideoCutterApp class
    def start_cutting(self):
        if not self.input_video or not self.output_folder:
            QMessageBox.warning(
                self, "Error", "Please select both input video and output folder."
            )
            return

        video_title = self.title_input.text().strip()
        if not video_title:
            QMessageBox.warning(self, "Error", "Please enter a video title.")
            return

        try:
            # Get selected GPU
            selected_gpu = self.available_gpus[self.gpu_combo.currentIndex()]
            logging.info(f"Using {selected_gpu['name']} for video processing")

            # Disable controls and enable cancel button
            self.enable_controls(False)

            # Clear log and reset progress
            self.log_widget.clear()
            self.progress_bar.setValue(0)

            # Create output directory
            output_dir = os.path.join(self.output_folder, video_title)
            os.makedirs(output_dir, exist_ok=True)

            # Create and setup worker thread
            self.worker = VideoCutterWorker(
                self.input_video,
                output_dir,
                self.threads_slider.value(),
                self.clip_duration_slider.value(),
                self.skip_duration_slider.value(),
                selected_gpu["encoder"],
            )

            # Connect signals
            self.worker.signals.progress.connect(self.handle_progress)
            self.worker.signals.progress_percent.connect(self.update_progress)
            self.worker.signals.status_update.connect(self.update_status)
            self.worker.signals.finished.connect(self.process_finished)
            self.worker.signals.error.connect(self.handle_error)

            # Start processing
            self.worker.start()

        except Exception as e:
            logging.error(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            self.enable_controls(True)

    def stop(self):
        """Hentikan proses worker"""
        self.is_running = False


if __name__ == "__main__":
    # Set up exception handling
    def handle_exception(exc_type, exc_value, exc_traceback):
        logging.error(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )
        sys.exit(1)

    sys.excepthook = handle_exception

    # Start application
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Create and show main window
    window = VideoCutterApp()
    window.show()

    sys.exit(app.exec())