# LLM Fine-Tuning Desktop Application

A complete desktop application for fine-tuning Large Language Models with local GGUF model export. Built with a three-component architecture:

1. **Python PyQt6 GUI** - User-facing desktop interface
2. **Java Backend** - Orchestration engine with custom DSA implementations
3. **Python ML Core** - Training and GGUF conversion scripts

## Low-RAM (<4GB) Usage

For machines with ~8GB system RAM and <4GB available for Python, use the new low-memory pipeline:

1. Choose a very small base model (examples):
   - `distilgpt2`
   - `tiiuae/falcon-rw-1b` (may be borderline) or a 0.5–1B class model
2. Use streaming dataset mode to avoid loading entire files:

```powershell
python ml_core/training_script.py `
  --job-id test1 `
  --dataset data/datasets/demo.jsonl `
  --base-model distilgpt2 `
  --output-dir models/test1 `
  --batch-size 1 `
  --grad-accum 16 `
  --max-length 128 `
  --epochs 1 `
  --learning-rate 5e-5 `
  --stream
```

Key memory-saving features:
- Batch size 1 + gradient accumulation simulates larger effective batch.
- `--max-length 128` trims sequences (reduce to 64 if still high memory).
- Streaming loaders (`--stream`) prevent full dataset materialization.
- Adafactor optimizer cuts optimizer state memory vs AdamW.
- Gradient checkpointing reduces activation memory.

Further tips:
- Close other applications to free RAM.
- Prefer plain JSONL over large CSV with many columns.
- If tokenization is slow streamed, you can pre-tokenize a small subset offline.

If you still exceed memory:
- Lower `--max-length` to 64.
- Increase `--grad-accum` (e.g. 32) and keep `--batch-size 1`.
- Reduce LoRA rank: `--lora-rank 4 --lora-alpha 8`.
- Train only for 1 epoch as a functional smoke test before longer runs.


## Features

- Upload training data (JSONL, CSV, or TXT formats)
- Select from popular base models (Llama, Mistral, Phi-3)
- Configure LoRA hyperparameters
- Real-time training monitoring with live logs and metrics
- Pause/resume/cancel training controls
- Export quantized GGUF models for local inference

## Prerequisites

### For GPU Training (Recommended)
- **Java 21+** (for backend) - LTS version required
- **Python 3.10 or 3.11** (for GUI and ML Core)
- **Maven** (for building Java backend)
- **CUDA-capable GPU** with 8GB+ VRAM (NVIDIA)
- **Git** (for cloning llama.cpp)
- **16GB+ System RAM**
- **50GB+ free disk space** (for models and data)

### For CPU Training (Your Ryzen 5 2500U System)
- **Java 21+** (for backend) - LTS version required
- **Python 3.13+** (for GUI and ML Core)
- **Maven** (for building Java backend)
- **Git** (for cloning llama.cpp)
- **7-8GB+ System RAM** (minimum)
- **20GB+ free disk space** (for small models)
- ⚠️ **Use TinyLlama (1.1B) or smaller models only**
- ⚠️ **Training will be 10-50x slower than GPU**
- ⚠️ **Use small datasets (100-500 examples max)**

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd JavaDSAProject
```

### 2. Build Java Backend

```bash
mvn clean package
```

This creates `target/llm-trainer-backend-1.0.0.jar`

### 3. Setup Python GUI

```bash
cd gui
pip install -r requirements.txt
cd ..
```

### 4. Setup Python ML Core

```bash
cd ml_core

# Install Python dependencies
pip install -r requirements.txt

# Clone and build llama.cpp
chmod +x setup.sh
./setup.sh

cd ..
```

The setup script will clone llama.cpp and build the quantization tools.

## Running the Application

### Step 1: Start Java Backend

In the project root directory:

```bash
java -jar target/llm-trainer-backend-1.0.0.jar
```

**Expected output:**
```
===================================
LLM Training Backend
===================================
Creating data directories...
Initializing components...
Data Manager initialized
Job Queue Manager initialized
Log Store initialized
Process Orchestrator initialized
Starting HTTP server on port 8080...
LLM Training Backend running on http://localhost:8080
===================================
Backend ready. Press Ctrl+C to stop.
===================================
```

Leave this terminal running.

### Step 2: Start Python GUI

In a **new terminal**, from the project root:

```bash
cd gui
python main.py
```

The GUI will check backend connectivity and open the main window.

## User Workflow

### Step 1: Project Setup

- Enter a project name
- Select a base model to fine-tune:
  
  **✅ CPU-Compatible Models (for Ryzen 5 2500U with 7.8GB RAM):**
  - **TinyLlama-1.1B** (Recommended - 1.1B params, trains in hours)
  - **Phi-2** (2.7B params, may be slow but works)
  - **Qwen-0.5B** (500M params, very fast)
  - **DistilGPT-2** (82M params, for testing)
  - **GPT-2** (124M params, classic model)
  
  **❌ GPU-Only Models (Require 8GB+ VRAM):**
  - Llama-3-8B / Llama-3.1-8B / Llama-3.2-3B
  - Mistral-7B-v0.2
  - Phi-3-mini / Phi-3-medium

**Tip for CPU:** Use TinyLlama with batch_size=1 and small datasets (100-500 examples). Training will be slow (10-50x slower than GPU) but will work on your system.

### Step 2: Upload Training Data

- Click "Choose File" and select your dataset
- Supported formats:
  - **JSONL**: One JSON object per line with `instruction` and `response` keys
  - **CSV**: Tabular data with text columns
  - **TXT**: Plain text for completion-style training
- Click "Upload to Backend"

**Example JSONL format:**
```jsonl
{"instruction": "What is AI?", "response": "AI stands for Artificial Intelligence..."}
{"instruction": "Explain machine learning", "response": "Machine learning is..."}
```

### Step 3: Configure Hyperparameters

**For GPU Training (8GB+ VRAM):**
- **Learning Rate**: 0.0001 - 0.0003 (recommended for LoRA)
- **Epochs**: Number of training passes over the dataset
- **Batch Size**: Lower values use less VRAM (try 2-4 for 8GB GPU)
- **LoRA Rank**: 8, 16, 32, or 64 (higher = more trainable parameters)

**For CPU Training (Ryzen 5 2500U with 7.8GB RAM):**
- **Learning Rate**: 0.0002 (default is fine)
- **Epochs**: 1 (start with just 1 epoch - training is very slow)
- **Batch Size**: 1 (MUST use 1 for low memory)
- **LoRA Rank**: 8 (lower rank uses less memory)
- **LoRA Alpha**: Usually 2x the rank
- **Quantization**: Q4_K_M (smaller), Q5_K_M, or Q8_0 (highest quality)

Click "Next" to create the training job.

### Step 4: Training

- Click "Start Training" to begin
- Monitor real-time:
  - **Loss**: Training loss value
  - **Epoch**: Current epoch progress
  - **Step**: Current training step
  - **Speed**: Samples per second
  - **Logs**: Live training output

**Controls:**
- **Pause**: Temporarily stop training
- **Resume**: Continue paused training
- **Cancel**: Stop and abandon training

Wait for "Training completed successfully!" message.

### Step 5: Export Model

- Click "Convert to GGUF" to start conversion
- Wait for conversion to complete
- Click "Download GGUF Model" to save the model locally
- Choose a location and filename

The downloaded `.gguf` file can be used with llama.cpp, Ollama, LM Studio, or other local inference tools.

## Project Structure

```
JavaDSAProject/
├── src/main/java/com/llmtrainer/     # Java backend source
│   ├── Main.java                     # Entry point
│   ├── api/                          # REST API handlers
│   ├── model/                        # Data models
│   ├── queue/                        # Job queue (LinkedList FIFO)
│   ├── storage/                      # Dataset storage (HashMap)
│   ├── logging/                      # Log store (Circular buffer)
│   ├── orchestrator/                 # Process management
│   └── util/                         # Utilities (JSON, UUID)
├── gui/                              # Python PyQt6 GUI
│   ├── main.py                       # GUI entry point
│   ├── main_window.py                # Wizard controller
│   ├── api/backend_client.py         # REST API client
│   ├── steps/                        # Wizard step widgets
│   └── utils/                        # Validators, formatters
├── ml_core/                          # Python ML scripts
│   ├── training_script.py            # LoRA fine-tuning
│   ├── convert_to_gguf.py            # GGUF conversion
│   ├── data_loader.py                # Dataset loading
│   ├── training_utils.py             # Helper functions
│   └── llama.cpp/                    # (created by setup.sh)
├── data/                             # Runtime data (created automatically)
│   ├── datasets/                     # Uploaded training data
│   ├── models/                       # Trained model weights
│   ├── gguf/                         # Final GGUF files
│   └── logs/                         # Training logs
├── pom.xml                           # Maven build configuration
└── README.md                         # This file
```

## Architecture

```
[Python PyQt6 GUI] <--REST API--> [Java Backend] <--ProcessBuilder--> [Python ML Scripts]
                                         |
                                   [File Storage]
```

### Communication Flow

1. **GUI → Backend**: REST API calls (HTTP/JSON)
2. **Backend → ML Scripts**: ProcessBuilder (command-line)
3. **ML Scripts → Backend**: stdout/stderr streams (logs and metrics)
4. **Backend → GUI**: Polling (status, logs, metrics)

### Data Structures

The Java backend implements custom data structures:

- **Job Queue**: LinkedList-based FIFO queue (O(1) enqueue/dequeue)
- **Dataset Storage**: HashMap (O(1) lookup)
- **Log Store**: Circular buffer (O(1) append, efficient streaming)

## API Endpoints

The Java backend exposes a REST API on `http://localhost:8080/api`:

### Datasets
- `POST /api/datasets/upload` - Upload training data
- `GET /api/datasets/{datasetId}` - Get dataset metadata
- `DELETE /api/datasets/{datasetId}` - Delete dataset

### Jobs
- `POST /api/jobs/create` - Create training job
- `POST /api/jobs/{jobId}/start` - Start training
- `POST /api/jobs/{jobId}/pause` - Pause training
- `POST /api/jobs/{jobId}/resume` - Resume training
- `POST /api/jobs/{jobId}/cancel` - Cancel training
- `GET /api/jobs/{jobId}/status` - Get job status
- `GET /api/jobs/{jobId}/logs` - Get training logs
- `GET /api/jobs/{jobId}/metrics` - Get training metrics
- `GET /api/jobs/queue` - Get all jobs
- `POST /api/jobs/{jobId}/convert-gguf` - Start GGUF conversion
- `GET /api/jobs/{jobId}/download-gguf` - Download GGUF file

## Troubleshooting

### Backend won't start

**Error:** `Port 8080 already in use`

**Solution:** Another process is using port 8080. Kill it or change the port in `ApiServer.java`.

### GUI can't connect to backend

**Error:** "Backend not running"

**Solution:**
1. Make sure Java backend is running first
2. Check that backend shows "running on http://localhost:8080"
3. Try restarting the backend

### Training fails with CUDA error

**Error:** "CUDA out of memory"

**Solution:**
- Reduce batch size (try 2 or even 1)
- Use a smaller base model (Llama-3.2-3B instead of Llama-3-8B)
- Close other applications using GPU memory

### GGUF conversion fails

**Error:** "llama.cpp not built"

**Solution:**
```bash
cd ml_core
chmod +x setup.sh
./setup.sh
```

### Model download is slow

This is normal. Model files are several GB in size. Progress bar shows download status.

## Configuration

### Change Backend Port

Edit `src/main/java/com/llmtrainer/api/ApiServer.java`:

```java
this.server = HttpServer.create(new InetSocketAddress("localhost", 9000), 0);
```

Also update `gui/api/backend_client.py`:

```python
def __init__(self, base_url: str = "http://localhost:9000/api"):
```

### Use Specific GPU

```bash
CUDA_VISIBLE_DEVICES=0 java -jar target/llm-trainer-backend-1.0.0.jar
```

## Development

### Build Backend

```bash
mvn clean package
```

### Run Backend in Development

```bash
mvn exec:java -Dexec.mainClass="com.llmtrainer.Main"
```

### GUI Development

```bash
cd gui
python main.py
```

## System Requirements

### For GPU Training (Recommended)

**Minimum:**
- 8GB GPU VRAM (NVIDIA with CUDA)
- 16GB System RAM
- 50GB free disk space
- 4-core CPU

**Recommended:**
- 16GB+ GPU VRAM (for larger models)
- 32GB System RAM
- 100GB+ free disk space (for multiple projects)
- 8-core CPU

### For CPU Training (Your Ryzen 5 2500U System)

**Your Hardware:**
- ✅ AMD Ryzen 5 2500U (4 cores, 8 threads)
- ✅ Vega 8 integrated graphics (2GB shared VRAM)
- ✅ 7.8GB System RAM
- ✅ Works with TinyLlama (1.1B) and smaller models

**Limitations:**
- ⚠️ Training is 10-50x slower than GPU
- ⚠️ Must use small models (< 2B parameters)
- ⚠️ Batch size must be 1
- ⚠️ Limit dataset to 100-500 examples
- ⚠️ Single epoch recommended to start

**Alternative:** Consider using Google Colab (free T4 GPU) or Kaggle Notebooks for larger models.

## Credits

- Built with HuggingFace Transformers and PEFT
- GGUF conversion powered by llama.cpp
- GUI built with PyQt6
- Backend uses Java's built-in HttpServer
