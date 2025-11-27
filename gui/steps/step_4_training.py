"""
Step 4: Training Control and Monitoring
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTextEdit, QGridLayout, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from api.backend_client import BackendError
from utils.formatters import format_metric_value


class Step4TrainingWidget(QWidget):
    """Step 4: Training control and live monitoring."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.status_timer = None
        self.metrics_timer = None
        self.logs_timer = None
        self.current_status = "QUEUED"
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("Training")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Status label
        self.status_label = QLabel("Status: QUEUED")
        status_font = QFont()
        status_font.setPointSize(12)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        layout.addWidget(self.status_label)

        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.start_button = QPushButton("Start Training")
        self.start_button.setFixedHeight(40)
        self.start_button.clicked.connect(self.start_training)
        button_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.setFixedHeight(40)
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause_training)
        button_layout.addWidget(self.pause_button)

        self.resume_button = QPushButton("Resume")
        self.resume_button.setFixedHeight(40)
        self.resume_button.setEnabled(False)
        self.resume_button.clicked.connect(self.resume_training)
        button_layout.addWidget(self.resume_button)

        self.cancel_button = QPushButton("Cancel Training")
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_training)
        button_layout.addWidget(self.cancel_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Metrics panel
        metrics_title = QLabel("Training Metrics")
        metrics_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(metrics_title)

        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(10)

        # Create metric labels
        self.loss_label = QLabel("Loss: —")
        self.epoch_label = QLabel("Epoch: —")
        self.step_label = QLabel("Step: —")
        self.speed_label = QLabel("Speed: —")

        for label in [self.loss_label, self.epoch_label, self.step_label, self.speed_label]:
            label.setStyleSheet("padding: 10px; background: #f5f5f5; border-radius: 5px; font-weight: bold;")

        metrics_layout.addWidget(self.loss_label, 0, 0)
        metrics_layout.addWidget(self.epoch_label, 0, 1)
        metrics_layout.addWidget(self.step_label, 1, 0)
        metrics_layout.addWidget(self.speed_label, 1, 1)

        layout.addLayout(metrics_layout)

        # Log viewer
        logs_title = QLabel("Training Logs")
        logs_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(logs_title)

        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setFont(QFont("Courier", 9))
        self.log_viewer.setStyleSheet("background: #2b2b2b; color: #f5f5f5; border: 1px solid #555;")
        layout.addWidget(self.log_viewer, stretch=1)

    def on_step_enter(self):
        """Called when entering this step."""
        # Start polling
        self.start_polling()

    def start_polling(self):
        """Start polling timers."""
        # Status timer (every 5 seconds)
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)

        # Metrics timer (every 3 seconds)
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.update_metrics)
        self.metrics_timer.start(3000)

        # Logs timer (every 2 seconds)
        self.logs_timer = QTimer(self)
        self.logs_timer.timeout.connect(self.update_logs)
        self.logs_timer.start(2000)

    def stop_polling(self):
        """Stop polling timers."""
        if self.status_timer:
            self.status_timer.stop()
        if self.metrics_timer:
            self.metrics_timer.stop()
        if self.logs_timer:
            self.logs_timer.stop()

    def start_training(self):
        """Start training job."""
        self.start_button.setEnabled(False)
        self.start_button.setText("Starting...")

        try:
            self.main_window.backend_client.start_job(self.main_window.job_id)
            self.current_status = "RUNNING"
            self.update_button_states()
        except BackendError as e:
            QMessageBox.critical(self, "Error", f"Failed to start training: {e.message}")
            self.start_button.setEnabled(True)
            self.start_button.setText("Start Training")

    def pause_training(self):
        """Pause training job."""
        try:
            self.main_window.backend_client.pause_job(self.main_window.job_id)
            self.current_status = "PAUSED"
            self.update_button_states()
        except BackendError as e:
            QMessageBox.critical(self, "Error", f"Failed to pause training: {e.message}")

    def resume_training(self):
        """Resume paused training job."""
        try:
            self.main_window.backend_client.resume_job(self.main_window.job_id)
            self.current_status = "RUNNING"
            self.update_button_states()
        except BackendError as e:
            QMessageBox.critical(self, "Error", f"Failed to resume training: {e.message}")

    def cancel_training(self):
        """Cancel training job."""
        reply = QMessageBox.question(
            self,
            "Confirm Cancel",
            "Are you sure you want to cancel training? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.main_window.backend_client.cancel_job(self.main_window.job_id)
                self.current_status = "CANCELLED"
                self.update_button_states()
                self.stop_polling()
            except BackendError as e:
                QMessageBox.critical(self, "Error", f"Failed to cancel training: {e.message}")

    def update_status(self):
        """Update job status from backend."""
        try:
            status_data = self.main_window.backend_client.get_job_status(self.main_window.job_id)
            self.current_status = status_data['status']
            self.status_label.setText(f"Status: {self.current_status}")

            self.update_button_states()

            # Check if completed or failed
            if self.current_status == "COMPLETED":
                self.stop_polling()
                QMessageBox.information(self, "Success", "Training completed successfully!")
                self.main_window.next_button.setEnabled(True)
            elif self.current_status == "FAILED":
                self.stop_polling()
                QMessageBox.critical(self, "Error", "Training failed. Check logs for details.")

        except BackendError as e:
            pass  # Ignore polling errors

    def update_metrics(self):
        """Update training metrics from backend."""
        try:
            metrics = self.main_window.backend_client.get_job_metrics(self.main_window.job_id)

            loss = format_metric_value(metrics.get('loss'))
            epoch = metrics.get('epoch')
            total_epochs = metrics.get('totalEpochs')
            step = format_metric_value(metrics.get('step'))
            speed = format_metric_value(metrics.get('samplesPerSecond'))

            self.loss_label.setText(f"Loss: {loss}")

            if epoch is not None and total_epochs is not None:
                self.epoch_label.setText(f"Epoch: {epoch}/{total_epochs}")
            else:
                self.epoch_label.setText("Epoch: —")

            self.step_label.setText(f"Step: {step}")
            self.speed_label.setText(f"Speed: {speed} samples/sec" if speed != "—" else "Speed: —")

        except BackendError as e:
            pass  # Ignore polling errors

    def update_logs(self):
        """Update training logs from backend."""
        try:
            logs_data = self.main_window.backend_client.get_job_logs(self.main_window.job_id, lines=100)
            logs = logs_data.get('logs', [])

            # Update log viewer
            self.log_viewer.setPlainText('\n'.join(logs))

            # Auto-scroll to bottom
            scrollbar = self.log_viewer.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        except BackendError as e:
            pass  # Ignore polling errors

    def update_button_states(self):
        """Update button enabled states based on status."""
        if self.current_status == "QUEUED":
            self.start_button.setVisible(True)
            self.start_button.setEnabled(True)
            self.start_button.setText("Start Training")
            self.pause_button.setEnabled(False)
            self.resume_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
        elif self.current_status == "RUNNING":
            self.start_button.setVisible(False)
            self.pause_button.setEnabled(True)
            self.resume_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
        elif self.current_status == "PAUSED":
            self.start_button.setVisible(False)
            self.pause_button.setEnabled(False)
            self.resume_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
        elif self.current_status in ["COMPLETED", "FAILED", "CANCELLED"]:
            self.start_button.setVisible(False)
            self.pause_button.setEnabled(False)
            self.resume_button.setEnabled(False)
            self.cancel_button.setEnabled(False)

    def validate(self):
        """Validate that training is completed."""
        if self.current_status != "COMPLETED":
            return False, "Training must be completed before proceeding"
        return True, ""

    def save_data(self):
        """No data to save."""
        pass
