# **Step-by-Step Guide: How LLM Commit Generator Works**

This guide explains exactly how LLM Commit Generator works, from extracting your git diff to generating commit messages and allowing you to select the best one.

## **Overview**

LLM Commit Generator is a tool that leverages large language models to automatically generate meaningful git commit messages based on your code changes. It uses Jan AI by default for local inference, with Ollama as an alternative option, giving you flexibility while keeping your data private.

The process follows these steps:

1. Extract git diff from your repository
2. Send the diff to an AI model for analysis
3. Parse the AI's response into commit message options
4. Present the options in a user-friendly interface
5. Create a git commit with your selected message

## **Step 1: Extracting the Git Diff**

When you run `lcm`, the tool first tries to get the staged changes using `git diff --cached`. If there are no staged changes, it falls back to unstaged changes using `git diff`. This ensures that the AI model sees only the relevant changes you want to commit.

The diff is limited to 5000 characters to avoid overwhelming the AI model and to respect the context windows of various models.

```python
def get_git_diff(max_chars: int = 5000) -> str:
    try:
        diff = subprocess.check_output(["git", "diff", "--cached"], text=True)
        if not diff:
            diff = subprocess.check_output(["git", "diff"], text=True)
        return diff[:max_chars]
    except subprocess.CalledProcessError:
        print("Error: Not a git repository or git is not installed.")
        sys.exit(1)
```

## **Step 2: Generating Commit Messages**

The extracted diff is sent to an AI model with a carefully crafted prompt that asks it to generate three concise, informative commit messages. The prompt specifies:

- Generate three options
- Make each message reflect the entire diff
- Keep messages concise (default 75 characters)
- Format with numbering for easy parsing

Based on your configuration, the tool will use either:

- Jan AI for local inference (default)
- Ollama as an alternative local inference option

## **Step 3: Presenting Options to User**

The AI's response is parsed to extract the suggested commit messages, which are then presented to you using the fzf terminal interface. This provides a clean, interactive way to browse and select the best message.

Options include:

- Use arrow keys or vim-style navigation to select a message
- Use number keys for quick selection
- Option to regenerate messages if none are satisfactory
- Press Esc to cancel and write your own message

## **Step 4: Creating the Commit**

After selecting a message, LLM Commit Generator uses `git commit -m "your selected message"` to create the commit with your chosen message.

## **Architecture**

LLM Commit Generator is organized into several modules:

- `ai_service.py`: Handles communication with AI providers (Jan AI/Ollama)
- `commit_generator.py`: Core functions for generating and parsing commit messages
- `cli.py`: Command-line interface and options handling

This modular design makes it easy to extend and customize the tool for your specific needs.

## 🎨 **Customizing the Blueprint**

To better understand how you can tailor this Blueprint to suit your specific needs, please visit the **[Customization Guide](customization.md)**.

## 🤝 **Contributing to the Blueprint**

Want to help improve or extend this Blueprint? Check out the **[Future Features & Contributions Guide](future-features-contributions.md)** to see how you can contribute your ideas, code, or feedback to make this Blueprint even better!
