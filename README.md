<p align="center">
  <picture>
    <!-- When the user prefers dark mode, show the white logo -->
    <source media="(prefers-color-scheme: dark)" srcset="./images/Blueprint-logo-white.png">
    <!-- When the user prefers light mode, show the black logo -->
    <source media="(prefers-color-scheme: light)" srcset="./images/Blueprint-logo-black.png">
    <!-- Fallback: default to the black logo -->
    <img src="./images/Blueprint-logo-black.png" width="35%" alt="Project logo"/>
  </picture>
</p>

# LLM Commit Generator

This blueprint guides you to easily generate AI-powered git commit messages based on your code changes. It uses local LLMs via Jan AI or Ollama to analyze git diffs and suggest concise, relevant commit messages.

📘 To explore this project further and discover other Blueprints, visit the [**Blueprints Hub**](https://developer-hub.mozilla.ai/).

👉 📖 For more detailed guidance on using this project, please visit our [**Docs here**](https://tooluse.github.io/llmcommit/)

### Built with

- Python 3.10+
- [Jan AI](https://jan.ai) for a user-friendly local AI experience
- Open-source LLMs via [Ollama](https://ollama.ai) as an alternative
- fzf for terminal UI

## Quick-start

1. Make sure you have Git, Python 3.10+, and pip installed
2. Install the package:
   ```bash
   pip install llm-commit-generator
   ```
3. Choose one of the following local inference options:

   **Option 1: Jan AI (Default)**

   - Install [Jan AI](https://jan.ai) and download a model (like Llama 3.1) through its interface
   - Start the Jan AI application and ensure it's running

   **Option 2: Ollama**

   - Install [Ollama](https://ollama.ai) and pull a model:

   ```bash
   ollama pull llama3.1
   ```

4. After adding your changes to your git repo, run:

   ```bash
   lcm
   ```

   For Ollama, use:

   ```bash
   lcm --ollama
   ```

## How it Works

1. The tool extracts your git diff (staged changes, or unstaged if no staged changes)
2. Sends the diff to an AI model with a prompt to generate concise commit messages
3. Presents you with message suggestions in a terminal UI using fzf
4. After selecting a message, commits your changes with the selected message

## Pre-requisites

- **System requirements**:

  - OS: Windows, macOS, or Linux
  - Python 3.10 or higher
  - Git
  - fzf (for terminal UI)
  - Jan AI or Ollama for local inference

- **Dependencies**:
  - Dependencies listed in `pyproject.toml`

## Troubleshooting

- If you get `fzf: command not found`, install fzf: [fzf installation guide](https://github.com/junegunn/fzf#installation)
- For Jan AI issues, ensure the Jan AI application is running
- For Ollama issues, ensure the Ollama service is running and your model is pulled

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! To get started, you can check out the [CONTRIBUTING.md](CONTRIBUTING.md) file.
