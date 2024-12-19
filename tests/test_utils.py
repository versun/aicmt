import os
import tempfile
from aicmt.utils import chunk_files, format_diff, confirm_action
from unittest.mock import patch


def test_chunk_files():
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test files
        files = []
        for i in range(3):
            file_path = os.path.join(temp_dir, f"test{i}.txt")
            with open(file_path, "w") as f:
                f.write("x" * (400 if i < 2 else 800))
            files.append(file_path)

        # Test chunking
        chunks = chunk_files(files, max_size=1000)
        assert len(chunks) == 2
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 1


def test_format_diff():
    # Test diff formatting
    diff_text = """diff --git a/test.py b/test.py
index 1234567..89abcdef 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
+import os
 def test_func():
-    return None
+    return True
"""
    formatted = format_diff(diff_text)

    # Check if the formatting is correct
    assert "┌" in formatted
    assert "└" in formatted
    assert "[bold blue]" in formatted
    assert "import os" in formatted


@patch("rich.prompt.Confirm.ask")
def test_confirm_action(mock_ask):
    # Test confirm action
    mock_ask.return_value = True
    assert confirm_action("Test message") is True

    mock_ask.return_value = False
    assert confirm_action("Test message") is False


def test_format_diff_special_cases():
    # Test special cases
    diff_text = """diff --git a/new_file.py b/new_file.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,2 @@
+def new_function():
+    pass"""

    formatted = format_diff(diff_text)
    assert "[bold yellow]│[/bold yellow]" in formatted
    assert "new file mode" in formatted

    diff_text_deleted = """diff --git a/deleted_file.py b/deleted_file.py
deleted file mode 100644
index 1234567..0000000
--- a/deleted_file.py
+++ /dev/null"""

    formatted = format_diff(diff_text_deleted)
    assert "[bold yellow]│[/bold yellow]" in formatted
    assert "deleted file mode" in formatted


def test_format_diff_hunk_header():
    # Test hunk header
    diff_text = """diff --git a/test.py b/test.py
index 1234567..89abcdef 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
+import os"""

    formatted = format_diff(diff_text)
    assert "[magenta]├" in formatted
    assert "@@ -1,3 +1,4 @@" in formatted


def test_format_diff_keyword_highlighting():
    # Test keyword highlighting
    diff_text = """diff --git a/test.py b/test.py
index 1234567..89abcdef 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
-def old_function():
+def new_function():
-    import os
+    from datetime import datetime
-class OldClass:
+class NewClass:"""

    formatted = format_diff(diff_text)
    assert "[bright_red]│ - def old_function()" in formatted
    assert "[bright_green]│ + def new_function()" in formatted
    assert "[bright_red]│ - class OldClass:" in formatted
    assert "[bright_green]│ + class NewClass:" in formatted


def test_format_diff_border_style():
    # Test border style
    diff_text = """diff --git a/test1.py b/test1.py
index 1234567..89abcdef 100644
--- a/test1.py
+++ b/test1.py
@@ -1,1 +1,1 @@
-old
+new
diff --git a/test2.py b/test2.py
index 2234567..99abcdef 100644
--- a/test2.py
+++ b/test2.py"""

    formatted = format_diff(diff_text)

    assert f"[bold blue]┌{'─' * 50}[/bold blue]" in formatted

    assert f"└{'─' * 50}" in formatted

    assert formatted.count(f"[bold blue]┌{'─' * 50}[/bold blue]") == 2
