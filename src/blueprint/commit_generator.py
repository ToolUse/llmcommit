"""Git commit message generator using AI models."""

import subprocess
import sys
import logging
from typing import List, Optional

from blueprint.ai_service import AIService


def get_git_diff(max_chars: int = 5000, debug: bool = False) -> str:
    """Get the git diff of staged changes, or unstaged if no staged changes.
    Filters out deleted files from the diff.

    Args:
        max_chars: Maximum number of characters to return
        debug: Whether to enable debug logging

    Returns:
        Git diff as string

    Raises:
        SystemExit: If not a git repository or git not installed
    """
    logger = logging.getLogger(__name__)

    try:
        logger.debug("Checking for staged changes")
        diff = subprocess.check_output(
            ["git", "diff", "--cached", "--diff-filter=ACMTU"], text=True
        )
        if not diff:
            logger.debug("No staged changes found, checking for unstaged changes")
            diff = subprocess.check_output(
                ["git", "diff", "--diff-filter=ACMTU"], text=True
            )

        if debug:
            logger.debug(f"Git diff (truncated): {diff[:200]}...")
        logger.debug(f"Got git diff with length {len(diff)} chars")
        return diff[:max_chars]  # Limit to max_chars characters
    except subprocess.CalledProcessError as e:
        logger.error(f"Git diff failed: {e}")
        print("Error: Not a git repository or git is not installed.")
        sys.exit(1)


def query_ai_service(
    prompt: str,
    service_type: str,
    ollama_model: str,
    jan_model: str,
    debug: bool = False,
) -> str:
    """Query AI service with the given prompt.

    Args:
        prompt: Prompt text to send to AI service
        service_type: Type of AI service ('ollama' or 'jan')
        ollama_model: Model name for Ollama
        jan_model: Model name for Jan AI
        debug: Whether to enable debug logging

    Returns:
        Response from AI service

    Raises:
        SystemExit: If there's an error querying the AI service
    """
    logger = logging.getLogger(__name__)

    try:
        print("Generating commit messages...", end="", flush=True)
        logger.debug(
            f"Querying {service_type} with model {ollama_model if service_type == 'ollama' else jan_model}"
        )

        if debug:
            logger.debug(f"Prompt: {prompt[:200]}...")

        ai_service = AIService(
            service_type,
            model=ollama_model if service_type == "ollama" else jan_model,
            debug=debug,
        )

        response = ai_service.query(prompt)
        print("Done!")

        if debug:
            logger.debug(f"AI response (truncated): {response[:200]}...")
        logger.debug(f"Received response with length {len(response)} chars")

        return response
    except Exception as e:
        logger.error(f"Error querying {service_type}: {e}")
        print(f"\nError querying {service_type.capitalize()}: {e}")
        sys.exit(1)


def parse_commit_messages(response: str, debug: bool = False) -> List[str]:
    """Parse the LLM response into a list of commit messages.

    Args:
        response: Text response from AI service
        debug: Whether to enable debug logging

    Returns:
        List of extracted commit messages
    """
    logger = logging.getLogger(__name__)
    logger.debug("Parsing commit messages from AI response")

    messages = []
    for line in response.split("\n"):
        line = line.strip()
        if debug:
            logger.debug(f"Processing line: {line}")

        if line.startswith(("1.", "2.", "3.")):
            message = line.split(".", 1)[1].strip()
            # Strip surrounding single quotes if present
            if message.startswith("'") and message.endswith("'"):
                message = message[1:-1]
            messages.append(message)
            logger.debug(f"Extracted message: {message}")

    logger.debug(f"Parsed {len(messages)} commit messages")
    return messages


def select_message_with_fzf(
    messages: List[str],
    use_vim: bool = False,
    use_num: bool = False,
    debug: bool = False,
) -> Optional[str]:
    """Use fzf to select a commit message, with option to regenerate.

    Args:
        messages: List of commit messages to select from
        use_vim: Whether to use vim-style navigation
        use_num: Whether to display numbers for selection
        debug: Whether to enable debug logging

    Returns:
        Selected message, "regenerate" to regenerate messages, or None if cancelled
    """
    logger = logging.getLogger(__name__)
    logger.debug("Displaying fzf selector for commit messages")

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
            logger.debug("Using vim-style navigation in fzf")

        if use_num:
            for i, msg in enumerate(messages):
                messages[i] = f"{i+1}. {msg}"
            fzf_args.extend(
                [
                    "--bind",
                    "1:accept-non-empty,2:accept-non-empty,3:accept-non-empty,4:accept-non-empty",
                ]
            )
            logger.debug("Using number selection in fzf")

        logger.debug(f"Displaying {len(messages)} options in fzf")
        result = subprocess.run(
            fzf_args,
            input="\n".join(messages),
            capture_output=True,
            text=True,
        )
        if result.returncode == 130:  # User pressed ESC
            logger.debug("User cancelled selection with ESC")
            return None
        selected = result.stdout.strip()
        logger.debug(f"User selected: '{selected}'")

        if selected == "Regenerate messages" or selected == "4. Regenerate messages":
            logger.debug("User chose to regenerate messages")
            return "regenerate"

        final_selection = (
            selected.split(". ", 1)[1] if use_num and selected else selected
        )
        logger.debug(f"Final selection: '{final_selection}'")
        return final_selection
    except subprocess.CalledProcessError as e:
        logger.error(f"fzf selection failed: {e}")
        print("Error: fzf selection failed.")
        return None


def create_commit(message: str, debug: bool = False) -> bool:
    """Create a git commit with the selected message.

    Args:
        message: Commit message to use
        debug: Whether to enable debug logging

    Returns:
        True if commit was successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Creating commit with message: '{message}'")

    try:
        subprocess.run(["git", "commit", "-m", message], check=True)
        logger.debug("Commit created successfully")
        print(f"Committed with message: {message}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create commit: {e}")
        print("Error: Failed to create commit.")
        return False


def generate_commit_messages(
    diff: str,
    max_chars: int = 75,
    service_type: str = "ollama",
    ollama_model: str = "llama3.1",
    jan_model: str = "Llama 3.1",
    debug: bool = False,
) -> List[str]:
    """Generate commit messages based on git diff.

    Args:
        diff: Git diff to generate commit messages for
        max_chars: Suggested maximum characters for commit messages
        service_type: 'ollama' or 'jan'
        ollama_model: Model name for Ollama
        jan_model: Model name for Jan AI
        debug: Whether to enable debug logging

    Returns:
        List of generated commit messages
    """
    logger = logging.getLogger(__name__)
    logger.debug("Generating commit messages")

    prompt = f"""
    Your task is to generate three concise, informative git commit messages based on the following git diff.
    Be sure that each commit message reflects the entire diff.
    It is very important that the entire commit is clear and understandable with each of the three options. 
    Try to fit each commit message in {max_chars} characters.
    Each message should be on a new line, starting with a number and a period (e.g., '1.', '2.', '3.').
    Here's the diff:\n\n{diff}"""

    logger.debug(f"Created prompt with length {len(prompt)} chars")
    response = query_ai_service(
        prompt, service_type, ollama_model, jan_model, debug=debug
    )

    if debug and response:
        logger.debug(f"Full response from LLM: {response}")
    elif not response:
        logger.error("Received empty response from AI service")

    messages = parse_commit_messages(response, debug=debug)
    logger.debug(f"Generated {len(messages)} commit messages")
    return messages
