"""
Step 1: Project Setup
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                              QComboBox, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from utils.validators import validate_project_name


class Step1ProjectWidget(QWidget):
    """Step 1: Project name and base model selection."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("Project Setup")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Project name field
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText("My Fine-Tune Project")
        self.project_name_edit.setFixedHeight(35)
        form_layout.addRow("Project Name:", self.project_name_edit)

        # Base model dropdown
        self.base_model_combo = QComboBox()
        self.base_model_combo.setFixedHeight(35)
        self.base_model_combo.addItems([
            "Qwen/Qwen2-0.5B-Instruct",  # ⭐ BEST - Instruction-tuned, 500M
            "HuggingFaceTB/SmolLM-360M-Instruct",  # Fastest, 360M
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0",  # Good for chat, 1.1B
            "microsoft/phi-2",  # 2.7B - Slower but capable
            "--- NOT for Q&A (completion only) ---",
            "distilgpt2",  # 82M - Testing only
            "gpt2",  # 124M - Completion only
            "--- GPU Models (Requires 8GB+ VRAM) ---",
            "meta-llama/Llama-3.2-3B",
            "meta-llama/Llama-3-8B",
            "mistralai/Mistral-7B-v0.2",
            "microsoft/Phi-3-mini-4k-instruct"
        ])
        form_layout.addRow("Base Model:", self.base_model_combo)

        layout.addLayout(form_layout)

        # Help text
        help_text = QLabel(
            "⭐ RECOMMENDED: Qwen2-0.5B-Instruct or SmolLM-360M-Instruct\n"
            "   These are instruction-tuned and work best for Q&A data.\n\n"
            "⚠️ AVOID: DistilGPT2/GPT-2 for Q&A tasks (they're completion models)\n\n"
            "💡 Your Ryzen 5 2500U + 8GB RAM can train models up to ~1B params."
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666; padding: 10px; background: #fff3cd; border-radius: 5px; border: 1px solid #ffc107;")
        layout.addWidget(help_text)

        layout.addStretch()

    def validate(self):
        """Validate inputs."""
        project_name = self.project_name_edit.text().strip()
        valid, error = validate_project_name(project_name)
        return valid, error

    def save_data(self):
        """Save data to main window state."""
        self.main_window.project_name = self.project_name_edit.text().strip()
        self.main_window.base_model = self.base_model_combo.currentText()
