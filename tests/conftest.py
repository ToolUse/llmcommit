"""Pytest configuration for Blueprint tests."""

import pytest


@pytest.fixture
def sample_git_diff():
    """Return a sample git diff for testing."""
    return """diff --git a/src/blueprint/commit_generator.py b/src/blueprint/commit_generator.py
index 123456..789abc 100644
--- a/src/blueprint/commit_generator.py
+++ b/src/blueprint/commit_generator.py
@@ -10,7 +10,7 @@ def get_git_diff(max_chars: int = 5000) -> str:
     \"\"\"Get the git diff of staged changes, or unstaged if no staged changes.\"\"\"
     try:
         diff = subprocess.check_output(["git", "diff", "--cached"], text=True)
-        if not diff.strip():
+        if not diff:
             diff = subprocess.check_output(["git", "diff"], text=True)
         return diff[:max_chars]  # Limit to max_chars characters
     except subprocess.CalledProcessError:
@@ -50,7 +50,7 @@ def parse_commit_messages(response: str) -> List[str]:
     messages = []
     for line in response.split("\\n"):
         if line.strip().startswith(("1.", "2.", "3.")):
-            messages.append(line.split(".", 1)[1])
+            messages.append(line.split(".", 1)[1].strip())
     return messages"""


@pytest.fixture
def sample_ai_response():
    """Return a sample AI response for testing."""
    return """Here are three commit message options for your changes:

1. Remove strip() from diff check and add strip() to parsed commit messages
2. Fix string handling in git diff and commit message parsing
3. Improve robustness of git diff checking and commit message parsing

These commit messages reflect the changes where you removed a strip() call in the git diff check and added one in the commit message parser."""
