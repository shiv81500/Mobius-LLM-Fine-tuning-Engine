"""
Test script to verify CPU training setup on Ryzen 5 2500U with 7.8GB RAM
This will check if PyTorch and dependencies work correctly.
"""
import sys

print("=" * 60)
print("CPU Training Setup Verification")
print("=" * 60)

# Check Python version
print(f"\n✓ Python version: {sys.version.split()[0]}")

# Check PyTorch
try:
    import torch
    print(f"✓ PyTorch version: {torch.__version__}")
    print(f"  - CUDA available: {torch.cuda.is_available()}")
    if not torch.cuda.is_available():
        print(f"  ⚠️  No CUDA GPU detected - will use CPU (expected for your system)")
    print(f"  - CPU threads: {torch.get_num_threads()}")
except ImportError as e:
    print(f"✗ PyTorch not installed: {e}")
    sys.exit(1)

# Check Transformers
try:
    import transformers
    print(f"✓ Transformers version: {transformers.__version__}")
except ImportError as e:
    print(f"✗ Transformers not installed: {e}")
    sys.exit(1)

# Check PEFT
try:
    import peft
    print(f"✓ PEFT version: {peft.__version__}")
except ImportError as e:
    print(f"✗ PEFT not installed: {e}")
    sys.exit(1)

# Check other dependencies
try:
    import datasets
    print(f"✓ Datasets version: {datasets.__version__}")
except ImportError as e:
    print(f"✗ Datasets not installed: {e}")

try:
    import accelerate
    print(f"✓ Accelerate version: {accelerate.__version__}")
except ImportError as e:
    print(f"✗ Accelerate not installed: {e}")

# Memory check
import psutil
mem = psutil.virtual_memory()
print(f"\n💾 System Memory:")
print(f"  - Total: {mem.total / (1024**3):.1f} GB")
print(f"  - Available: {mem.available / (1024**3):.1f} GB")
print(f"  - Used: {mem.percent}%")

if mem.available < 4 * (1024**3):
    print(f"  ⚠️  Low memory! Close other applications before training.")

# Recommendations
print("\n" + "=" * 60)
print("RECOMMENDATIONS FOR YOUR SYSTEM (Ryzen 5 2500U, 7.8GB RAM):")
print("=" * 60)
print("\n✅ Compatible Models:")
print("  - TinyLlama/TinyLlama-1.1B-Chat-v1.0 (BEST CHOICE)")
print("  - microsoft/phi-2 (2.7B - slower but works)")
print("  - Qwen/Qwen-0.5B (very lightweight)")
print("  - distilgpt2, gpt2 (for testing)")

print("\n⚙️  Training Settings:")
print("  - Batch Size: 1 (REQUIRED)")
print("  - Epochs: 1-2 (start with 1)")
print("  - LoRA Rank: 8")
print("  - Dataset: 100-500 examples max")

print("\n⏱️  Expected Training Time (TinyLlama, 100 examples, 1 epoch):")
print("  - Your system: ~30-60 minutes")
print("  - With GPU: ~2-5 minutes")

print("\n💡 Tips:")
print("  - Close all other applications before training")
print("  - Training will be SLOW - be patient!")
print("  - Consider using Google Colab for free GPU access")
print("  - Start with a small test dataset (10-20 examples)")

print("\n✅ Setup verification complete!")
print("=" * 60)
