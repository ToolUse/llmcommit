"""Prompts used for AI services."""


def get_commit_message_prompt(diff: str, max_chars: int = 200) -> str:
    """Generate the prompt for commit message generation.

    Args:
        diff: Git diff to generate commit messages for
        max_chars: Suggested maximum characters for commit messages

    Returns:
        Formatted prompt string
    """
    return f"""
Your task is to generate three concise, informative git commit messages based on the following git diff.
Be sure that each commit message reflects the entire diff.
Keep the commit messages under {max_chars} characters.
It is very important that the entire commit is clear and understandable with each of the three options.
Each message should be on a new line, starting with a number and a period (e.g., '1.', '2.', '3.').
Here's the diff:\n\n{diff}
"""
