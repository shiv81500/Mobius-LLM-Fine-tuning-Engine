"""
Main training script for LoRA fine-tuning.
Launched by Java backend via ProcessBuilder.
(CPU-MODIFIED VERSION)
"""
import argparse
import sys
import os
import time
from pathlib import Path

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    TrainerCallback,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model

from data_loader import (
    load_jsonl,
    load_csv,
    load_txt,
    load_jsonl_streaming,
    load_csv_streaming,
    load_txt_streaming,
    format_for_training,
)
from training_utils import (
    format_log_line,
    calculate_eta,
    print_trainable_parameters,
    suggest_lora_target_modules,
)


class LoggingCallback(TrainerCallback):
    """Custom callback for logging training progress."""

    def __init__(self):
        self.start_time = time.time()

    def on_log(self, args, state, control, logs=None, **kwargs):
        """Log training metrics in parseable format."""
        if logs:
            epoch = state.epoch if hasattr(state, 'epoch') else 0
            total_epochs = args.num_train_epochs

            loss = logs.get('loss', 0)
            step = state.global_step
            total_steps = state.max_steps

            # Calculate speed
            elapsed = time.time() - self.start_time
            speed = step / elapsed if elapsed > 0 else 0

            # Calculate ETA
            eta = calculate_eta(step, total_steps, elapsed)

            # Print in parseable format
            print(format_log_line(
                f"Epoch {int(epoch)}/{int(total_epochs)}, "
                f"Step {step}/{total_steps}, "
                f"Loss: {loss:.4f}, "
                f"Speed: {speed:.2f} samples/sec, "
                f"ETA: {eta}"
            ))
            sys.stdout.flush()


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Train LLM with LoRA fine-tuning")

    parser.add_argument("--job-id", type=str, required=True, help="Job ID")
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset file")
    parser.add_argument("--base-model", type=str, required=True, help="HuggingFace model ID")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory")
    parser.add_argument("--learning-rate", type=float, default=0.0001, help="Learning rate")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size (kept tiny for <4GB RAM)")
    parser.add_argument("--grad-accum", type=int, default=8, help="Gradient accumulation steps")
    parser.add_argument("--max-length", type=int, default=128, help="Sequence length for tokenization")
    parser.add_argument("--stream", action="store_true", help="Stream dataset to reduce RAM usage")
    parser.add_argument("--lora-rank", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora-alpha", type=int, default=32, help="LoRA alpha")

    return parser.parse_args()


def main():
    """Main training function."""
    args = parse_args()

    print(format_log_line(f"Starting training job {args.job_id}"))
    print(format_log_line(f"Base model: {args.base_model}"))
    print(format_log_line(f"Dataset: {args.dataset}"))
    print(format_log_line(f"Output directory: {args.output_dir}"))

    # Threading hints for low-core CPUs (Ryzen 5 2500U)
    try:
        num_threads = int(os.environ.get("OMP_NUM_THREADS", "4"))
        torch.set_num_threads(num_threads)
        # Keep interop threads small on CPU
        torch.set_num_interop_threads(1)
        print(format_log_line(f"Torch threads set: num_threads={num_threads}, interop=1"))
    except Exception as _e:
        print(format_log_line("Warning: could not set Torch thread config"))

    # Detect dataset format
    dataset_ext = Path(args.dataset).suffix.lower()
    print(format_log_line(f"Detected dataset format: {dataset_ext}"))

    # Load dataset
    print(format_log_line("Loading dataset..."))
    try:
        if args.stream:
            if dataset_ext == '.jsonl':
                dataset = load_jsonl_streaming(args.dataset)
            elif dataset_ext == '.csv':
                dataset = load_csv_streaming(args.dataset)
            elif dataset_ext == '.txt':
                dataset = load_txt_streaming(args.dataset)
            else:
                raise ValueError(f"Unsupported file format: {dataset_ext}")

            # For streaming datasets, count quickly without holding in RAM
            try:
                # Fast count for jsonl/txt without loading
                if dataset_ext in {'.jsonl', '.txt'}:
                    with open(args.dataset, 'r', encoding='utf-8') as f:
                        approx = sum(1 for _ in f)
                        # for txt streaming we read by char chunks; approx lines is a proxy for chunks
                        if dataset_ext == '.txt':
                            # estimate chunks by average 128 chars per line if needed
                            pass
                elif dataset_ext == '.csv':
                    # subtract header row if present
                    with open(args.dataset, 'r', encoding='utf-8') as f:
                        approx = sum(1 for _ in f) - 1
                else:
                    approx = 0
                if approx > 0:
                    print(format_log_line(f"Streaming dataset (~{approx} lines)"))
                else:
                    print(format_log_line("Streaming dataset (unknown length)"))
            except Exception:
                print(format_log_line("Streaming dataset (unknown length)"))
        else:
            if dataset_ext == '.jsonl':
                dataset = load_jsonl(args.dataset)
            elif dataset_ext == '.csv':
                dataset = load_csv(args.dataset)
            elif dataset_ext == '.txt':
                dataset = load_txt(args.dataset)
            else:
                raise ValueError(f"Unsupported file format: {dataset_ext}")

            print(format_log_line(f"Loaded {len(dataset)} training examples"))
    except Exception as e:
        print(format_log_line(f"Error loading dataset: {str(e)}"), file=sys.stderr)
        sys.exit(1)

    # Load tokenizer
    print(format_log_line("Loading tokenizer..."))
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        print(format_log_line("Tokenizer loaded"))
    except Exception as e:
        print(format_log_line(f"Error loading tokenizer: {str(e)}"), file=sys.stderr)
        sys.exit(1)

    # Tokenize dataset
    print(format_log_line("Tokenizing dataset..."))
    try:
        tokenized_dataset = format_for_training(dataset, tokenizer, max_length=args.max_length)
        # Ensure tokenized streaming dataset yields dicts with uniform tensor-like lists
        # For IterableDataset, wrap items to enforce list[int] for input_ids/attention_mask
        try:
            from datasets import IterableDataset
            if isinstance(tokenized_dataset, IterableDataset):
                def normalize(example):
                    # Some tokenizers may return lists already; ensure list of ints
                    example["input_ids"] = list(example["input_ids"])
                    example["attention_mask"] = list(example["attention_mask"])
                    return example
                tokenized_dataset = tokenized_dataset.map(normalize)
        except Exception:
            pass
        print(format_log_line("Dataset tokenized"))
    except Exception as e:
        print(format_log_line(f"Error tokenizing dataset: {str(e)}"), file=sys.stderr)
        sys.exit(1)

    # Load base model
    print(format_log_line(f"Loading model {args.base_model}..."))
    # ================== CPU MODIFICATION 1 ==================
    print(format_log_line("WARNING: Forcing model to load on CPU. This will be very slow."))
    try:
        model = AutoModelForCausalLM.from_pretrained(
            args.base_model,
            trust_remote_code=True
            # Keeping defaults to CPU + fp32; users should pick a small base (e.g., distilgpt2)
        )
        # Ensure pad token id is set for GPT2-like models
        try:
            if getattr(model.config, "pad_token_id", None) is None:
                model.config.pad_token_id = tokenizer.pad_token_id
        except Exception:
            pass
        print(format_log_line("Model loaded on CPU"))
    # ========================================================
    except Exception as e:
        print(format_log_line(f"Error loading model: {str(e)}"), file=sys.stderr)
        print(format_log_line("This might be a CUDA out of memory error. Try reducing batch size."), file=sys.stderr)
        sys.exit(1)

    # Apply LoRA configuration
    print(format_log_line(f"Applying LoRA config: rank={args.lora_rank}, alpha={args.lora_alpha}"))
    try:
        target_modules = suggest_lora_target_modules(model)
        print(format_log_line(f"Auto-selected LoRA target modules: {target_modules}"))
        lora_config = LoraConfig(
            r=args.lora_rank,
            lora_alpha=args.lora_alpha,
            target_modules=target_modules,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )

        model = get_peft_model(model, lora_config)
        # Reduce activation memory on supported models
        try:
            # disable cache when using gradient checkpointing for HF models
            try:
                model.config.use_cache = False
            except Exception:
                pass
            # Prefer non-reentrant checkpointing to avoid PT warnings on int inputs
            try:
                model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
            except TypeError:
                model.gradient_checkpointing_enable()
            # Ensure at least one input requires grad for checkpointing backward
            if hasattr(model, "enable_input_require_grads"):
                model.enable_input_require_grads()
        except Exception:
            pass
        print_trainable_parameters(model)
    except Exception as e:
        print(format_log_line(f"Error applying LoRA: {str(e)}"), file=sys.stderr)
        sys.exit(1)

    # Prepare training arguments
    print(format_log_line("Preparing training arguments..."))
    # Compute max_steps if using streaming dataset (IterableDataset lacks __len__)
    calc_max_steps = None
    if args.stream:
        try:
            # approx variables defined earlier as 'approx' if we were able to count
            num_examples = locals().get('approx', 0)
            if num_examples <= 0:
                # Fall back to a small fixed-step smoke run
                num_examples = 512
            import math
            num_batches_per_epoch = math.ceil(max(1, num_examples) / max(1, args.batch_size))
            num_update_steps_per_epoch = math.ceil(num_batches_per_epoch / max(1, args.grad_accum))
            calc_max_steps = max(1, num_update_steps_per_epoch * max(1, args.epochs))
            print(format_log_line(f"Max steps (streaming): {calc_max_steps} (updates per epoch {num_update_steps_per_epoch})"))
        except Exception as e:
            print(format_log_line(f"Could not estimate steps ({e}), defaulting to 200"))
            calc_max_steps = 200

    # ================== CPU MODIFICATION 2 ==================
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        logging_steps=10,
        save_strategy="epoch",
        fp16=False,  # <-- This is the critical change (was True)
        bf16=False,
        optim="adafactor",  # memory efficient optimizer
        report_to="none",
        remove_unused_columns=False,
        dataloader_num_workers=0,
        dataloader_pin_memory=False,
        group_by_length=False,
        max_steps=calc_max_steps if calc_max_steps is not None else -1,
    )
    # ========================================================

    # Initialize trainer
    print(format_log_line("Initializing trainer..."))
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
        callbacks=[LoggingCallback()]
    )

    # Start training
    print(format_log_line("=== Starting training ==="))
    sys.stdout.flush()

    try:
        trainer.train()
    except Exception as e:
        print(format_log_line(f"Training error: {str(e)}"), file=sys.stderr)
        sys.exit(1)

    # Save model
    print(format_log_line("Training completed, saving model..."))
    try:
        trainer.save_model(args.output_dir)
        print(format_log_line(f"Model saved to {args.output_dir}"))
    except Exception as e:
        print(format_log_line(f"Error saving model: {str(e)}"), file=sys.stderr)
        sys.exit(1)

    # Merge LoRA weights
    print(format_log_line("Merging LoRA weights with base model..."))
    try:
        merged_dir = os.path.join(args.output_dir, "merged")
        os.makedirs(merged_dir, exist_ok=True)

        # Merge and unload
        merged_model = model.merge_and_unload()
        merged_model.save_pretrained(merged_dir)
        tokenizer.save_pretrained(merged_dir)

        print(format_log_line(f"Merged model saved to {merged_dir}"))
    except Exception as e:
        print(format_log_line(f"Error merging model: {str(e)}"), file=sys.stderr)
        print(format_log_line("Continuing without merge - GGUF conversion may fail"), file=sys.stderr)

    print(format_log_line("=== Training job complete ==="))


if __name__ == "__main__":
    main()