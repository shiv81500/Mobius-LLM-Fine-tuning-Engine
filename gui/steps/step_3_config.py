"""
Step 3: Hyperparameters Configuration
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QFormLayout, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from api.backend_client import BackendError
from utils.validators import (validate_learning_rate, validate_epochs,
                              validate_batch_size, validate_lora_alpha)


class CreateJobThread(QThread):
    """Thread for creating job."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, backend_client, project_name, dataset_id, base_model, hyperparameters):
        super().__init__()
        self.backend_client = backend_client
        self.project_name = project_name
        self.dataset_id = dataset_id
        self.base_model = base_model
        self.hyperparameters = hyperparameters

    def run(self):
        try:
            result = self.backend_client.create_job(
                self.project_name,
                self.dataset_id,
                self.base_model,
                self.hyperparameters
            )
            self.finished.emit(result)
        except BackendError as e:
            self.error.emit(e.message)
        except Exception as e:
            self.error.emit(str(e))


class Step3ConfigWidget(QWidget):
    """Step 3: Configure hyperparameters."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.create_job_thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("Configure Hyperparameters")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Learning rate
        self.lr_edit = QLineEdit("2e-4")
        self.lr_edit.setFixedHeight(35)
        form_layout.addRow("Learning Rate:", self.lr_edit)
        form_layout.addRow("", QLabel("Recommended: 2e-4 for Qwen/SmolLM fine-tuning"))

        # Epochs
        self.epochs_edit = QLineEdit("15")
        self.epochs_edit.setFixedHeight(35)
        form_layout.addRow("Number of Epochs:", self.epochs_edit)
        form_layout.addRow("", QLabel("⚠️ Small datasets (<50 examples) need 15-20 epochs"))

        # Batch size
        self.batch_size_edit = QLineEdit("1")
        self.batch_size_edit.setFixedHeight(35)
        form_layout.addRow("Batch Size:", self.batch_size_edit)
        form_layout.addRow("", QLabel("⚠️ CPU Mode: Use batch_size=1 for 7.8GB RAM"))

        # LoRA Rank
        self.lora_rank_combo = QComboBox()
        self.lora_rank_combo.setFixedHeight(35)
        self.lora_rank_combo.addItems(["4", "8", "16", "32", "64"])
        self.lora_rank_combo.setCurrentText("8")
        self.lora_rank_combo.currentTextChanged.connect(self.on_rank_changed)
        form_layout.addRow("LoRA Rank:", self.lora_rank_combo)
        form_layout.addRow("", QLabel("⚠️ CPU Mode: Use rank=8 for less memory"))

        # LoRA Alpha
        self.lora_alpha_edit = QLineEdit("16")
        self.lora_alpha_edit.setFixedHeight(35)
        form_layout.addRow("LoRA Alpha:", self.lora_alpha_edit)
        form_layout.addRow("", QLabel("Usually 2x the rank"))

        # Quantization
        self.quantization_combo = QComboBox()
        self.quantization_combo.setFixedHeight(35)
        self.quantization_combo.addItems(["Q4_K_M", "Q5_K_M", "Q8_0"])
        form_layout.addRow("GGUF Quantization:", self.quantization_combo)
        form_layout.addRow("", QLabel("Q4_K_M = smaller, Q8_0 = highest quality"))

        # Low-RAM defaults note (applied silently)
        form_layout.addRow("", QLabel("Low-RAM mode: batch=1, gradAccum=8, maxLen=256, stream on"))

        layout.addLayout(form_layout)
        layout.addStretch()

    def on_rank_changed(self, rank_str):
        """Auto-update alpha to 2x rank."""
        try:
            rank = int(rank_str)
            self.lora_alpha_edit.setText(str(rank * 2))
        except:
            pass

    def validate(self):
        """Validate all hyperparameters."""
        # Validate learning rate
        valid, error = validate_learning_rate(self.lr_edit.text())
        if not valid:
            self.lr_edit.setStyleSheet("border: 2px solid red;")
            return False, error
        self.lr_edit.setStyleSheet("")

        # Validate epochs
        valid, error = validate_epochs(self.epochs_edit.text())
        if not valid:
            self.epochs_edit.setStyleSheet("border: 2px solid red;")
            return False, error
        self.epochs_edit.setStyleSheet("")

        # Validate batch size
        valid, error = validate_batch_size(self.batch_size_edit.text())
        if not valid:
            self.batch_size_edit.setStyleSheet("border: 2px solid red;")
            return False, error
        self.batch_size_edit.setStyleSheet("")

        # Validate LoRA alpha
        valid, error = validate_lora_alpha(self.lora_alpha_edit.text())
        if not valid:
            self.lora_alpha_edit.setStyleSheet("border: 2px solid red;")
            return False, error
        self.lora_alpha_edit.setStyleSheet("")

        return True, ""

    def save_data(self):
        """Save hyperparameters and create job."""
        hyperparameters = {
            "learningRate": float(self.lr_edit.text()),
            "epochs": int(self.epochs_edit.text()),
            "batchSize": int(self.batch_size_edit.text()),
            "loraRank": int(self.lora_rank_combo.currentText()),
            "loraAlpha": int(self.lora_alpha_edit.text()),
            "quantization": self.quantization_combo.currentText(),
            # Hidden low-RAM defaults (used by backend and trainer)
            "gradAccum": 16,
            "maxLength": 128,
            "stream": True,
        }

        self.main_window.hyperparameters = hyperparameters

        # Create job
        self.create_job_thread = CreateJobThread(
            self.main_window.backend_client,
            self.main_window.project_name,
            self.main_window.dataset_id,
            self.main_window.base_model,
            hyperparameters
        )
        self.create_job_thread.finished.connect(self.on_job_created)
        self.create_job_thread.error.connect(self.on_job_error)
        self.create_job_thread.start()

        # Wait for job creation
        self.create_job_thread.wait()

    def on_job_created(self, result):
        """Handle successful job creation."""
        self.main_window.job_id = result['jobId']

    def on_job_error(self, error_message):
        """Handle job creation error."""
        QMessageBox.critical(self, "Error", f"Failed to create job: {error_message}")
