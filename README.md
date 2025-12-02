# 🚀 Mobius LLM Fine-Tuning Engine

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
![Java](https://img.shields.io/badge/Java-21+-orange?style=for-the-badge&logo=openjdk&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red?style=for-the-badge&logo=pytorch&logoColor=white)
![License](https://img.shields.io/badge/License-Apache-green?style=for-the-badge)

**A complete desktop application for fine-tuning Large Language Models on CPU/GPU with GGUF export for LM Studio**

[Features](#-features) • [Quick Start](#-quick-start) • [Model Guide](#-model-recommendations) • [Training Tips](#-training-tips)

</div>

---

## 🎯 What is This?

Mobius is a **local LLM fine-tuning engine** that lets you:
- Fine-tune small language models on your own data
- Export to GGUF format for use in **LM Studio**, Ollama, or llama.cpp
- Train on **CPU** (no GPU required!) with optimized settings

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  PyQt6 GUI      │────▶│  Java Backend   │────▶│  Python ML Core │
│  (Desktop App)  │◀────│  (Orchestrator) │◀────│  (Training)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📁 **Multi-Format Data** | Upload JSONL, CSV, or TXT training data |
| 🤖 **Model Selection** | Choose from CPU-optimized models |
| ⚙️ **LoRA Fine-Tuning** | Memory-efficient training with LoRA |
| 📊 **Live Monitoring** | Real-time training logs and metrics |
| ⏸️ **Training Controls** | Pause, resume, or cancel training |
| 📦 **GGUF Export** | Convert to GGUF for LM Studio |
| 💻 **CPU Optimized** | Works on systems with 8GB RAM |

---

## 🔧 Model Recommendations

### For CPU Systems (8GB RAM)

| Model | Parameters | RAM Usage | Best For | Training Time |
|-------|------------|-----------|----------|---------------|
| **Qwen2-0.5B-Instruct** ⭐ | 500M | ~1GB | Q&A, Instructions | Fast |
| **SmolLM-360M-Instruct** | 360M | ~500MB | Simple Q&A | Fastest |
| **TinyLlama-1.1B-Chat** | 1.1B | ~2GB | Conversations | Medium |
| **Phi-2** | 2.7B | ~4GB | Complex Tasks | Slow |

### ⚠️ Models to AVOID on CPU

| Model | Why Avoid |
|-------|-----------|
| DistilGPT2 | Not instruction-tuned, gives gibberish for Q&A |
| GPT-2 | Completion only, doesn't follow instructions |
| Llama-3-8B | Too large, needs 16GB+ RAM |
| Mistral-7B | Too large, needs 14GB+ RAM |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Java 21+**
- **Maven**
- **8GB+ RAM**

### Installation

```powershell
# 1. Clone the repository
git clone https://github.com/Adil-Ijaz7/Mobius-LLM-Fine-tuning-Engine.git
cd Mobius-LLM-Fine-tuning-Engine

# 2. Create Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install Python dependencies
pip install -r ml_core/requirements.txt
pip install -r gui/requirements.txt

# 4. Build Java backend
mvn clean package
```

### Running

**Terminal 1 - Start Backend:**
```powershell
java -jar target/llm-trainer-backend-1.0.0.jar
```

**Terminal 2 - Start GUI:**
```powershell
cd gui
python main.py
```

---

## 📝 Training Data Format

Your data should be in **JSONL format** with `instruction` and `response` fields:

```jsonl
{"instruction": "What is machine learning?", "response": "Machine learning is a subset of AI..."}
{"instruction": "Explain neural networks", "response": "Neural networks are computing systems..."}
{"instruction": "What is Python?", "response": "Python is a programming language..."}
```

### Recommended Dataset Size

| Dataset Size | Epochs | Expected Quality |
|--------------|--------|------------------|
| 17 examples | 15-20 | Basic memorization |
| 50-100 examples | 10-15 | Good learning |
| 200-500 examples | 5-10 | Excellent results |
| 1000+ examples | 3-5 | Production quality |

---

## ⚙️ Training Settings for CPU

### Recommended Configuration

| Setting | Value | Why |
|---------|-------|-----|
| **Model** | `Qwen/Qwen2-0.5B-Instruct` | Small, instruction-tuned |
| **Epochs** | 10-20 | Small datasets need more passes |
| **Batch Size** | 1 | Memory efficiency |
| **Grad Accumulation** | 8 | Simulates larger batches |
| **Learning Rate** | 2e-4 | Good for small models |
| **Max Length** | 256 | Covers most Q&A pairs |
| **LoRA Rank** | 8 | CPU-efficient |
| **LoRA Alpha** | 16 | Standard ratio |

### Command Line Training

```powershell
python ml_core/training_script.py `
  --job-id my-training `
  --dataset data.jsonl `
  --base-model "Qwen/Qwen2-0.5B-Instruct" `
  --output-dir ./output `
  --epochs 15 `
  --batch-size 1 `
  --grad-accum 8 `
  --learning-rate 2e-4 `
  --max-length 256 `
  --lora-rank 8 `
  --lora-alpha 16
```

---

## 📦 Using in LM Studio

After training, export to GGUF:

1. **Merge LoRA adapters** with base model
2. **Convert to GGUF** using llama.cpp
3. **Load in LM Studio** with correct prompt template

### LM Studio Prompt Template

Set these in LM Studio → Settings → Prompt Template:

| Field | Value |
|-------|-------|
| Before User | `### Instruction:\n` |
| After User | `\n\n` |
| Before Assistant | `### Response:\n` |
| After Assistant | `\n\n` |

---

## 🔍 Troubleshooting

### Model Gives Gibberish Responses

**Cause:** Using completion model (DistilGPT2/GPT-2) for Q&A task

**Solution:** Use instruction-tuned model like `Qwen/Qwen2-0.5B-Instruct`

### Out of Memory Error

**Cause:** Model too large or max_length too high

**Solutions:**
- Use smaller model (SmolLM-360M)
- Reduce `--max-length` to 128
- Add `--stream` flag
- Close other applications

### Training Too Slow

**Cause:** CPU training is inherently slow

**Solutions:**
- Use smaller model (SmolLM vs TinyLlama)
- Reduce epochs for testing
- Use `--lora-rank 4` for faster training

---

## 📁 Project Structure

```
Mobius-LLM-Fine-tuning-Engine/
├── gui/                    # PyQt6 Desktop Application
│   ├── main.py            # Entry point
│   ├── main_window.py     # Main window UI
│   ├── steps/             # Wizard step panels
│   └── api/               # Backend API client
├── ml_core/               # Python ML Training
│   ├── training_script.py # Main training script
│   ├── data_loader.py     # Dataset loading
│   ├── convert_to_gguf.py # GGUF conversion
│   └── cpu_models.txt     # Model recommendations
├── src/main/java/         # Java Backend
│   └── com/llmtrainer/    # Backend services
├── data/                  # Training data storage
└── pom.xml               # Maven build config
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Adil Ijaz**
- GitHub: [@Adil-Ijaz7](https://github.com/Adil-Ijaz7)

---

<div align="center">

⭐ **Star this repo if you find it helpful!** ⭐

</div>
