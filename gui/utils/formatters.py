"""
Data formatting utilities for the GUI.
"""


def format_file_size(bytes_size: int) -> str:
    """Format file size in bytes to human-readable string."""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"


def format_duration(start_time: str, end_time: str) -> str:
    """
    Format duration between two ISO datetime strings.

    Returns:
        String like "1h 25m 30s"
    """
    from datetime import datetime

    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        duration = end - start

        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except Exception:
        return "N/A"


def format_metric_value(value) -> str:
    """Format a metric value for display."""
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
