"""
Step 2: Data Upload
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                              QFileDialog, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import os

from api.backend_client import BackendError
from utils.formatters import format_file_size


class UploadThread(QThread):
    """Thread for uploading dataset."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, backend_client, file_path, file_format):
        super().__init__()
        self.backend_client = backend_client
        self.file_path = file_path
        self.file_format = file_format

    def run(self):
        try:
            result = self.backend_client.upload_dataset(self.file_path, self.file_format)
            self.finished.emit(result)
        except BackendError as e:
            self.error.emit(e.message)
        except Exception as e:
            self.error.emit(str(e))


class Step2DataWidget(QWidget):
    """Step 2: Upload training data."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.selected_file = None
        self.uploaded = False
        self.upload_thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("Upload Training Data")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # File selection button
        self.choose_button = QPushButton("Choose File")
        self.choose_button.setFixedHeight(40)
        self.choose_button.clicked.connect(self.choose_file)
        layout.addWidget(self.choose_button)

        # Selected file info
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("padding: 10px; background: #f5f5f5; border-radius: 5px;")
        layout.addWidget(self.file_label)

        # Upload button
        self.upload_button = QPushButton("Upload to Backend")
        self.upload_button.setFixedHeight(40)
        self.upload_button.setEnabled(False)
        self.upload_button.clicked.connect(self.upload_file)
        layout.addWidget(self.upload_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Help text
        help_text = QLabel(
            "Supported formats:\n"
            "• JSONL: One JSON object per line with 'instruction' and 'response' keys\n"
            "• CSV: Tabular data with text columns\n"
            "• TXT: Plain text for completion-style training\n\n"
            "Maximum file size: 10GB"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666; padding: 10px; background: #f5f5f5; border-radius: 5px;")
        layout.addWidget(help_text)

        layout.addStretch()

    def choose_file(self):
        """Open file dialog to choose dataset file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Training Data File",
            "",
            "Data Files (*.jsonl *.csv *.txt);;All Files (*)"
        )

        if file_path:
            self.selected_file = file_path
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            self.file_label.setText(
                f"Selected: {file_name}\n"
                f"Size: {format_file_size(file_size)}"
            )

            self.upload_button.setEnabled(True)
            self.uploaded = False
            self.status_label.setText("")

    def upload_file(self):
        """Upload selected file to backend."""
        if not self.selected_file:
            return

        # Determine format from extension
        ext = os.path.splitext(self.selected_file)[1].lower()
        format_map = {'.jsonl': 'jsonl', '.csv': 'csv', '.txt': 'txt'}
        file_format = format_map.get(ext, 'jsonl')

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.upload_button.setEnabled(False)
        self.choose_button.setEnabled(False)
        self.status_label.setText("Uploading...")

        # Start upload thread
        self.upload_thread = UploadThread(
            self.main_window.backend_client,
            self.selected_file,
            file_format
        )
        self.upload_thread.finished.connect(self.on_upload_success)
        self.upload_thread.error.connect(self.on_upload_error)
        self.upload_thread.start()

    def on_upload_success(self, result):
        """Handle successful upload."""
        self.progress_bar.setVisible(False)
        self.uploaded = True

        dataset_id = result['datasetId']
        row_count = result['rowCount']

        self.main_window.dataset_id = dataset_id

        self.status_label.setText(
            f"✓ Upload successful!\n"
            f"Dataset ID: {dataset_id}\n"
            f"Training examples: {row_count}"
        )
        self.status_label.setStyleSheet("color: green; font-weight: bold;")

        self.choose_button.setEnabled(True)

    def on_upload_error(self, error_message):
        """Handle upload error."""
        self.progress_bar.setVisible(False)
        self.upload_button.setEnabled(True)
        self.choose_button.setEnabled(True)

        self.status_label.setText(f"✗ Upload failed: {error_message}")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

        QMessageBox.critical(self, "Upload Error", error_message)

    def validate(self):
        """Validate that dataset has been uploaded."""
        if not self.uploaded:
            return False, "Please upload training data first"
        return True, ""

    def save_data(self):
        """Data already saved in on_upload_success."""
        pass
