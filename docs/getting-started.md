# Getting Started with LLM Commit Generator

Get started with this Blueprint using one of the options below:

---

## Installation

### Prerequisites

Before you begin, make sure you have:

1. **Python 3.10 or higher** installed
2. **Git** installed and configured
3. **fzf** installed for the terminal UI (see [installation guide](https://github.com/junegunn/fzf#installation))
4. Either:
   - **Jan AI** installed for local inference ([install guide](https://jan.ai/))
   - Or **Ollama** as an alternative local inference option ([install guide](https://ollama.ai/download))

### Install from PyPI

The easiest way to install LLM Commit Generator is via pip:

```bash
pip install llm-commit-generator
```

### Install from Source

Alternatively, you can install from source:

```bash
git clone https://github.com/tooluse/llmcommit.git
cd llmcommit
pip install -e .
```

## Setup

### For Inference with Jan AI (Default)

1. Install and launch Jan AI from [jan.ai](https://jan.ai/)
2. Download a model (like llama 3.1) through the Jan AI interface
3. Ensure the Jan AI application is running
4. (Optional) Set a custom model:
   ```bash
   export JAN_MODEL="your-preferred-model"
   ```

### For Inference with Ollama

1. Start the Ollama service
2. Pull a model (we recommend llama3.1):
   ```bash
   ollama pull llama3.1
   ```
3. (Optional) Set a custom model:
   ```bash
   export OLLAMA_MODEL="your-preferred-model"
   ```

## Usage

### Basic Usage

1. Make changes to your files in a git repository
2. Run:
   ```bash
   lcm
   ```
3. Select one of the generated commit messages using the arrow keys or number keys
4. Press Enter to commit with the selected message, or Esc to cancel

### Advanced Options

```bash
# Use Ollama instead of Jan AI
lcm --ollama

# Show performance analytics
lcm --analytics

# Use vim-style navigation in fzf
lcm --vim

# Use number selection for messages
lcm --num

# Set the maximum characters for commit messages
lcm --max_chars 100
```

## What's Next?

- See the [Step-by-Step Guide](step-by-step-guide.md) to understand how LLM Commit Generator works
- Learn about [customization options](customization.md) to tailor it to your needs
