"""
Training utilities for LLM fine-tuning.
"""
import time
from datetime import datetime
from typing import List


def format_log_line(message: str) -> str:
    """
    Format log line with timestamp prefix.

    Returns:
        String like "2025-11-01 12:06:00 - {message}"
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"{timestamp} - {message}"


def calculate_eta(current_step: int, total_steps: int, elapsed_time: float) -> str:
    """
    Calculate estimated time remaining.

    Args:
        current_step: Current training step
        total_steps: Total number of steps
        elapsed_time: Time elapsed so far (in seconds)

    Returns:
        Formatted string like "01:25:30"
    """
    if current_step == 0:
        return "N/A"

    avg_time_per_step = elapsed_time / current_step
    remaining_steps = total_steps - current_step
    remaining_seconds = int(avg_time_per_step * remaining_steps)

    hours = remaining_seconds // 3600
    minutes = (remaining_seconds % 3600) // 60
    seconds = remaining_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def get_model_size(model) -> int:
    """
    Calculate total parameters in model.

    Returns:
        Parameter count
    """
    return sum(p.numel() for p in model.parameters())


def print_trainable_parameters(model):
    """
    Print count and percentage of trainable parameters.
    Useful for LoRA to show efficiency.
    """
    trainable_params = 0
    all_param = 0

    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()

    percentage = 100 * trainable_params / all_param if all_param > 0 else 0

    print(format_log_line(
        f"Trainable params: {trainable_params:,} || "
        f"All params: {all_param:,} || "
        f"Trainable%: {percentage:.2f}%"
    ))


def suggest_lora_target_modules(model) -> List[str]:
    """Heuristically pick LoRA target modules based on model architecture.

    Returns a list of module name substrings that PEFT will match.
    The detection is conservative and aims to work for common families:
    - LLaMA/Mistral: q_proj,k_proj,v_proj,o_proj
    - GPT-2/DistilGPT2: c_attn
    - Falcon: query_key_value
    Fallback to ["q_proj","v_proj"] if nothing matches.
    """
    names = [n for n, _ in model.named_modules()]
    joined = "\n".join(names)

    if "q_proj" in joined and "v_proj" in joined:
        targets = ["q_proj", "k_proj", "v_proj", "o_proj"]
    elif "c_attn" in joined:
        targets = ["c_attn"]
    elif "query_key_value" in joined:
        targets = ["query_key_value"]
    else:
        targets = ["q_proj", "v_proj"]

    return targets
