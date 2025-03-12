"""Git commit message generator using AI models."""

import os
import subprocess
import sys
import time
from typing import List, Optional

from blueprint.ai_service import AIService


def get_git_diff(max_chars: int = 5000) -> str:
    """Get the git diff of staged changes, or unstaged if no staged changes.

    Args:
        max_chars: Maximum number of characters to return

    Returns:
        Git diff as string

    Raises:
        SystemExit: If not a git repository or git not installed
    """
    try:
        diff = subprocess.check_output(["git", "diff", "--cached"], text=True)
        if not diff:
            diff = subprocess.check_output(["git", "diff"], text=True)
        return diff[:max_chars]  # Limit to max_chars characters
    except subprocess.CalledProcessError:
        print("Error: Not a git repository or git is not installed.")
        sys.exit(1)


def query_ai_service(
    prompt: str, service_type: str, ollama_model: str, jan_model: str
) -> str:
    """Query AI service with the given prompt.

    Args:
        prompt: Prompt text to send to AI service
        service_type: Type of AI service ('ollama' or 'jan')
        ollama_model: Model name for Ollama
        jan_model: Model name for Jan AI

    Returns:
        Response from AI service

    Raises:
        SystemExit: If there's an error querying the AI service
    """
    try:
        print("Generating commit messages...", end="", flush=True)
        ai_service = AIService(
            service_type, model=ollama_model if service_type == "ollama" else jan_model
        )
        response = ai_service.query(prompt)
        print("Done!")
        return response
    except Exception as e:
        print(f"\nError querying {service_type.capitalize()}: {e}")
        sys.exit(1)


def parse_commit_messages(response: str) -> List[str]:
    """Parse the LLM response into a list of commit messages.

    Args:
        response: Text response from AI service

    Returns:
        List of extracted commit messages
    """
    messages = []
    for line in response.split("\n"):
        if line.strip().startswith(("1.", "2.", "3.")):
            messages.append(line.split(".", 1)[1].strip())
    return messages


def select_message_with_fzf(
    messages: List[str], use_vim: bool = False, use_num: bool = False
) -> Optional[str]:
    """Use fzf to select a commit message, with option to regenerate.

    Args:
        messages: List of commit messages to select from
        use_vim: Whether to use vim-style navigation
        use_num: Whether to display numbers for selection

    Returns:
        Selected message, "regenerate" to regenerate messages, or None if cancelled
    """
    try:
        messages.append("Regenerate messages")
        fzf_args = [
            "fzf",
            "--height=10",
            "--layout=reverse",
            "--prompt=Select a commit message (ESC to cancel): ",
            "--no-info",
            "--margin=1,2",
            "--border",
            "--color=prompt:#D73BC9,pointer:#D73BC9",
        ]

        if use_vim:
            fzf_args.extend(["--bind", "j:down,k:up"])

        if use_num:
            for i, msg in enumerate(messages):
                messages[i] = f"{i+1}. {msg}"
            fzf_args.extend(
                [
                    "--bind",
                    "1:accept-non-empty,2:accept-non-empty,3:accept-non-empty,4:accept-non-empty",
                ]
            )

        result = subprocess.run(
            fzf_args,
            input="\n".join(messages),
            capture_output=True,
            text=True,
        )
        if result.returncode == 130:  # User pressed ESC
            return None
        selected = result.stdout.strip()
        if selected == "Regenerate messages" or selected == "4. Regenerate messages":
            return "regenerate"
        return selected.split(". ", 1)[1] if use_num and selected else selected
    except subprocess.CalledProcessError:
        print("Error: fzf selection failed.")
        return None


def create_commit(message: str) -> bool:
    """Create a git commit with the selected message.

    Args:
        message: Commit message to use

    Returns:
        True if commit was successful, False otherwise
    """
    try:
        subprocess.run(["git", "commit", "-m", message], check=True)
        print(f"Committed with message: {message}")
        return True
    except subprocess.CalledProcessError:
        print("Error: Failed to create commit.")
        return False


def generate_commit_messages(
    diff: str,
    max_chars: int = 75,
    service_type: str = "ollama",
    ollama_model: str = "llama3.1",
    jan_model: str = "Llama 3.1",
) -> List[str]:
    """Generate commit messages based on git diff.

    Args:
        diff: Git diff to generate commit messages for
        max_chars: Suggested maximum characters for commit messages
        service_type: 'ollama' or 'jan'
        ollama_model: Model name for Ollama
        jan_model: Model name for Jan AI

    Returns:
        List of generated commit messages
    """
    prompt = f"""
    Your task is to generate three concise, informative git commit messages based on the following git diff.
    Be sure that each commit message reflects the entire diff.
    It is very important that the entire commit is clear and understandable with each of the three options. 
    Try to fit each commit message in {max_chars} characters.
    Each message should be on a new line, starting with a number and a period (e.g., '1.', '2.', '3.').
    Here's the diff:\n\n{diff}"""

    response = query_ai_service(prompt, service_type, ollama_model, jan_model)
    return parse_commit_messages(response)
