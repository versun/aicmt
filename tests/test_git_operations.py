import os
import pytest
from git import Repo, InvalidGitRepositoryError
from aicmt.git_operations import GitOperations


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
