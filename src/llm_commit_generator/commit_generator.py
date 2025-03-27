"""Git commit message generator using AI models."""

import subprocess
import sys
import logging
from typing import List

from llm_commit_generator.ai_service import AIService
from llm_commit_generator.prompts import get_commit_message_prompt


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

        # Use trim_diff to intelligently truncate if needed
        if len(diff) > max_chars:
            diff = trim_diff(diff, max_chars, debug)

        return diff
    except subprocess.CalledProcessError as e:
        logger.error(f"Git diff failed: {e}")
        print("Error: Not a git repository or git is not installed.")
        sys.exit(1)


def trim_diff(diff: str, max_chars: int, debug: bool = False) -> str:
    """Intelligently trim a git diff to stay under max_chars by preserving complete files and hunks.

    Args:
        diff: The git diff to trim
        max_chars: Maximum character limit
        debug: Whether to enable debug logging

    Returns:
        Trimmed diff with complete files and hunks
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Trimming diff to stay under {max_chars} chars")

    if len(diff) <= max_chars:
        return diff

    lines = diff.split("\n")
    result_lines: list[str] = []
    current_length = 0
    in_hunk = False

    # First, count the number of actual change lines (+ or -) to prioritize
    change_lines_count = 0
    for line in lines:
        stripped = line.lstrip()
        if (stripped.startswith("+") or stripped.startswith("-")) and stripped not in (
            "+",
            "-",
        ):
            change_lines_count += 1

    # If there are few changes, we want to keep ALL of them
    keep_all_changes = change_lines_count < 50  # arbitrary threshold
    if keep_all_changes and debug:
        logger.debug(
            f"Only {change_lines_count} actual change lines - will prioritize keeping all changes"
        )

    # Initialize important indices set
    important_indices: set[int] = set()

    # First pass: collect critical changes and their context
    if keep_all_changes:
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            # Mark change lines and surrounding context
            if (
                stripped.startswith("+") or stripped.startswith("-")
            ) and stripped not in ("+", "-"):
                # Mark this line and surrounding context (3 lines before and after)
                for j in range(max(0, i - 3), min(len(lines), i + 4)):
                    important_indices.add(j)
            # Always mark hunk headers
            elif stripped.startswith("@@"):
                important_indices.add(i)

    # Second pass: keep important lines and natural boundaries
    for i, line in enumerate(lines):
        line_length = len(line) + 1  # +1 for newline
        stripped = line.lstrip()

        # Start of a new file
        if line.startswith("diff --git"):
            # If adding this new file would exceed our limit, stop here
            if current_length + line_length > max_chars and result_lines:
                # Unless this file contains important changes we want to keep
                if keep_all_changes and any(
                    j in important_indices for j in range(i, min(len(lines), i + 20))
                ):
                    if debug:
                        logger.debug(
                            f"Keeping file at line {i} despite size limit due to important changes"
                        )
                else:
                    break
            in_hunk = False

        # Start of a new hunk
        elif stripped.startswith("@@"):
            in_hunk = True

        # If we're about to exceed the limit but this is an important line, keep it anyway
        if current_length + line_length > max_chars:
            if keep_all_changes and i in important_indices:
                if debug:
                    logger.debug(f"Keeping important line {i} despite size limit")
            # If we're not at a natural boundary and this isn't an important line, stop here
            elif not in_hunk and not line.startswith("diff --git"):
                # We're between hunks or files, safe to stop here
                break

        # Add the line
        result_lines.append(line)
        current_length += line_length

    result = "\n".join(result_lines)

    if debug:
        logger.debug(f"Trimmed diff from {len(diff)} chars to {len(result)} chars")
        logger.debug(f"Preserved {len(result_lines)} of {len(lines)} lines")
        # Check if we preserved all important changes
        if keep_all_changes:
            preserved_important = sum(
                1 for i in important_indices if i < len(result_lines)
            )
            logger.debug(
                f"Preserved {preserved_important} of {len(important_indices)} important lines"
            )

    return result


def filter_diff(
    raw_diff: str, include_filenames: bool = True, debug: bool = False
) -> str:
    """Filter git diff to remove metadata and keep only meaningful changes.

    Args:
        raw_diff: Raw git diff output
        include_filenames: Whether to keep filenames in the output
        debug: Whether to enable debug logging

    Returns:
        Filtered diff with only relevant content
    """
    logger = logging.getLogger(__name__)
    logger.debug("Filtering git diff to remove metadata")

    if not raw_diff:
        return ""

    filtered_lines = []
    current_file = None

    for line in raw_diff.split("\n"):
        # Skip common metadata lines
        if line.startswith("diff --git") or line.startswith("index "):
            continue

        # Handle filename markers but keep the filename
        if line.startswith("--- "):
            continue
        if line.startswith("+++ "):
            if line.startswith("+++ b/") and include_filenames:
                current_file = line[6:]  # Remove the "+++ b/" prefix
            continue

        # Add filename header if we just found a new file
        if current_file and include_filenames:
            filtered_lines.append(f"File: {current_file}")
            current_file = None

        # Keep everything else: hunk headers, context lines, and actual changes
        filtered_lines.append(line)

    filtered_diff = "\n".join(filtered_lines)

    if debug:
        logger.debug(
            f"Original diff: {len(raw_diff)} chars, Filtered: {len(filtered_diff)} chars"
        )
        logger.debug(f"Removed {len(raw_diff) - len(filtered_diff)} chars of metadata")
        logger.debug(
            "Filtered diff preview (first 500 chars):\n" + filtered_diff[:500]
            if filtered_diff
            else "(empty)"
        )

    return filtered_diff


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

        ai_service = AIService(
            service_type,
            model=ollama_model if service_type == "ollama" else jan_model,
            debug=debug,
        )

        response = ai_service.query(prompt)
        print("Done!")

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
            if (message.startswith("'") and message.endswith("'")) or (
                message.startswith('"') and message.endswith('"')
            ):
                message = message[1:-1]
            messages.append(message)
            logger.debug(f"Extracted message: {message}")

    logger.debug(f"Parsed {len(messages)} commit messages")
    return messages


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
    max_chars: int = 200,
    service_type: str = "ollama",
    ollama_model: str = "llama3.1",
    jan_model: str = "llama3.2-3b-instruct",
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

    # Filter the diff to remove noise
    filtered_diff = filter_diff(diff, include_filenames=True, debug=debug)

    # Explicit logging of the filtered diff for debugging
    if debug:
        logger.debug(f"FILTERED DIFF used for prompting LLM:\n{filtered_diff}")
        if not filtered_diff:
            logger.warning("FILTERED DIFF is empty")

    prompt = get_commit_message_prompt(diff, max_chars)

    logger.debug(f"Created prompt with length {len(prompt)} chars")
    if debug:
        logger.debug("FINAL PROMPT:\n" + prompt)

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
