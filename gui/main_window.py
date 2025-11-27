"""
Main wizard window for LLM Training GUI.
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from api.backend_client import BackendClient
from steps.step_1_project import Step1ProjectWidget
from steps.step_2_data import Step2DataWidget
from steps.step_3_config import Step3ConfigWidget
from steps.step_4_training import Step4TrainingWidget
from steps.step_5_export import Step5ExportWidget


class MainWindow(QMainWindow):
    """Main wizard window with 5 steps."""

    def __init__(self, backend_client: BackendClient):
        super().__init__()
        self.backend_client = backend_client

        # Project state
        self.project_name = None
        self.base_model = None
        self.dataset_id = None
        self.hyperparameters = None
        self.job_id = None

        self.current_step = 0
        self.total_steps = 5

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Mobius LLM Fine-Tuning Engine")
        self.setMinimumSize(900, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title_label = QLabel("Mobius LLM Fine-Tuning Engine")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Progress indicator
        self.progress_label = QLabel("Step 1 of 5: Project Setup")
        progress_font = QFont()
        progress_font.setPointSize(12)
        self.progress_label.setFont(progress_font)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("color: #555; padding: 10px;")
        main_layout.addWidget(self.progress_label)

        # Step content area (stacked widget)
        self.stacked_widget = QStackedWidget()

        # Create step widgets
        self.step1 = Step1ProjectWidget(self)
        self.step2 = Step2DataWidget(self)
        self.step3 = Step3ConfigWidget(self)
        self.step4 = Step4TrainingWidget(self)
        self.step5 = Step5ExportWidget(self)

        self.stacked_widget.addWidget(self.step1)
        self.stacked_widget.addWidget(self.step2)
        self.stacked_widget.addWidget(self.step3)
        self.stacked_widget.addWidget(self.step4)
        self.stacked_widget.addWidget(self.step5)

        main_layout.addWidget(self.stacked_widget, stretch=1)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)

        self.back_button = QPushButton("← Back")
        self.back_button.setFixedHeight(40)
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setEnabled(False)

        self.next_button = QPushButton("Next →")
        self.next_button.setFixedHeight(40)
        self.next_button.clicked.connect(self.go_next)

        nav_layout.addWidget(self.back_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_button)

        main_layout.addLayout(nav_layout)

        # Set initial step
        self.update_ui()

    def update_ui(self):
        """Update UI based on current step."""
        self.stacked_widget.setCurrentIndex(self.current_step)

        # Update progress label
        step_names = ["Project Setup", "Upload Data", "Configure Training", "Training", "Export Model"]
        self.progress_label.setText(f"Step {self.current_step + 1} of {self.total_steps}: {step_names[self.current_step]}")

        # Update button states
        self.back_button.setEnabled(self.current_step > 0)

        if self.current_step == 4:
            self.next_button.setText("Finish")
        else:
            self.next_button.setText("Next →")

    def go_back(self):
        """Go to previous step."""
        if self.current_step > 0:
            # Special handling for step 4 (training)
            if self.current_step == 4:
                reply = QMessageBox.question(
                    self,
                    "Confirm",
                    "Going back will abandon this training job. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

                # Cancel job if running
                if self.job_id:
                    try:
                        self.backend_client.cancel_job(self.job_id)
                    except:
                        pass
                    self.job_id = None

            self.current_step -= 1
            self.update_ui()

    def go_next(self):
        """Go to next step or finish."""
        # Validate current step
        current_widget = self.stacked_widget.currentWidget()
        if hasattr(current_widget, 'validate'):
            valid, error_message = current_widget.validate()
            if not valid:
                QMessageBox.warning(self, "Validation Error", error_message)
                return

        # Save data from current step
        if hasattr(current_widget, 'save_data'):
            current_widget.save_data()

        # Move to next step or finish
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
            self.update_ui()

            # Trigger step entry actions
            next_widget = self.stacked_widget.currentWidget()
            if hasattr(next_widget, 'on_step_enter'):
                next_widget.on_step_enter()
        else:
            # Finish button clicked
            self.handle_finish()

    def handle_finish(self):
        """Handle finish button click."""
        reply = QMessageBox.question(
            self,
            "Close Application",
            "What would you like to do?",
            QMessageBox.StandardButton.Close | QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Close:
            self.close()

    def closeEvent(self, event):
        """Handle window close event."""
        # Check if training is running
        if self.current_step == 3 and self.job_id:  # Step 4 (index 3)
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Training is in progress. Closing will not stop training but you'll lose visibility. Close anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        event.accept()
