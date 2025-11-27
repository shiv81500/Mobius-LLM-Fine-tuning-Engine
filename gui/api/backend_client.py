"""
Backend API client for communicating with Java backend REST API.
"""
import requests
from typing import Dict, Optional, List


class BackendError(Exception):
    """Exception raised for backend API errors."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Backend error ({status_code}): {message}")


class BackendClient:
    """Client for Java backend REST API."""

    def __init__(self, base_url: str = "http://localhost:8080/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _handle_response(self, response: requests.Response) -> Dict:
        """Handle API response and extract data or raise error."""
        try:
            json_response = response.json()
        except Exception:
            raise BackendError(response.status_code, "Invalid JSON response")

        if response.status_code >= 400:
            error_message = json_response.get("error", "Unknown error")
            raise BackendError(response.status_code, error_message)

        if json_response.get("status") == "error":
            error_message = json_response.get("error", "Unknown error")
            raise BackendError(response.status_code, error_message)

        return json_response.get("data", {})

    # Dataset operations

    def upload_dataset(self, file_path: str, format: str) -> Dict:
        """
        Upload a training dataset file.

        Args:
            file_path: Path to the dataset file
            format: File format ('jsonl', 'csv', or 'txt')

        Returns:
            Dict with datasetId, filename, fileSize, rowCount
        """
        url = f"{self.base_url}/datasets/upload"

        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'format': format}
            # Don't use session for multipart upload
            response = requests.post(url, files=files, data=data)

        return self._handle_response(response)

    def get_dataset(self, dataset_id: str) -> Dict:
        """Get dataset metadata by ID."""
        url = f"{self.base_url}/datasets/{dataset_id}"
        response = self.session.get(url)
        return self._handle_response(response)

    def delete_dataset(self, dataset_id: str) -> Dict:
        """Delete a dataset by ID."""
        url = f"{self.base_url}/datasets/{dataset_id}"
        response = self.session.delete(url)
        return self._handle_response(response)

    # Job operations

    def create_job(self, project_name: str, dataset_id: str,
                   base_model: str, hyperparameters: Dict) -> Dict:
        """
        Create a new training job.

        Returns:
            Dict with jobId, status, createdAt
        """
        url = f"{self.base_url}/jobs/create"
        payload = {
            "projectName": project_name,
            "datasetId": dataset_id,
            "baseModel": base_model,
            "hyperparameters": hyperparameters
        }
        response = self.session.post(url, json=payload)
        return self._handle_response(response)

    def start_job(self, job_id: str) -> Dict:
        """Start a queued training job."""
        url = f"{self.base_url}/jobs/{job_id}/start"
        response = self.session.post(url)
        return self._handle_response(response)

    def pause_job(self, job_id: str) -> Dict:
        """Pause a running training job."""
        url = f"{self.base_url}/jobs/{job_id}/pause"
        response = self.session.post(url)
        return self._handle_response(response)

    def resume_job(self, job_id: str) -> Dict:
        """Resume a paused training job."""
        url = f"{self.base_url}/jobs/{job_id}/resume"
        response = self.session.post(url)
        return self._handle_response(response)

    def cancel_job(self, job_id: str) -> Dict:
        """Cancel a training job."""
        url = f"{self.base_url}/jobs/{job_id}/cancel"
        response = self.session.post(url)
        return self._handle_response(response)

    def get_job_status(self, job_id: str) -> Dict:
        """Get current status and details of a training job."""
        url = f"{self.base_url}/jobs/{job_id}/status"
        response = self.session.get(url)
        return self._handle_response(response)

    def get_job_logs(self, job_id: str, lines: int = 100) -> Dict:
        """
        Get training logs for a job.

        Returns:
            Dict with jobId and logs (list of strings)
        """
        url = f"{self.base_url}/jobs/{job_id}/logs?lines={lines}"
        response = self.session.get(url)
        return self._handle_response(response)

    def get_job_metrics(self, job_id: str) -> Dict:
        """
        Get current training metrics for a job.

        Returns:
            Dict with loss, epoch, step, samplesPerSecond, estimatedTimeRemaining
        """
        url = f"{self.base_url}/jobs/{job_id}/metrics"
        response = self.session.get(url)
        return self._handle_response(response)

    def get_queue(self) -> Dict:
        """
        Get all jobs in the queue.

        Returns:
            Dict with 'jobs' list
        """
        url = f"{self.base_url}/jobs/queue"
        response = self.session.get(url)
        return self._handle_response(response)

    def convert_to_gguf(self, job_id: str) -> Dict:
        """Start GGUF conversion for a completed job."""
        url = f"{self.base_url}/jobs/{job_id}/convert-gguf"
        response = self.session.post(url)
        return self._handle_response(response)

    def get_conversion_status(self, job_id: str) -> Dict:
        """Get GGUF conversion status and recent logs for a job."""
        url = f"{self.base_url}/jobs/{job_id}/conversion-status"
        response = self.session.get(url)
        return self._handle_response(response)

    def download_gguf(self, job_id: str, save_path: str,
                     progress_callback=None) -> None:
        """
        Download GGUF model file.

        Args:
            job_id: Job ID
            save_path: Local path to save the file
            progress_callback: Optional callback(bytes_downloaded, total_bytes)
        """
        url = f"{self.base_url}/jobs/{job_id}/download-gguf"
        response = self.session.get(url, stream=True)

        if response.status_code != 200:
            raise BackendError(response.status_code, "Failed to download GGUF file")

        total_size = int(response.headers.get('content-length', 0))

        with open(save_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total_size)

    def check_connection(self) -> bool:
        """Check if backend is reachable."""
        try:
            self.get_queue()
            return True
        except Exception:
            return False
