"""Command-line interface for LLM-powered commit message generator."""

import argparse
import os
import sys
import time

from blueprint.commit_generator import (
    get_git_diff,
    generate_commit_messages,
    select_message_with_fzf,
    create_commit,
)


def main():
    """Main entry point for the CLI application."""
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
    JAN_MODEL = os.getenv("JAN_MODEL", "llama 3.1")

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
    args = parser.parse_args()

    # Start timing
    start_time = time.time()

    # Get git diff
    diff = get_git_diff()
    if not diff:
        print("No changes to commit.")
        sys.exit(0)

    # Generate commit messages
    service_type = "ollama" if args.ollama else "jan"
    commit_messages = generate_commit_messages(
        diff=diff,
        max_chars=args.max_chars,
        service_type=service_type,
        ollama_model=OLLAMA_MODEL,
        jan_model=JAN_MODEL,
    )

    # Stop timing for initial generation
    end_time = time.time()

    # Show analytics if requested
    if args.analytics:
        print(f"\nAnalytics:")
        print(
            f"Time taken to generate commit messages: {end_time - start_time:.2f} seconds"
        )
        print(f"Inference used: {'Ollama' if args.ollama else 'Jan AI'}")
        print(f"Model name: {OLLAMA_MODEL if args.ollama else JAN_MODEL}")
        print("")  # Add a blank line for better readability

    # Check if we have messages
    if not commit_messages:
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

            commit_messages = generate_commit_messages(
                diff=diff,
                max_chars=args.max_chars,
                service_type=service_type,
                ollama_model=OLLAMA_MODEL,
                jan_model=JAN_MODEL,
            )

            end_time = time.time()

            if args.analytics:
                print(f"\nRegeneration Analytics:")
                print(
                    f"Time taken to regenerate commit messages: {end_time - start_time:.2f} seconds"
                )
                print("")  # Add a blank line for better readability

            if not commit_messages:
                print("Error: Could not generate commit messages.")
                sys.exit(1)
        elif selected_message:
            create_commit(selected_message)
            break
        else:
            print("Commit messages rejected. Please create commit message manually.")
            break


if __name__ == "__main__":
    main()
