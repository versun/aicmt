import os
import pytest
from git import Repo, InvalidGitRepositoryError, GitCommandError, NoSuchPathError
from gitdb.exc import BadName
from aicmt.git_operations import GitOperations
from pathlib import Path


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
        # Create a new file
        with open("test.txt", "w") as f:
            f.write("test content")

        changes = git_ops.get_unstaged_changes()
        assert len(changes) == 1
        assert changes[0].file == "test.txt"
        assert changes[0].status == "new file"
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
        assert any("stage_test.txt" in str(entry)
                   for entry in git_ops.repo.index.entries.keys())
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


def test_get_commit_history(temp_git_repo):
    """Test getting commit history"""
    git_ops = GitOperations(temp_git_repo)

    # Switch to the repository directory
    current_dir = os.getcwd()
    os.chdir(temp_git_repo)

    try:
        # Create multiple commits
        for i in range(3):
            with open(f"history_test_{i}.txt", "w") as f:
                f.write(f"test content {i}")
            git_ops.stage_files([f"history_test_{i}.txt"])
            git_ops.commit_changes(f"Test commit {i}")

        history = git_ops.get_commit_history(
            max_count=4)  # Modified to 4 to get all commits
        assert len(history) == 4  # 3 new commits + 1 initial commit
    finally:
        # Restore the original directory
        os.chdir(current_dir)


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
        assert "[Binary file]" in changes[0].diff
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
        assert changes[0].diff == "[Binary file]"
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
        assert change.diff == "[File deleted]"
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
    assert content == "[File deleted]"


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

    # Switch to the repository directory
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

        git_ops.repo.index.add(
            ["test1.txt", "test2.txt", "test3.bin", "test4.txt"])
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
        test1_change = next(change for change in changes
                            if change.file == "test1.txt")
        test2_change = next(change for change in changes
                            if change.file == "test2.txt")
        test3_change = next(change for change in changes
                            if change.file == "test3.bin")
        test5_change = next(change for change in changes
                            if change.file == "test5.txt")

        # Test modified text file
        assert test1_change.status == "modified"
        assert "modified content" in test1_change.diff
        assert test1_change.insertions > 0
        assert test1_change.deletions > 0

        # Test deleted file
        assert test2_change.status == "deleted"
        assert "[File deleted]" in test2_change.diff
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

    finally:
        # Restore the original directory
        os.chdir(current_dir)
