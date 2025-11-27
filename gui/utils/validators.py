"""
Input validation utilities for the GUI.
"""
import re


def validate_project_name(name: str) -> tuple[bool, str]:
    """
    Validate project name.

    Returns:
        (is_valid, error_message)
    """
    if not name or len(name.strip()) == 0:
        return False, "Project name cannot be empty"

    if len(name) > 100:
        return False, "Project name must be 100 characters or less"

    # Allow alphanumeric, space, dash, underscore
    if not re.match(r'^[a-zA-Z0-9 _-]+$', name):
        return False, "Project name can only contain letters, numbers, spaces, dashes, and underscores"

    return True, ""


def validate_learning_rate(value: str) -> tuple[bool, str]:
    """
    Validate learning rate input.

    Returns:
        (is_valid, error_message)
    """
    try:
        lr = float(value)
        if lr < 0.00001 or lr > 0.01:
            return False, "Learning rate must be between 0.00001 and 0.01"
        return True, ""
    except ValueError:
        return False, "Learning rate must be a valid number"


def validate_epochs(value: str) -> tuple[bool, str]:
    """
    Validate epochs input.

    Returns:
        (is_valid, error_message)
    """
    try:
        epochs = int(value)
        if epochs < 1 or epochs > 100:
            return False, "Epochs must be between 1 and 100"
        return True, ""
    except ValueError:
        return False, "Epochs must be a valid integer"


def validate_batch_size(value: str) -> tuple[bool, str]:
    """
    Validate batch size input.

    Returns:
        (is_valid, error_message)
    """
    try:
        batch_size = int(value)
        if batch_size < 1 or batch_size > 128:
            return False, "Batch size must be between 1 and 128"
        return True, ""
    except ValueError:
        return False, "Batch size must be a valid integer"


def validate_lora_alpha(value: str) -> tuple[bool, str]:
    """
    Validate LoRA alpha input.

    Returns:
        (is_valid, error_message)
    """
    try:
        alpha = int(value)
        if alpha < 1 or alpha > 256:
            return False, "LoRA alpha must be between 1 and 256"
        return True, ""
    except ValueError:
        return False, "LoRA alpha must be a valid integer"
