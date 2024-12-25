import os
import pytest
from git import Repo, InvalidGitRepositoryError, GitCommandError, NoSuchPathError
from gitdb.exc import BadName
from aicmt.git_operations import GitOperations, BINARY_MESSAGE, DELETED_MESSAGE, safe_file_operation, FileStatus
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary Git repository for testing"""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    repo = Repo.init(repo_path)

    # Create an initial commit
    (repo_path / "README.md").write_text("# Test Repo")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    return str(repo_path)


def test_init_valid_repo(temp_git_repo):
    """Test initialization of a valid repository"""
    git_ops = GitOperations(temp_git_repo)
    assert isinstance(git_ops.repo, Repo)


def test_init_invalid_repo(tmp_path):
    """Test initialization of an invalid repository"""
    with pytest.raises(InvalidGitRepositoryError):
        GitOperations(str(tmp_path))


def test_init_nonexistent_path(tmp_path):
    """Test initialization with a nonexistent path"""
    nonexistent_path = str(tmp_path / "nonexistent")
    with pytest.raises(NoSuchPathError) as excinfo:
        GitOperations(nonexistent_path)
    assert str(excinfo.value) == f"Path '{nonexistent_path}' does not exist"


def test_get_unstaged_changes(temp_git_repo):
    """Test getting unstaged changes"""
    git_ops = GitOperations(temp_git_repo)

    # Switch to the repository directory
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Create a new file and add it to git
        with open("test.txt", "w") as f:
            f.write("test content")

        # Add file to git and modify it
        git_ops.repo.index.add(["test.txt"])
        git_ops.repo.index.commit("Initial commit")

        with open("test.txt", "w") as f:
            f.write("modified content")

        changes = git_ops.get_unstaged_changes()
        assert len(changes) == 1
        assert changes[0].file == "test.txt"
        assert changes[0].status == "modified"

        # Test exception handling
        def mock_handle_modified_file(*args):
            raise Exception("Test error")

        # Patch the _handle_modified_file method to raise an exception
        with patch.object(GitOperations, "_handle_modified_file", side_effect=mock_handle_modified_file):
            with patch("aicmt.cli_interface.CLIInterface.display_warning") as mock_warning:
                changes = git_ops.get_unstaged_changes()
                mock_warning.assert_called_once_with("Warning: Could not process test.txt: Test error")

    finally:
        # Restore the original directory
        os.chdir(current_dir)


def test_stage_files(temp_git_repo):
    """Test staging files"""
    git_ops = GitOperations(temp_git_repo)

    # Switch to the repository directory
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Create a new file
        with open("stage_test.txt", "w") as f:
            f.write("test content")

        # Stage the file
        git_ops.stage_files(["stage_test.txt"])

        # Get the list of files in the staging area
        # staged_files = [
        #     item.a_path
        #     for item in git_ops.repo.index.diff(git_ops.repo.head.commit)
        # ]
        untracked = git_ops.repo.untracked_files

        # Verify that the file is correctly staged
        assert "stage_test.txt" not in untracked
        # Directly check if the file name is in the index
        assert any("stage_test.txt" in str(entry) for entry in git_ops.repo.index.entries.keys())

        with pytest.raises(ValueError) as excinfo:
            git_ops.stage_files([])
        assert str(excinfo.value) == "No files to stage!"

    finally:
        # Restore the original directory
        os.chdir(current_dir)


def test_commit_changes(temp_git_repo):
    """Test committing changes"""
    git_ops = GitOperations(temp_git_repo)

    # Switch to the repository directory
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Create and stage a new file
        with open("commit_test.txt", "w") as f:
            f.write("test content")
        git_ops.stage_files(["commit_test.txt"])

        git_ops.commit_changes("Test commit")
        latest_commit = next(git_ops.repo.iter_commits())
        assert "Test commit" == latest_commit.message
    finally:
        # Restore the original directory
        os.chdir(current_dir)


def test_get_current_branch(temp_git_repo):
    """Test getting current branch name"""
    git_ops = GitOperations(temp_git_repo)
    assert git_ops.get_current_branch() in ["master", "main"]


def test_checkout_branch(temp_git_repo):
    """Test checking out branch"""
    git_ops = GitOperations(temp_git_repo)

    # Create and switch to a new branch
    git_ops.checkout_branch("test-branch", create=True)
    assert git_ops.get_current_branch() == "test-branch"


def test_deleted_file_changes(temp_git_repo):
    """Test handling of deleted files"""
    git_ops = GitOperations(temp_git_repo)
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Create and commit a file first
        with open("to_delete.txt", "w") as f:
            f.write("file to be deleted")
        git_ops.stage_files(["to_delete.txt"])
        git_ops.commit_changes("Add file to delete")

        # Delete the file
        os.remove("to_delete.txt")

        changes = git_ops.get_unstaged_changes()
        assert len(changes) == 1
        assert changes[0].file == "to_delete.txt"
        assert changes[0].status == "deleted"
    finally:
        os.chdir(current_dir)


def test_binary_file_changes(temp_git_repo):
    """Test handling of binary files"""
    git_ops = GitOperations(temp_git_repo)
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Create a binary file
        with open("binary_file.bin", "wb") as f:
            f.write(bytes([0x00, 0x01, 0x02, 0x03]))

        changes = git_ops.get_unstaged_changes()
        assert len(changes) == 1
        assert changes[0].file == "binary_file.bin"
        assert changes[0].status == "new file (binary)"
        assert BINARY_MESSAGE in changes[0].diff
    finally:
        os.chdir(current_dir)


def test_modified_file_changes(temp_git_repo):
    """Test handling of modified files"""
    git_ops = GitOperations(temp_git_repo)
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Create and commit a file
        with open("modify_me.txt", "w") as f:
            f.write("original content")
        git_ops.stage_files(["modify_me.txt"])
        git_ops.commit_changes("Add file to modify")

        # Modify the file
        with open("modify_me.txt", "w") as f:
            f.write("modified content")

        changes = git_ops.get_unstaged_changes()
        assert len(changes) == 1
        assert changes[0].file == "modify_me.txt"
        assert changes[0].status == "modified"
        assert "+modified content" in changes[0].diff
        assert "-original content" in changes[0].diff
    finally:
        os.chdir(current_dir)


def test_binary_file_decode_error(temp_git_repo):
    """Test handling of binary files that cause UnicodeDecodeError"""
    git_ops = GitOperations(temp_git_repo)
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Create a binary file that will cause UnicodeDecodeError
        with open("test.bin", "wb") as f:
            f.write(bytes([0xFF, 0xFE, 0xFD] * 100))  # Invalid UTF-8 bytes

        changes = git_ops.get_unstaged_changes()
        assert len(changes) == 1
        assert changes[0].file == "test.bin"
        assert changes[0].status == "new file (binary)"
        assert changes[0].diff == BINARY_MESSAGE
    finally:
        os.chdir(current_dir)


def test_file_not_found_error(temp_git_repo):
    """Test handling of files that don't exist during diff generation"""
    git_ops = GitOperations(temp_git_repo)
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Create a file first
        file_path = "temp.txt"
        with open(file_path, "w") as f:
            f.write("test content")

        # Add the file to git's index
        git_ops.repo.index.add([file_path])

        # Now delete the file
        os.remove(file_path)

        # Get changes after file deletion
        changes = git_ops.get_unstaged_changes()
        matching_changes = [c for c in changes if c.file == file_path]
        assert len(matching_changes) == 1
        change = matching_changes[0]
        assert change.status == "deleted"
        assert change.diff == DELETED_MESSAGE
    finally:
        os.chdir(current_dir)


def test_error_handling(temp_git_repo):
    """Test error handling scenarios"""
    git_ops = GitOperations(temp_git_repo)
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Test staging non-existent file
        with pytest.raises(FileNotFoundError):
            git_ops.stage_files(["non_existent.txt"])

        # Test push to non-existent remote
        with pytest.raises(ValueError):
            git_ops.push_changes("non-existent-remote")

        # Add a remote that points to a non-existent repository
        git_ops.repo.create_remote("test-remote", "file:///non-existent-repo")
        with pytest.raises(GitCommandError):
            git_ops.push_changes("test-remote")

        # Test checkout non-existent branch without create flag
        with pytest.raises(GitCommandError):
            git_ops.checkout_branch("non-existent-branch", create=False)
    finally:
        os.chdir(current_dir)


def test_handle_modified_file_diff_error(temp_git_repo):
    """Test IOError handling when git diff fails for a modified file"""
    git_ops = GitOperations(temp_git_repo)
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Create and commit a test file
        test_file = "test_diff_error.txt"
        with open(test_file, "w") as f:
            f.write("initial content")
        git_ops.stage_files([test_file])
        git_ops.commit_changes("Add test file")

        # Modify the file
        with open(test_file, "w") as f:
            f.write("modified content")

        # Create a Mock object for Git
        class MockGit:
            def diff(self, *args, **kwargs):
                raise GitCommandError("git diff", 128)

        # Replace the git object with our mock
        git_ops.git = MockGit()

        # Test that IOError is raised when trying to get diff
        with pytest.raises(IOError) as excinfo:
            git_ops._handle_modified_file(test_file, Path(test_file))

        assert str(excinfo.value) == f"Failed to get diff for {test_file}"

    finally:
        os.chdir(current_dir)


def test_handle_untracked_file_deleted(temp_git_repo):
    """Test _handle_untracked_file method when the file is deleted"""
    git_ops = GitOperations(temp_git_repo)

    # Create a non-existent file path
    file_path = os.path.join(temp_git_repo, "non_existent_file.txt")
    file_path_obj = Path(file_path)

    # Test the _handle_untracked_file method
    status, content = git_ops._handle_untracked_file(file_path, file_path_obj)

    # Assert the results
    assert status == "deleted"
    assert content == DELETED_MESSAGE


def test_stage_deleted_file(temp_git_repo):
    """Test staging a deleted file"""
    git_ops = GitOperations(temp_git_repo)

    # Switch to the repository directory
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Create and commit a new file first
        test_file = "to_be_deleted.txt"
        with open(test_file, "w") as f:
            f.write("this file will be deleted")

        # Add and commit the file
        git_ops.repo.index.add([test_file])
        git_ops.repo.index.commit("Add file that will be deleted")

        # Delete the file
        os.remove(test_file)

        # Stage the deleted file
        git_ops.stage_files([test_file])

        # Verify that the file is marked as deleted in the index
        diff = git_ops.repo.head.commit.diff()
        deleted_files = [d.a_path for d in diff if d.change_type == "D"]
        assert test_file in deleted_files

    finally:
        # Restore the original directory
        os.chdir(current_dir)


def test_get_commit_changes(temp_git_repo):
    """Test getting changes from a specific commit"""
    git_ops = GitOperations(temp_git_repo)
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)
    try:
        # Create and commit initial files
        with open("test1.txt", "w") as f:
            f.write("initial content")
        with open("test2.txt", "w") as f:
            f.write("file to be deleted")
        with open("test3.bin", "wb") as f:
            f.write(b"\x00\x01\x02\x03")  # Binary content
        with open("test4.txt", "w") as f:
            pass  # Empty file

        git_ops.repo.index.add(["test1.txt", "test2.txt", "test3.bin", "test4.txt"])
        git_ops.repo.index.commit("Initial commit")

        # Make various changes
        # 1. Modify test1.txt
        with open("test1.txt", "w") as f:
            f.write("modified content")

        # 2. Delete test2.txt
        os.remove("test2.txt")

        # 3. Modify binary file
        with open("test3.bin", "wb") as f:
            f.write(b"\x03\x02\x01\x00")

        # 4. Create new empty file
        with open("test5.txt", "w") as f:
            pass

        git_ops.repo.index.add(["test1.txt", "test3.bin", "test5.txt"])
        git_ops.repo.index.remove(["test2.txt"])
        second_commit = git_ops.repo.index.commit("Various changes")

        # Get changes from the second commit
        changes = git_ops.get_commit_changes(second_commit.hexsha)

        # Verify number of changes
        assert len(changes) == 4

        # Find changes by filename
        test1_change = next(change for change in changes if change.file == "test1.txt")
        test2_change = next(change for change in changes if change.file == "test2.txt")
        test3_change = next(change for change in changes if change.file == "test3.bin")
        test5_change = next(change for change in changes if change.file == "test5.txt")

        # Test modified text file
        assert test1_change.status == "modified"
        assert "modified content" in test1_change.diff
        assert test1_change.insertions > 0
        assert test1_change.deletions > 0

        # Test deleted file
        assert test2_change.status == "deleted"
        assert DELETED_MESSAGE in test2_change.diff
        assert test2_change.insertions == 0
        assert test2_change.deletions > 0

        # Test binary file
        assert test3_change.status == "modified"
        assert test3_change.insertions >= 0
        assert test3_change.deletions >= 0

        # Test new empty file
        assert test5_change.status == "new file"
        assert test5_change.insertions == 0
        assert test5_change.deletions == 0

        # Test invalid commit hash
        with pytest.raises(BadName):
            git_ops.get_commit_changes("invalid_hash")

        # Test large file changes
        with open("large_file.txt", "w") as f:
            f.write("x" * 1024 * 1024)  # 1MB of data
        git_ops.repo.index.add(["large_file.txt"])
        large_file_commit = git_ops.repo.index.commit("Add large file")
        large_file_changes = git_ops.get_commit_changes(large_file_commit.hexsha)
        large_file_change = next(change for change in large_file_changes if change.file == "large_file.txt")
        assert large_file_change.status == "new file"
        assert large_file_change.insertions > 0
        assert large_file_change.deletions == 0

        # Test file permission changes
        os.chmod("test1.txt", 0o755)  # Make file executable
        git_ops.repo.index.add(["test1.txt"])
        permission_commit = git_ops.repo.index.commit("Change file permissions")
        permission_changes = git_ops.get_commit_changes(permission_commit.hexsha)
        permission_change = next(change for change in permission_changes if change.file == "test1.txt")
        assert permission_change.status == "modified"

        # Test file rename
        git_ops.repo.git.mv("test4.txt", "test4_renamed.txt")
        rename_commit = git_ops.repo.index.commit("Rename file")
        rename_changes = git_ops.get_commit_changes(rename_commit.hexsha)
        assert len(rename_changes) == 1  # Git treats rename as a single change
        rename_change = rename_changes[0]
        assert rename_change.status == FileStatus.MODIFIED
        assert rename_change.file == "test4_renamed.txt"
        assert "Renamed from test4.txt to test4_renamed.txt" in rename_change.diff

        # Test commit with special characters
        with open("special_file.txt", "w") as f:
            f.write("special content")
        git_ops.repo.index.add(["special_file.txt"])
        special_commit = git_ops.repo.index.commit("Test 🚀 Special Characters! #$%^&*()")
        special_changes = git_ops.get_commit_changes(special_commit.hexsha)
        special_change = next(change for change in special_changes if change.file == "special_file.txt")
        assert special_change.status == "new file"
    finally:
        # Restore the original directory
        os.chdir(current_dir)


def test_get_staged_changes(temp_git_repo):
    """Test getting staged changes"""
    git_ops = GitOperations(temp_git_repo)
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)
    try:
        # Test new text file
        with open("new_file.txt", "w") as f:
            f.write("new content")
        git_ops.stage_files(["new_file.txt"])

        # Test new binary file
        with open("new_binary.bin", "wb") as f:
            f.write(bytes([0x00, 0x01, 0x02, 0x03]))
        git_ops.stage_files(["new_binary.bin"])

        # Test modified file
        with open("modify.txt", "w") as f:
            f.write("initial")
        git_ops.stage_files(["modify.txt"])

        # Get and verify staged changes
        first_changes = git_ops.get_staged_changes()
        assert len(first_changes) == 3

        git_ops.commit_changes("Add file to modify")

        with open("modify.txt", "w") as f:
            f.write("modified")
        git_ops.stage_files(["modify.txt"])

        # Test deleted file
        with open("delete.txt", "w") as f:
            f.write("to be deleted")
        git_ops.stage_files(["delete.txt"])

        second_changes = git_ops.get_staged_changes()
        assert len(second_changes) == 2

        git_ops.commit_changes("Add file to delete")

        os.remove("delete.txt")
        git_ops.stage_files(["delete.txt"])
        third_changes = git_ops.get_staged_changes()

        # Verify new text file
        new_file = next(c for c in first_changes if c.file == "new_file.txt")
        assert new_file.status == "new file"
        assert "new content" in new_file.diff
        assert new_file.insertions == 1
        assert new_file.deletions == 0

        # Verify new binary file
        binary_file = next(c for c in first_changes if c.file == "new_binary.bin")
        assert binary_file.status == "new file (binary)"
        assert binary_file.diff == BINARY_MESSAGE

        # Verify modified file
        modified_file = next(c for c in second_changes if c.file == "modify.txt")
        assert modified_file.status == "modified"
        assert "-initial" in modified_file.diff
        assert "+modified" in modified_file.diff
        assert modified_file.insertions == 1
        assert modified_file.deletions == 1

        # Verify deleted file
        deleted_file = next(c for c in third_changes if c.file == "delete.txt")
        assert deleted_file.status == "deleted"
        assert deleted_file.diff == DELETED_MESSAGE
        assert deleted_file.insertions == 0
        assert deleted_file.deletions > 0

    finally:
        os.chdir(current_dir)


def test_file_reading(temp_git_repo):
    """Test file reading"""
    git_ops = GitOperations(temp_git_repo)
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)
    try:
        # Test new text file
        with open("new_file.txt", "w") as f:
            f.write("new content")
        git_ops.stage_files(["new_file.txt"])

        # Test new binary file
        with open("new_binary.bin", "wb") as f:
            f.write(bytes([0x00, 0x01, 0x02, 0x03]))
        git_ops.stage_files(["new_binary.bin"])

        # Test modified file
        with open("modify.txt", "w") as f:
            f.write("initial")
        git_ops.stage_files(["modify.txt"])

        # Remove the file
        os.remove("new_file.txt")

        changes = git_ops.get_staged_changes()
        # Test that IOError is raised when trying to get diff
        new_file = next(c for c in changes if c.file == "new_file.txt")
        assert new_file.status == "error"
        assert "No such file" in new_file.diff

        git_ops.commit_changes("Add file to modify")

    finally:
        os.chdir(current_dir)


def test_safe_file_operation(temp_git_repo):
    """Test the safe_file_operation context manager"""
    test_file = Path(temp_git_repo) / "test.txt"

    # Test normal operation
    with safe_file_operation(test_file):
        with open(test_file, "w") as f:
            f.write("test content")

    assert test_file.exists()
    assert test_file.read_text() == "test content"

    # Test UnicodeDecodeError handling
    binary_file = Path(temp_git_repo) / "binary.bin"
    binary_file.write_bytes(b"\x80\x81")

    with safe_file_operation(binary_file) as result:
        with open(binary_file, "r") as f:
            f.read()
        assert result == (FileStatus.NEW_BINARY, BINARY_MESSAGE)

    # Test IOError handling
    non_existent_file = Path(temp_git_repo) / "non_existent.txt"
    with pytest.raises(IOError):
        with safe_file_operation(non_existent_file):
            with open(non_existent_file, "r") as f:
                f.read()


def test_is_binary_file(temp_git_repo):
    """Test the _is_binary_file method"""
    git_ops = GitOperations(temp_git_repo)
    repo_path = Path(temp_git_repo)

    # Test text file
    text_file = repo_path / "test.txt"
    text_file.write_text("Hello, World!")
    assert not git_ops._is_binary_file(text_file)

    # Test binary file
    binary_file = repo_path / "test.bin"
    with binary_file.open("wb") as f:
        f.write(b"\x00\x01\x02\x03")
    assert git_ops._is_binary_file(binary_file)

    # Test non-existent file
    non_existent = repo_path / "non_existent.txt"
    assert not git_ops._is_binary_file(non_existent)

    # Test file with read error (create a directory with same name)
    error_file = repo_path / "error_file"
    error_file.mkdir()
    assert not git_ops._is_binary_file(error_file)


def test_get_file_content(tmp_path):
    git_ops = GitOperations()

    # Test text file
    text_file = tmp_path / "test.txt"
    text_file.write_text("Hello, World!", encoding="utf-8")
    status, content = git_ops._get_file_content(text_file)
    assert status == FileStatus.NEW_FILE
    assert content == "Hello, World!"

    # Test binary file
    binary_file = tmp_path / "test.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03")
    status, content = git_ops._get_file_content(binary_file)
    assert status == FileStatus.NEW_BINARY
    assert content == BINARY_MESSAGE

    # Test non-existent file
    non_existent = tmp_path / "non_existent.txt"
    with pytest.raises(FileNotFoundError):
        git_ops._get_file_content(non_existent)


def test_file_processing_warning(temp_git_repo):
    """Test file processing warning"""
    git_ops = GitOperations(temp_git_repo)

    # Switch to the repository directory
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Create a new file and add it to git
        with open("test.txt", "w") as f:
            f.write("test content")

        # Add file to git and modify it
        git_ops.repo.index.add(["test.txt"])
        git_ops.repo.index.commit("Initial commit")

        with open("test.txt", "w") as f:
            f.write("modified content")

        # Test exception handling
        def mock_handle_modified_file(*args):
            raise Exception("Test error")

        # Patch the _handle_modified_file method to raise an exception
        with patch.object(GitOperations, "_handle_modified_file", side_effect=mock_handle_modified_file):
            with patch("aicmt.cli_interface.CLIInterface.display_warning") as mock_warning:
                git_ops.get_unstaged_changes()
                mock_warning.assert_called_once_with("Warning: Could not process test.txt: Test error")

    finally:
        # Restore the original directory
        os.chdir(current_dir)


def test_untracked_file_warning(temp_git_repo):
    """Test warning display for untracked file processing error"""
    git_ops = GitOperations(temp_git_repo)

    # Switch to the repository directory
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Create a new file
        with open("test.txt", "w") as f:
            f.write("test content")

        # Test exception handling
        def mock_handle_untracked_file(*args):
            raise Exception("Test error")

        # Patch the _handle_untracked_file method to raise an exception
        with patch.object(GitOperations, "_handle_untracked_file", side_effect=mock_handle_untracked_file):
            with patch("aicmt.cli_interface.CLIInterface.display_warning") as mock_warning:
                git_ops.get_unstaged_changes()
                mock_warning.assert_called_once_with("Warning: Could not process test.txt: Test error")

    finally:
        # Restore the original directory
        os.chdir(current_dir)


def test_process_file_diff_deleted_exception(temp_git_repo):
    """Test _process_file_diff method when file deletion raises an exception"""
    git_ops = GitOperations(temp_git_repo)

    # Create a mock diff object
    class MockDiff:
        def __init__(self):
            self.a_path = "nonexistent.txt"
            self.deleted_file = True
            self.renamed_file = False
            self.new_file = False
            self.a_blob = None

    # Test when an exception occurs during file deletion handling
    diff = MockDiff()
    status, content, insertions, deletions = git_ops._process_file_diff(diff)
    assert status == FileStatus.DELETED
    assert content == DELETED_MESSAGE
    assert insertions == 0
    assert deletions == 0


def test_process_file_diff_git_error(temp_git_repo):
    """Test _process_file_diff method when git command raises an error"""
    git_ops = GitOperations(temp_git_repo)

    # Create a mock diff object
    class MockDiff:
        def __init__(self):
            self.a_path = "test.txt"
            self.deleted_file = False
            self.new_file = False
            self.renamed_file = False

    # Create a mock git object
    mock_git = MagicMock()
    mock_git.diff.side_effect = GitCommandError("git diff", 128)

    # Test when git command raises an error
    with patch.object(git_ops.repo, "git", mock_git):
        status, content, insertions, deletions = git_ops._process_file_diff(MockDiff())
        assert status == FileStatus.ERROR
        assert "[Error getting diff: " in content
        assert insertions == 0
        assert deletions == 0
