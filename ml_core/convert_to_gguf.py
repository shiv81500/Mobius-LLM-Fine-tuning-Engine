"""
GGUF conversion script using llama.cpp.
Launched by Java backend after training completes.
"""
import argparse
import sys
import os
import subprocess
from pathlib import Path

from training_utils import format_log_line


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Convert trained model to GGUF format")

    parser.add_argument("--model-dir", type=str, required=True, help="Directory containing trained model")
    parser.add_argument("--output-file", type=str, required=True, help="Output GGUF file path")
    parser.add_argument("--quantization", type=str, default="Q4_K_M", help="Quantization level")

    return parser.parse_args()


def check_llama_cpp():
    """Check if llama.cpp is built and available."""
    # Check for various possible binary names/locations
    possible_paths = [
        "ml_core/llama.cpp/quantize",
        "ml_core/llama.cpp/quantize.exe",
        "ml_core/llama.cpp/llama-quantize",
        "ml_core/llama.cpp/llama-quantize.exe",
        "ml_core/llama.cpp/build/bin/Release/llama-quantize.exe",
        "ml_core/llama.cpp/build/bin/Release/quantize.exe"
    ]
    
    found_path = None
    for path in possible_paths:
        if os.path.exists(path):
            found_path = path
            break

    if not found_path:
        print(format_log_line("Warning: llama.cpp not built (quantize binary not found)"), file=sys.stderr)
        print(format_log_line("Quantization will be skipped. Only F16 GGUF will be generated."), file=sys.stderr)
        return None

    return found_path


def convert_to_f16(model_dir: str, output_file: str) -> bool:
    """
    Convert PyTorch model to F16 GGUF.

    Returns:
        True if successful, False otherwise
    """
    print(format_log_line(f"Converting PyTorch model to F16 GGUF..."))

    # Updated to use convert_hf_to_gguf.py as convert.py is deprecated/renamed
    convert_script = "ml_core/llama.cpp/convert_hf_to_gguf.py"

    if not os.path.exists(convert_script):
        print(format_log_line(f"Error: {convert_script} not found"), file=sys.stderr)
        return False

    try:
        result = subprocess.run(
            [
                sys.executable,
                convert_script,
                model_dir,
                "--outtype", "f16",
                "--outfile", output_file
            ],
            capture_output=True,
            text=True,
            check=True
        )

        # Print output
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(format_log_line(line))

        print(format_log_line("F16 GGUF created"))
        return True

    except subprocess.CalledProcessError as e:
        print(format_log_line(f"Error during conversion: {e}"), file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False


def quantize_gguf(input_file: str, output_file: str, quantization: str, quantize_binary: str) -> bool:
    """
    Quantize F16 GGUF to specified quantization level.

    Returns:
        True if successful, False otherwise
    """
    print(format_log_line(f"Quantizing to {quantization}..."))

    try:
        result = subprocess.run(
            [
                quantize_binary,
                input_file,
                output_file,
                quantization
            ],
            capture_output=True,
            text=True,
            check=True
        )

        # Print output
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(format_log_line(line))

        print(format_log_line("Quantization complete"))
        return True

    except subprocess.CalledProcessError as e:
        print(format_log_line(f"Error during quantization: {e}"), file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False


def main():
    """Main conversion function."""
    args = parse_args()

    print(format_log_line("Starting GGUF conversion"))
    print(format_log_line(f"Model: {args.model_dir}"))
    print(format_log_line(f"Quantization: {args.quantization}"))

    # Check if model directory exists
    if not os.path.exists(args.model_dir):
        print(format_log_line(f"Error: Model directory not found: {args.model_dir}"), file=sys.stderr)
        sys.exit(1)

    # Check if llama.cpp is built
    quantize_binary = check_llama_cpp()
    
    # Create temporary F16 GGUF file
    # If quantization is skipped, this will be the final output file
    if not quantize_binary:
        temp_f16_file = args.output_file
    else:
        temp_f16_file = args.output_file.replace('.gguf', '_f16_temp.gguf')

    # Step 1: Convert to F16 GGUF
    if not convert_to_f16(args.model_dir, temp_f16_file):
        print(format_log_line("GGUF conversion failed"), file=sys.stderr)
        sys.exit(1)

    # Step 2: Quantize to target format (only if binary exists)
    if quantize_binary:
        if not quantize_gguf(temp_f16_file, args.output_file, args.quantization, quantize_binary):
            print(format_log_line("Quantization failed"), file=sys.stderr)
            # Clean up temp file
            if os.path.exists(temp_f16_file):
                os.remove(temp_f16_file)
            sys.exit(1)

        # Clean up temp file
        print(format_log_line("Cleaning up temporary files..."))
        if os.path.exists(temp_f16_file):
            os.remove(temp_f16_file)
            print(format_log_line("Temporary files removed"))
    else:
        print(format_log_line("Skipping quantization step."))
        print(format_log_line(f"F16 GGUF saved to: {args.output_file}"))

    # Verify output file exists and get size
    if os.path.exists(args.output_file):
        file_size = os.path.getsize(args.output_file)
        size_mb = file_size / (1024 * 1024)
        print(format_log_line(f"Final GGUF size: {size_mb:.2f} MB"))
        print(format_log_line(f"GGUF conversion complete: {args.output_file}"))
    else:
        print(format_log_line("Error: Output file was not created"), file=sys.stderr)
        sys.exit(1)

    # Verify output file exists and get size
    if os.path.exists(args.output_file):
        file_size = os.path.getsize(args.output_file)
        size_mb = file_size / (1024 * 1024)
        print(format_log_line(f"Final GGUF size: {size_mb:.2f} MB"))
        print(format_log_line(f"GGUF conversion complete: {args.output_file}"))
    else:
        print(format_log_line("Error: Output file was not created"), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
