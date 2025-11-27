from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                              QFileDialog, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import os

from api.backend_client import BackendError
from utils.formatters import format_duration


class ConversionMonitorThread(QThread):
    """Thread to monitor conversion progress."""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    status_update = pyqtSignal(dict)

    def __init__(self, backend_client, job_id):
        super().__init__()
        self.backend_client = backend_client
        self.job_id = job_id
        self.running = True

    def run(self):
        import time
        while self.running:
            try:
                conv = self.backend_client.get_conversion_status(self.job_id)
                self.status_update.emit(conv)
                if conv.get('phase') == 'CONVERSION_COMPLETED' and conv.get('fileExists'):
                    self.finished.emit()
                    return
                if conv.get('phase') == 'CONVERSION_FAILED':
                    self.error.emit('Conversion failed')
                    return
            except Exception as e:
                # Emit partial error but keep looping unless critical
                self.status_update.emit({'phase': 'UNKNOWN', 'error': str(e)})
            time.sleep(3)

    def stop(self):
        self.running = False


class DownloadThread(QThread):
    """Thread for downloading GGUF file."""
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, backend_client, job_id, save_path):
        super().__init__()
        self.backend_client = backend_client
        self.job_id = job_id
        self.save_path = save_path

    def run(self):
        try:
            self.backend_client.download_gguf(
                self.job_id,
                self.save_path,
                progress_callback=lambda downloaded, total: self.progress.emit(downloaded, total)
            )
            self.finished.emit(self.save_path)
        except BackendError as e:
            self.error.emit(e.message)
        except Exception as e:
            self.error.emit(str(e))


class Step5ExportWidget(QWidget):
    """Step 5: Export model as GGUF."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.conversion_monitor = None
        self.download_thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("Export Model")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Job summary section
        summary_title = QLabel("Job Summary")
        summary_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(summary_title)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("padding: 10px; background: #f5f5f5; border-radius: 5px;")
        layout.addWidget(self.summary_label)

        # GGUF conversion section
        conversion_title = QLabel("GGUF Conversion")
        conversion_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(conversion_title)

        self.quantization_label = QLabel()
        layout.addWidget(self.quantization_label)

        self.convert_button = QPushButton("Convert to GGUF")
        self.convert_button.setFixedHeight(40)
        self.convert_button.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_button)

        self.conversion_status_label = QLabel("Conversion status: Not started")
        layout.addWidget(self.conversion_status_label)

        self.conversion_detail_label = QLabel("")
        self.conversion_detail_label.setWordWrap(True)
        self.conversion_detail_label.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(self.conversion_detail_label)

        self.conversion_progress = QProgressBar()
        self.conversion_progress.setVisible(False)
        layout.addWidget(self.conversion_progress)

        # Download section
        download_title = QLabel("Download")
        download_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(download_title)

        self.download_button = QPushButton("Download GGUF Model")
        self.download_button.setFixedHeight(50)
        self.download_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px;")
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.download_gguf)
        layout.addWidget(self.download_button)

        self.download_progress = QProgressBar()
        self.download_progress.setVisible(False)
        layout.addWidget(self.download_progress)

        self.download_status_label = QLabel("")
        layout.addWidget(self.download_status_label)

        layout.addStretch()

    def on_step_enter(self):
        """Called when entering this step."""
        # Load job summary
        try:
            status = self.main_window.backend_client.get_job_status(self.main_window.job_id)

            project_name = status.get('projectName', 'N/A')
            base_model = status.get('baseModel', 'N/A')
            started_at = status.get('startedAt', '')
            completed_at = status.get('completedAt', '')

            duration = format_duration(started_at, completed_at) if started_at and completed_at else 'N/A'

            status_str = status.get('status', 'UNKNOWN')
            self.summary_label.setText(
                f"Project: {project_name}\n"
                f"Base Model: {base_model}\n"
                f"Status: {status_str}\n"
                f"Training Time: {duration}"
            )

            # Check quantization
            hyperparams = status.get('hyperparameters', {})
            quantization = hyperparams.get('quantization', 'Q4_K_M')
            self.quantization_label.setText(f"Quantization: {quantization}")

            # Check if GGUF already exists
            gguf_path = status.get('ggufPath')
            if gguf_path:
                self.convert_button.setVisible(False)
                self.conversion_status_label.setText("Conversion status: Complete")
                self.download_button.setEnabled(True)
            else:
                # Only allow conversion when training is completed
                if status_str == 'COMPLETED':
                    self.convert_button.setVisible(True)
                    self.convert_button.setEnabled(True)
                    self.conversion_status_label.setText("Conversion status: Not started")
                else:
                    self.convert_button.setVisible(True)
                    self.convert_button.setEnabled(False)
                    self.conversion_status_label.setText("Conversion status: Waiting for training to complete")
                self.download_button.setEnabled(False)

        except BackendError as e:
            QMessageBox.critical(self, "Error", f"Failed to load job status: {e.message}")

    def start_conversion(self):
        """Start GGUF conversion."""
        self.convert_button.setEnabled(False)
        self.conversion_progress.setVisible(True)
        self.conversion_progress.setRange(0, 0)  # Indeterminate
        self.conversion_status_label.setText("Conversion status: Converting...")

        try:
            self.main_window.backend_client.convert_to_gguf(self.main_window.job_id)

            # Start monitoring conversion
            self.conversion_monitor = ConversionMonitorThread(
                self.main_window.backend_client,
                self.main_window.job_id
            )
            self.conversion_monitor.finished.connect(self.on_conversion_complete)
            self.conversion_monitor.error.connect(self.on_conversion_error)
            self.conversion_monitor.status_update.connect(self.on_conversion_status_update)
            self.conversion_monitor.start()

        except BackendError as e:
            self.on_conversion_error(e.message)

    def on_conversion_complete(self):
        """Handle conversion completion."""
        self.conversion_progress.setVisible(False)
        self.conversion_status_label.setText("Conversion status: Complete!")
        self.download_button.setEnabled(True)

        if self.conversion_monitor:
            self.conversion_monitor.stop()

    def on_conversion_error(self, error_message):
        """Handle conversion error."""
        self.conversion_progress.setVisible(False)
        self.convert_button.setEnabled(True)
        self.conversion_status_label.setText(f"Conversion failed: {error_message}")
        QMessageBox.critical(self, "Conversion Error", error_message)

    def on_conversion_status_update(self, conv):
        """Update UI with detailed conversion status."""
        phase = conv.get('phase', 'UNKNOWN')
        file_exists = conv.get('fileExists')
        size_bytes = conv.get('fileSizeBytes', 0) or 0
        logs = conv.get('recentConversionLogs', [])
        # Show last 3 lines for brevity
        tail = logs[-3:] if logs else []
        tail_text = '\n'.join(tail)
        size_mb = f"{size_bytes/1024/1024:.2f} MB" if file_exists else "--"
        self.conversion_status_label.setText(f"Conversion status: {phase}")
        self.conversion_detail_label.setText(
            f"File ready: {file_exists} | Size: {size_mb}\nRecent logs:\n{tail_text}" if phase != 'CONVERSION_COMPLETED' else f"File ready: {file_exists} | Size: {size_mb}"
        )

    def download_gguf(self):
        """Download GGUF model file."""
        # Open save dialog
        default_name = f"{self.main_window.project_name}.gguf".replace(" ", "_")
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save GGUF Model",
            default_name,
            "GGUF Files (*.gguf);;All Files (*)"
        )

        if not save_path:
            return

        # Start download
        self.download_button.setEnabled(False)
        self.download_progress.setVisible(True)
        self.download_progress.setValue(0)
        self.download_status_label.setText("Downloading...")

        self.download_thread = DownloadThread(
            self.main_window.backend_client,
            self.main_window.job_id,
            save_path
        )
        self.download_thread.progress.connect(self.on_download_progress)
        self.download_thread.finished.connect(self.on_download_complete)
        self.download_thread.error.connect(self.on_download_error)
        self.download_thread.start()

    def on_download_progress(self, downloaded, total):
        """Update download progress."""
        if total > 0:
            progress = int((downloaded / total) * 100)
            self.download_progress.setValue(progress)

    def on_download_complete(self, file_path):
        """Handle download completion."""
        self.download_progress.setVisible(False)
        self.download_button.setEnabled(True)

        self.download_status_label.setText(f"✓ Model downloaded successfully to:\n{file_path}")
        self.download_status_label.setStyleSheet("color: green; font-weight: bold;")

        # Show success message with option to open folder
        reply = QMessageBox.information(
            self,
            "Download Complete",
            f"Model downloaded successfully!\n\nLocation: {file_path}\n\nWould you like to open the containing folder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            import subprocess
            import platform
            folder = os.path.dirname(file_path)

            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", folder])
            else:  # Linux
                subprocess.Popen(["xdg-open", folder])

    def on_download_error(self, error_message):
        """Handle download error."""
        self.download_progress.setVisible(False)
        self.download_button.setEnabled(True)
        self.download_status_label.setText(f"✗ Download failed: {error_message}")
        self.download_status_label.setStyleSheet("color: red; font-weight: bold;")
        QMessageBox.critical(self, "Download Error", error_message)

    def validate(self):
        """No validation needed for final step."""
        return True, ""

    def save_data(self):
        """No data to save."""
        pass
