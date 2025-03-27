"""Command-line interface for LLM-powered commit message generator."""

import argparse
import os
import sys
import time
import logging
import subprocess
from typing import List, Optional

from llm_commit_generator.commit_generator import (
    get_git_diff,
    generate_commit_messages,
    create_commit,
)

DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"
DEFAULT_JAN_MODEL = "llama3.2-3b-instruct"


def setup_logging(debug_mode):
    """Set up logging based on debug mode."""
    log_level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def select_message_with_fzf(
    messages: List[str],
    use_vim: bool = False,
    use_num: bool = False,
) -> Optional[str]:
    """Use fzf to select a commit message, with option to regenerate.

    Args:
        messages: List of commit messages to select from
        use_vim: Whether to use vim-style navigation
        use_num: Whether to display numbers for selection

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
                messages[i] = f"{i + 1}. {msg}"
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


def main():
    """Main entry point for the CLI application."""
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    JAN_MODEL = os.getenv("JAN_MODEL", DEFAULT_JAN_MODEL)

    parser = argparse.ArgumentParser(
        description="Generate git commit messages using LLMs."
    )
    parser.add_argument(
        "--ollama",
        action="store_true",
        help="Use Ollama API instead of Jan AI (default is Jan AI)",
    )
    parser.add_argument(
        "--analytics", action="store_true", help="Display performance analytics"
    )
    parser.add_argument(
        "--vim", action="store_true", help="Use vim-style navigation in fzf"
    )
    parser.add_argument(
        "--num", action="store_true", help="Use number selection for commit messages"
    )
    parser.add_argument(
        "--max_chars",
        type=int,
        default=75,
        help="Suggested maximum number of characters for each commit message (default: 75)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Set up logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    logger.debug("Debug mode enabled")

    # Start timing
    start_time = time.time()

    # Get git diff
    logger.debug("Getting git diff")
    diff = get_git_diff(debug=args.debug)
    if not diff:
        logger.error("No changes to commit")
        print("No changes to commit.")
        sys.exit(0)

    # Generate commit messages
    service_type = "ollama" if args.ollama else "jan"
    logger.debug(f"Generating commit messages using {service_type}")
    commit_messages = generate_commit_messages(
        diff=diff,
        max_chars=args.max_chars,
        service_type=service_type,
        ollama_model=OLLAMA_MODEL,
        jan_model=JAN_MODEL,
        debug=args.debug,
    )

    # Stop timing for initial generation
    end_time = time.time()

    # Show analytics if requested
    if args.analytics:
        print("\nAnalytics:")
        print(
            f"Time taken to generate commit messages: {end_time - start_time:.2f} seconds"
        )
        print(f"Inference used: {'Ollama' if args.ollama else 'Jan AI'}")
        print(f"Model name: {OLLAMA_MODEL if args.ollama else JAN_MODEL}")
        print("")  # Add a blank line for better readability

    # Check if we have messages
    if not commit_messages:
        logger.error("Could not generate commit messages")
        print("Error: Could not generate commit messages.")
        sys.exit(1)

    # Select message or regenerate
    while True:
        selected_message = select_message_with_fzf(
            commit_messages, use_vim=args.vim, use_num=args.num
        )

        if selected_message == "regenerate":
            # Time regeneration
            start_time = time.time()
            logger.debug("Regenerating commit messages")

            commit_messages = generate_commit_messages(
                diff=diff,
                max_chars=args.max_chars,
                service_type=service_type,
                ollama_model=OLLAMA_MODEL,
                jan_model=JAN_MODEL,
                debug=args.debug,
            )

            end_time = time.time()

            if args.analytics:
                print("\nRegeneration Analytics:")
                print(
                    f"Time taken to regenerate commit messages: {end_time - start_time:.2f} seconds"
                )
                print("")  # Add a blank line for better readability

            if not commit_messages:
                logger.error("Could not regenerate commit messages")
                print("Error: Could not generate commit messages.")
                sys.exit(1)
        elif selected_message:
            logger.debug(f"Creating commit with message: {selected_message}")
            create_commit(selected_message, debug=args.debug)
            break
        else:
            logger.debug("Commit messages rejected")
            print("Commit messages rejected. Please create commit message manually.")
            break


if __name__ == "__main__":
    main()
