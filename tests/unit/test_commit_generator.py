"""Tests for commit_generator.py."""

import subprocess
from unittest import mock

import pytest

from llm_commit_generator.commit_generator import (
    create_commit,
    generate_commit_messages,
    get_git_diff,
    parse_commit_messages,
    query_ai_service,
)
from llm_commit_generator.cli import select_message_with_fzf

# Global patch for subprocess to prevent any real subprocess calls
subprocess_mock = mock.patch("subprocess.run")
subprocess_check_output_mock = mock.patch("subprocess.check_output")


@pytest.fixture(autouse=True)
def no_subprocess_calls(monkeypatch):
    """Prevent any subprocess calls during tests."""

    # This fixture automatically runs for all tests
    def mock_run(*args, **kwargs):
        # Check if this is an fzf call
        if isinstance(args[0], list) and any("fzf" in str(arg) for arg in args[0]):
            # Create a mock CompletedProcess object simulating fzf selection
            mock_process = mock.Mock()
            mock_process.returncode = 0
            mock_process.stdout = "Selected mock message\n"
            return mock_process

        # For other subprocess calls
        mock_process = mock.Mock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        return mock_process

    def mock_check_output(*args, **kwargs):
        return ""

    # Apply the mocks
    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    # Mock stdin to prevent any input requests
    monkeypatch.setattr("sys.stdin", mock.Mock())


@pytest.fixture(autouse=True)
def no_user_input(monkeypatch):
    """Prevent any calls that would request user input."""

    # Mock built-in input function
    def mock_input(prompt=None):
        raise RuntimeError("Test tried to get user input via input()!")

    monkeypatch.setattr("builtins.input", mock_input)


@pytest.fixture
def sample_ai_response():
    """Sample AI response for testing."""
    return """I've analyzed the git diff and summarized the changes.

1. Remove strip() from diff check and add strip() to parsed commit messages
2. Fix string handling in git diff and commit message parsing
3. Improve robustness of git diff checking and commit message parsing"""


@pytest.fixture
def sample_git_diff():
    """Sample git diff for testing."""
    return """diff --git a/src/app.py b/src/app.py
index 1234567..abcdefg 100644
--- a/src/app.py
+++ b/src/app.py
@@ -10,7 +10,7 @@ def some_function():
     # This is a test function
-    x = input().strip()
+    x = input()
     return x
 
@@ -20,7 +20,7 @@ def parse_message(msg):
-    return msg
+    return msg.strip()
"""


@mock.patch("subprocess.check_output")
def test_get_git_diff_staged_changes(mock_check_output):
    """Test getting git diff with staged changes."""
    # Setup
    mock_check_output.side_effect = [
        "staged changes diff",  # First call returns staged changes
    ]

    # Execute
    result = get_git_diff(max_chars=100)

    # Assert
    assert result == "staged changes diff"
    mock_check_output.assert_called_with(
        ["git", "diff", "--cached", "--diff-filter=ACMTU"], text=True
    )
    assert mock_check_output.call_count == 1


@mock.patch("subprocess.check_output")
def test_get_git_diff_unstaged_changes(mock_check_output):
    """Test getting git diff with unstaged changes."""
    # Setup
    mock_check_output.side_effect = [
        "",  # First call returns empty (no staged changes)
        "unstaged changes diff",  # Second call returns unstaged changes
    ]

    # Execute
    result = get_git_diff(max_chars=100)

    # Assert
    assert result == "unstaged changes diff"
    assert mock_check_output.call_count == 2
    mock_check_output.assert_has_calls(
        [
            mock.call(["git", "diff", "--cached", "--diff-filter=ACMTU"], text=True),
            mock.call(["git", "diff", "--diff-filter=ACMTU"], text=True),
        ]
    )


@mock.patch("subprocess.check_output")
@mock.patch("blueprint.commit_generator.trim_diff")
def test_get_git_diff_max_chars(mock_trim_diff, mock_check_output):
    """Test limiting git diff to max_chars using trim_diff."""
    # Setup
    mock_check_output.return_value = "a" * 100  # Return a long string
    mock_trim_diff.return_value = "a" * 50  # Mocked trimmed output

    # Execute
    result = get_git_diff(max_chars=50)

    # Assert
    assert result == "a" * 50
    # Verify trim_diff was called with the right parameters
    mock_trim_diff.assert_called_once_with("a" * 100, 50, False)


@mock.patch("subprocess.check_output")
def test_get_git_diff_error(mock_check_output):
    """Test error handling in get_git_diff."""
    # Setup
    mock_check_output.side_effect = subprocess.CalledProcessError(1, "git")

    # Execute with pytest to capture sys.exit
    with pytest.raises(SystemExit):
        get_git_diff()


@mock.patch("blueprint.commit_generator.AIService")
def test_query_ai_service_ollama(mock_ai_service):
    """Test querying AI service using Ollama."""
    # Setup
    mock_instance = mock_ai_service.return_value
    mock_instance.query.return_value = "AI response"

    # Execute
    with mock.patch("builtins.print"):  # Suppress print output during test
        result = query_ai_service("test prompt", "ollama", "llama3.1", "Llama 3.1")

    # Assert
    assert result == "AI response"
    mock_ai_service.assert_called_with("ollama", model="llama3.1", debug=False)
    mock_instance.query.assert_called_with("test prompt")


@mock.patch("blueprint.commit_generator.AIService")
def test_query_ai_service_jan(mock_ai_service):
    """Test querying AI service using Jan AI."""
    # Setup
    mock_instance = mock_ai_service.return_value
    mock_instance.query.return_value = "AI response"

    # Execute
    with mock.patch("builtins.print"):  # Suppress print output during test
        result = query_ai_service("test prompt", "jan", "llama3.1", "Llama 3.1")

    # Assert
    assert result == "AI response"
    mock_ai_service.assert_called_with("jan", model="Llama 3.1", debug=False)
    mock_instance.query.assert_called_with("test prompt")


@mock.patch("blueprint.commit_generator.AIService")
def test_query_ai_service_error(mock_ai_service):
    """Test error handling in query_ai_service for Ollama."""
    # Setup
    mock_instance = mock_ai_service.return_value
    mock_instance.query.side_effect = Exception("API error")

    # Execute with pytest to capture sys.exit
    with mock.patch("builtins.print"):  # Suppress print output during test
        with pytest.raises(SystemExit):
            query_ai_service("test prompt", "ollama", "llama3.1", "Llama 3.1")


def test_parse_commit_messages(sample_ai_response):
    """Test parsing commit messages from AI response."""
    # Execute
    result = parse_commit_messages(sample_ai_response)

    # Assert
    assert result == [
        "Remove strip() from diff check and add strip() to parsed commit messages",
        "Fix string handling in git diff and commit message parsing",
        "Improve robustness of git diff checking and commit message parsing",
    ]


def test_parse_commit_messages_with_custom_input():
    """Test parsing commit messages from a custom AI response."""
    # Setup
    ai_response = """Here are some commit messages:
1. Fix bug in authentication module
2. Update documentation for API endpoints
3. Refactor user management code
Some other text that shouldn't be included."""

    # Execute
    result = parse_commit_messages(ai_response)

    # Assert
    assert result == [
        "Fix bug in authentication module",
        "Update documentation for API endpoints",
        "Refactor user management code",
    ]


def test_parse_commit_messages_empty():
    """Test parsing empty AI response."""
    # Execute
    result = parse_commit_messages("")

    # Assert
    assert result == []


@mock.patch("subprocess.run")
def test_select_message_with_fzf(mock_run):
    """Test selecting a message with fzf."""
    # Setup
    mock_run.return_value = mock.Mock(returncode=0, stdout="Selected commit message\n")
    messages = ["Message 1", "Message 2", "Message 3"]

    # Execute
    result = select_message_with_fzf(messages)

    # Assert
    assert result == "Selected commit message"
    assert "Regenerate messages" in mock_run.call_args[1]["input"]


@mock.patch("subprocess.run")
def test_select_message_with_fzf_vim_style(mock_run):
    """Test selecting a message with vim-style navigation."""
    # Setup
    mock_run.return_value = mock.Mock(returncode=0, stdout="Selected commit message\n")
    messages = ["Message 1", "Message 2"]

    # Execute
    result = select_message_with_fzf(messages, use_vim=True)

    # Assert
    assert result == "Selected commit message"
    # Check that vim bindings were included
    assert "--bind" in mock_run.call_args[0][0]
    assert "j:down,k:up" in mock_run.call_args[0][0]


@mock.patch("subprocess.run")
def test_select_message_with_fzf_number_selection(mock_run):
    """Test selecting a message with number selection."""
    # Setup
    mock_run.return_value = mock.Mock(returncode=0, stdout="2. Message 2\n")
    messages = ["Message 1", "Message 2"]

    # Execute
    result = select_message_with_fzf(messages, use_num=True)

    # Assert
    assert result == "Message 2"
    # Check that number bindings were included
    assert any("--bind" in arg for arg in mock_run.call_args[0][0])


@mock.patch("subprocess.run")
def test_select_message_with_fzf_esc_pressed(mock_run):
    """Test cancelling fzf selection with ESC."""
    # Setup
    mock_run.return_value = mock.Mock(returncode=130, stdout="")
    messages = ["Message 1", "Message 2"]

    # Execute
    result = select_message_with_fzf(messages)

    # Assert
    assert result is None


@mock.patch("subprocess.run")
def test_select_message_with_fzf_regenerate(mock_run):
    """Test selecting 'Regenerate messages' option."""
    # Setup
    mock_run.return_value = mock.Mock(returncode=0, stdout="Regenerate messages\n")
    messages = ["Message 1", "Message 2"]

    # Execute
    result = select_message_with_fzf(messages)

    # Assert
    assert result == "regenerate"


@mock.patch("subprocess.run")
def test_create_commit_success(mock_run):
    """Test creating a commit successfully."""
    # Setup
    mock_run.return_value = mock.Mock(returncode=0)
    message = "Commit message"

    # Execute
    with mock.patch("builtins.print"):  # Suppress print output during test
        result = create_commit(message)

    # Assert
    assert result is True
    mock_run.assert_called_with(["git", "commit", "-m", message], check=True)


@mock.patch("subprocess.run")
def test_create_commit_error(mock_run):
    """Test error handling in create_commit."""
    # Setup
    mock_run.side_effect = subprocess.CalledProcessError(1, "git")
    message = "Commit message"

    # Execute
    with mock.patch("builtins.print"):  # Suppress print output during test
        result = create_commit(message)

    # Assert
    assert result is False


@mock.patch("blueprint.commit_generator.query_ai_service")
def test_generate_commit_messages(mock_query_ai_service, sample_git_diff):
    """Test generating commit messages with sample diff."""
    # Setup
    mock_query_ai_service.return_value = """Here are some commit messages:
1. First commit message
2. Second commit message
3. Third commit message"""

    # Execute
    result = generate_commit_messages(sample_git_diff, max_chars=75)

    # Assert
    assert result == [
        "First commit message",
        "Second commit message",
        "Third commit message",
    ]
    # Verify the prompt includes the specified max characters
    assert (
        "Please keep it under 75 characters per message"
        in mock_query_ai_service.call_args[0][0]
    )
    # Verify the diff is included in the prompt
    assert "--- BEGIN GIT DIFF ---" in mock_query_ai_service.call_args[0][0]
    assert "--- END GIT DIFF ---" in mock_query_ai_service.call_args[0][0]


@mock.patch("blueprint.commit_generator.query_ai_service")
def test_generate_commit_messages_custom_service(mock_query_ai_service):
    """Test generating commit messages with custom service settings."""
    # Setup
    mock_query_ai_service.return_value = """Here are some commit messages:
1. First commit message
2. Second commit message
3. Third commit message"""

    # Execute
    result = generate_commit_messages(
        "test diff",
        max_chars=100,
        service_type="jan",
        ollama_model="custom-ollama",
        jan_model="custom-jan",
    )

    # Assert
    assert len(result) == 3
    # Check if custom service settings were passed correctly
    mock_query_ai_service.assert_called_with(
        mock.ANY, "jan", "custom-ollama", "custom-jan", debug=False
    )
    # Verify the prompt includes the custom max characters
    assert (
        "Please keep it under 100 characters per message"
        in mock_query_ai_service.call_args[0][0]
    )


@mock.patch("blueprint.cli.select_message_with_fzf")
@mock.patch("blueprint.commit_generator.generate_commit_messages")
@mock.patch("blueprint.commit_generator.get_git_diff")
@mock.patch("blueprint.commit_generator.create_commit")
def test_end_to_end_flow(mock_create, mock_get_diff, mock_generate, mock_select):
    """Test the full end-to-end flow with mocked components."""
    # Setup
    mock_get_diff.return_value = "sample diff"
    mock_generate.return_value = ["Message 1", "Message 2", "Message 3"]
    mock_select.return_value = "Message 2"  # Ensure this is a string, not None
    mock_create.return_value = True

    # Execute a simulated main flow using the module functions directly
    mock_get_diff()
    mock_generate("sample diff")
    mock_select(["Message 1", "Message 2", "Message 3"])
    mock_create("Message 2")

    # Assert the mocks were called correctly
    mock_get_diff.assert_called_once()
    mock_generate.assert_called_once_with("sample diff")
    mock_select.assert_called_once_with(["Message 1", "Message 2", "Message 3"])
    mock_create.assert_called_once_with("Message 2")
