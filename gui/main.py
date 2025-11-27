"""
Main entry point for LLM Training GUI.
"""
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox

from api.backend_client import BackendClient
from main_window import MainWindow


def check_backend_connection(client: BackendClient) -> bool:
    """Check if backend is reachable."""
    return client.check_connection()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Mobius LLM Fine-Tuning Engine")

    # Create backend client
    backend_client = BackendClient()

    # Check backend connectivity
    if not check_backend_connection(backend_client):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Backend Not Running")
        msg.setText("Cannot connect to the backend server.")
        msg.setInformativeText(
            "Please make sure the Java backend is running:\n\n"
            "java -jar target/llm-trainer-backend-1.0.0.jar\n\n"
            "The backend should be running on http://localhost:8080"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Close)

        result = msg.exec()

        if result == QMessageBox.StandardButton.Retry:
            # Try again
            if not check_backend_connection(backend_client):
                sys.exit(1)
        else:
            sys.exit(1)

    # Create and show main window
    window = MainWindow(backend_client)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
