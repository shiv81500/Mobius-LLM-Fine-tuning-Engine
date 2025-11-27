"""
Data loading utilities for various training data formats with low-RAM options.

Notes:
- Default loaders returned an in-memory `Dataset`, which can spike RAM usage
    when files are large. To support <4GB setups, we add generator-based streaming
    loaders that return `IterableDataset` and avoid materializing the full corpus
    in memory.
"""
import json
import csv
from typing import Iterable
from datasets import Dataset, IterableDataset
import torch, os
torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "4")))
torch.set_num_interop_threads(1)


def load_jsonl(file_path: str) -> Dataset:
    """
    Load JSONL file where each line is JSON object.
    Expected keys: "instruction", "response" OR "input", "output" OR "text"

    Returns:
        HuggingFace Dataset with "text" column formatted for training.
    """
    data = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            obj = json.loads(line)

            # Try different key combinations
            if 'instruction' in obj and 'response' in obj:
                text = f"### Instruction:\n{obj['instruction']}\n\n### Response:\n{obj['response']}"
            elif 'input' in obj and 'output' in obj:
                text = f"### Input:\n{obj['input']}\n\n### Output:\n{obj['output']}"
            elif 'text' in obj:
                text = obj['text']
            else:
                # Use all keys
                text = json.dumps(obj)

            data.append({"text": text})

    return Dataset.from_list(data)


def load_jsonl_streaming(file_path: str) -> IterableDataset:
    """Stream a JSONL file line-by-line as an IterableDataset."""
    def generator() -> Iterable[dict]:
        with open(file_path, 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if 'instruction' in obj and 'response' in obj:
                    text = f"### Instruction:\n{obj['instruction']}\n\n### Response:\n{obj['response']}"
                elif 'input' in obj and 'output' in obj:
                    text = f"### Input:\n{obj['input']}\n\n### Output:\n{obj['output']}"
                elif 'text' in obj:
                    text = obj['text']
                else:
                    text = json.dumps(obj)
                yield {"text": text}

    return IterableDataset.from_generator(generator)


def load_csv(file_path: str) -> Dataset:
    """
    Load CSV file, auto-detect text columns.
    Combines relevant text columns into training examples.

    Returns:
        HuggingFace Dataset with "text" column.
    """
    data = []

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Combine all text columns
            text_parts = []
            for key, value in row.items():
                if value and len(value.strip()) > 0:
                    text_parts.append(f"{key}: {value}")

            if text_parts:
                text = "\n".join(text_parts)
                data.append({"text": text})

    return Dataset.from_list(data)


def load_csv_streaming(file_path: str) -> IterableDataset:
    """Stream rows from a CSV as an IterableDataset."""
    def generator() -> Iterable[dict]:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                text_parts = []
                for key, value in row.items():
                    if value and len(value.strip()) > 0:
                        text_parts.append(f"{key}: {value}")
                if text_parts:
                    yield {"text": "\n".join(text_parts)}

    return IterableDataset.from_generator(generator)


def load_txt(file_path: str, chunk_size: int = 2048) -> Dataset:
    """
    Load plain text file, split into chunks for completion training.

    Args:
        file_path: Path to text file
        chunk_size: Number of characters per chunk

    Returns:
        HuggingFace Dataset with "text" column.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        full_text = f.read()

    # Split into chunks
    chunks = []
    for i in range(0, len(full_text), chunk_size):
        chunk = full_text[i:i + chunk_size]
        if chunk.strip():
            chunks.append({"text": chunk})

    return Dataset.from_list(chunks)


def load_txt_streaming(file_path: str, chunk_size: int = 2048) -> IterableDataset:
    """Stream a text file in fixed-size chunks as an IterableDataset."""
    def generator() -> Iterable[dict]:
        with open(file_path, 'r', encoding='utf-8') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                if chunk.strip():
                    yield {"text": chunk}

    return IterableDataset.from_generator(generator)


def format_for_training(dataset: Dataset, tokenizer, max_length: int = 128) -> Dataset:
    """
    Tokenizes dataset for causal language modeling.
    Adds input_ids, attention_mask columns.

    Returns:
        Tokenized Dataset ready for Trainer.
    """
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding="max_length",
            max_length=max_length
        )

    # Support both in-memory and iterable datasets without materializing data
    if isinstance(dataset, IterableDataset):
        # Important: remove original 'text' column so the data collator doesn't try
        # to batch raw strings (which would cause tensor creation errors)
        return dataset.map(
            lambda ex: tokenizer(
                ex["text"],
                truncation=True,
                padding="max_length",
                max_length=max_length
            ),
            remove_columns=["text"]
        )
    else:
        tokenized = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        return tokenized
