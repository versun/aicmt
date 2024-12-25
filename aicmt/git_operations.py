from contextlib import contextmanager
from typing import List, NamedTuple, Optional, Tuple, Union, Any
import git
from git import Repo
from pathlib import Path
from enum import Enum
from .cli_interface import CLIInterface


class Change(NamedTuple):
    """Represents a change in a Git repository

    Attributes:
        file: Path to the changed file
        status: Current status of the file ('modified', 'deleted', 'new file', etc.)
        diff: Actual changes or special messages ('[File deleted]', 'BINARY_MESSAGE')
        insertions: Number of inserted lines
        deletions: Number of deleted lines
    """

    file: str
    status: str
    diff: str
    insertions: int
    deletions: int


class FileStatus(str, Enum):
    """Enum representing possible file statuses"""

    MODIFIED = "modified"
    DELETED = "deleted"
    NEW_FILE = "new file"
    NEW_BINARY = "new file (binary)"
    ERROR = "error"


# Constants
BINARY_MESSAGE = "[Binary file]"
DELETED_MESSAGE = "[File deleted]"
DEFAULT_REMOTE = "origin"
MAX_BINARY_CHECK_SIZE = 1024 * 1024  # 1MB


@contextmanager
def safe_file_operation(file_path: Union[str, Path]) -> Any:
    """Context manager for safe file operations with proper error handling"""
    try:
        yield
    except UnicodeDecodeError:
        return FileStatus.NEW_BINARY, BINARY_MESSAGE
        # yield (FileStatus.NEW_BINARY, BINARY_MESSAGE)
    except IOError as e:
        CLIInterface.display_error(f"Error reading file {file_path}: {str(e)}")
        raise


class GitOperations:
    def __init__(self, repo_path: str = "."):
        """Initialize GitOperations with a repository path

        Args:
            repo_path: Path to the git repository

        Raises:
            git.InvalidGitRepositoryError: If the path is not a valid git repository
            git.NoSuchPathError: If the path does not exist
        """
        try:
            self.repo = Repo(repo_path)
            self.git = self.repo.git
        except git.InvalidGitRepositoryError:
            raise git.InvalidGitRepositoryError("Not a valid Git repository")
        except git.NoSuchPathError:
            raise git.NoSuchPathError(f"Path '{repo_path}' does not exist")

    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if a file is binary

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if the file is binary, False otherwise
        """
        if not file_path.exists():
            return False
        try:
            with file_path.open("rb") as f:
                chunk = f.read(MAX_BINARY_CHECK_SIZE)
                return b"\0" in chunk or not chunk.decode("utf-8", errors="ignore")

        except IOError:
            return False

    def _get_file_content(self, file_path: Path) -> Tuple[str, str]:
        """Get file content with proper status

        Args:
            file_path: Path to the file

        Returns:
            Tuple[str, str]: (status, content)
        """
        with safe_file_operation(file_path):
            if self._is_binary_file(file_path):
                return FileStatus.NEW_BINARY, BINARY_MESSAGE

            return FileStatus.NEW_FILE, file_path.read_text(encoding="utf-8")

    def get_unstaged_changes(self) -> List[Change]:
        """Get all unstaged changes in the repository

        Returns:
            List[Change]: List of changes in the repository
            - status can be one of:
                "modified", "deleted", "new file", "new file (binary)", "error"
            - diff contains the actual changes or special messages:
                DELETED_MESSAGE, BINARY_MESSAGE

        Raises:
            IOError: If there is an error reading a file
            git.GitCommandError: If there is an error executing a git command
        """
        changes: List[Change] = []

        # Handle modified and deleted files
        for item in self.repo.index.diff(None):
            try:
                path_obj = Path(item.a_path)
                file_status, diff = self._handle_modified_file(item.a_path, path_obj)
                insertions, deletions = (0, 0) if diff.startswith("[") else self._calculate_diff_stats(diff)
                changes.append(Change(file=item.a_path, status=file_status, diff=diff, insertions=insertions, deletions=deletions))
            except Exception as e:
                CLIInterface.display_warning(f"Warning: Could not process {item.a_path}: {str(e)}")

        # Handle untracked files separately
        for file_path in self.repo.untracked_files:
            try:
                path_obj = Path(file_path)
                file_status, diff = self._handle_untracked_file(file_path, path_obj)
                insertions = len(diff.splitlines()) if not diff.startswith("[") else 0
                changes.append(Change(file=file_path, status=file_status, diff=diff, insertions=insertions, deletions=0))
            except Exception as e:
                CLIInterface.display_warning(f"Warning: Could not process {file_path}: {str(e)}")

        return changes

    def get_staged_changes(self) -> List[Change]:
        """Get all staged changes in the repository

        Returns:
            List[Change]: List of changes in the repository
            - status can be one of:
                "modified", "deleted", "new file", "new file (binary)", "error"
            - diff contains the actual changes or special messages:
                DELETED_MESSAGE, BINARY_MESSAGE
            - insertions and deletions contain the number of added/removed lines

        Raises:
            IOError: If there is an error reading a file
            git.GitCommandError: If there is an error executing a git command
        """
        changes = []
        diff_index = self.repo.index.diff(None, staged=True)

        for diff in diff_index:
            status = FileStatus.ERROR
            content = ""
            insertions = 0
            deletions = 0

            try:
                status, content, insertions, deletions = self._process_file_diff(diff)
            except Exception as e:
                status = FileStatus.ERROR
                content = f"[Unexpected error: {str(e)}]"

            changes.append(Change(file=diff.b_path or diff.a_path, status=status, diff=content, insertions=insertions, deletions=deletions))

        return changes

    def _process_file_diff(self, diff) -> Tuple:
        """
        Handles file differences in Git repositories.

        Args.
            diff: Git diff object containing information about file changes.

        Returns.
            tuple: (status, content, insertions, deletions)
            - status: File status (deleted/new file/modified, etc.)
            - content: file content or differences
            - insertions: number of lines inserted
            - deletions: number of lines deleted
        """
        if diff.renamed_file:
            try:
                content = f"Renamed from {diff.rename_from} to {diff.rename_to}"
                return FileStatus.MODIFIED, content, 0, 0
            except Exception as e:
                return FileStatus.ERROR, f"[Error processing rename: {str(e)}]", 0, 0

        if diff.deleted_file:
            try:
                return (FileStatus.DELETED, DELETED_MESSAGE, 0, len(diff.a_blob.data_stream.read().decode("utf-8").splitlines()))
            except Exception:
                return FileStatus.DELETED, DELETED_MESSAGE, 0, 0

        if diff.new_file:
            if diff.b_blob and diff.b_blob.mime_type != "text/plain":
                return FileStatus.NEW_BINARY, BINARY_MESSAGE, 0, 0

            file_path = Path(self.repo.working_dir) / diff.b_path
            with safe_file_operation(file_path):
                content = file_path.read_text(encoding="utf-8")
                return FileStatus.NEW_FILE, content, len(content.splitlines()), 0

        # Handle modified files
        try:
            # Check if the file is modified in the staging area
            staged_diff = self.repo.git.diff("--cached", diff.a_path)
            if staged_diff:
                content = staged_diff
            else:
                # If the file is not modified in the staging area, compare with the parent commit
                content = self.repo.git.diff("HEAD^", "HEAD", diff.a_path)

            insertions, deletions = self._calculate_diff_stats(content)
            return FileStatus.MODIFIED, content, insertions, deletions
        except git.GitCommandError as e:
            return FileStatus.ERROR, f"[Error getting diff: {str(e)}]", 0, 0

    def _calculate_diff_stats(self, diff_content: str) -> Tuple[int, int]:
        """Calculates the number of inserted and deleted lines in a diff content

        Args:
            diff_content: The diff content to analyze

        Returns:
            Tuple[int, int]: Number of insertions and deletions
        """
        insertions = deletions = 0
        for line in diff_content.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                insertions += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1
        return insertions, deletions

    def _handle_modified_file(self, file_path: str, file_path_obj: Path) -> Tuple[str, str]:
        """Handle modified file status and diff generation

        Args:
            file_path (str): Path to the file
            file_path_obj (Path): Path object for the file

        Returns:
            Tuple[str, str]: (status, diff)
        """
        try:
            # Try to get diff first
            diff = self.git.diff(file_path)
            return FileStatus.MODIFIED, diff
        except git.exc.GitCommandError:
            # If file doesn't exist, treat it as deleted
            if not file_path_obj.exists():
                return FileStatus.DELETED, DELETED_MESSAGE
            # If file exists but diff failed, something else is wrong
            raise IOError(f"Failed to get diff for {file_path}")

    def _handle_untracked_file(self, file_path: str, file_path_obj: Path) -> Tuple[str, str]:
        """Handle untracked file status and content reading

        Args:
            file_path (str): Path to the file
            file_path_obj (Path): Path object for the file

        Returns:
            Tuple[str, str]: (status, content)
        """
        if not file_path_obj.is_file():
            return FileStatus.DELETED, DELETED_MESSAGE

        try:
            # Check if file is binary
            with open(file_path, "rb") as f:
                content = f.read(1024 * 1024)  # Read first MB to check for binary content
                if b"\0" in content:
                    return FileStatus.NEW_BINARY, BINARY_MESSAGE

            # File is not binary, try to read as text
            with open(file_path, "r", encoding="utf-8") as f:
                return FileStatus.NEW_FILE, f.read()
        except UnicodeDecodeError:
            return FileStatus.NEW_BINARY, BINARY_MESSAGE

    def stage_files(self, files: List[str]) -> None:
        """Stage specified files

        Args:
            files: List of files to stage

        Raises:
            git.GitCommandError: If there is an error staging the files
        """
        if not files:
            raise ValueError("No files to stage!")

        try:
            # Get current status of files
            status = self.repo.git.status("--porcelain").splitlines()

            for file in files:
                # Find status for this file
                file_status = next((s for s in status if s.split()[-1] == file), None)
                if file_status and file_status.startswith(" D"):
                    # File is deleted, use remove
                    self.repo.index.remove([file])
                else:
                    # File is modified or new, use add
                    self.repo.index.add([file])
        except git.GitCommandError as e:
            raise git.GitCommandError(f"Failed to stage files: {str(e)}", e.status, e.stderr) from e

    def commit_changes(self, message: str) -> None:
        """Create a commit with the staged changes

        Args:
            message: Commit message

        Raises:
            git.GitCommandError: If there is an error creating the commit
        """
        try:
            self.repo.index.commit(message)
        except git.GitCommandError as e:
            raise git.GitCommandError(f"Failed to commit changes: {str(e)}", e.status, e.stderr)

    def push_changes(self, remote: str = DEFAULT_REMOTE, branch: Optional[str] = None) -> None:
        """Push commits to remote repository

        Args:
            remote: Name of the remote repository (default: "origin")
            branch: Name of the branch to push (default: current branch)

        Raises:
            git.GitCommandError: If there is an error pushing the changes
        """
        try:
            if branch is None:
                branch = self.get_current_branch()
            origin = self.repo.remote(remote)
            origin.push(branch)
        except git.GitCommandError as e:
            raise git.GitCommandError(f"Failed to push changes: {str(e)}", e.status, e.stderr)

    def get_current_branch(self) -> str:
        """Get the name of the current branch

        Returns:
            str: Name of the current branch

        Raises:
            git.GitCommandError: If there is an error getting the current branch
        """
        try:
            return self.repo.active_branch.name
        except git.GitCommandError as e:
            raise git.GitCommandError(f"Failed to get current branch: {str(e)}", e.status, e.stderr)

    def checkout_branch(self, branch_name: str, create: bool = False) -> None:
        """Checkout a branch

        Args:
            branch_name: Name of the branch to checkout
            create: Create the branch if it doesn't exist

        Raises:
            git.GitCommandError: If there is an error checking out the branch
        """
        try:
            if create and branch_name not in self.repo.heads:
                self.repo.create_head(branch_name)
            self.repo.git.checkout(branch_name)
        except git.GitCommandError as e:
            raise git.GitCommandError(f"Failed to checkout branch: {str(e)}", e.status, e.stderr)

    def get_commit_changes(self, commit_hash: str) -> List[Change]:
        """Get changes from a specific commit

        Args:
            commit_hash: Hash of the commit to analyze

        Returns:
            List[Change]: List of changes in the commit

        Raises:
            git.GitCommandError: If there is an error getting the commit changes
        """
        try:
            commit = self.repo.commit(commit_hash)
            parent = commit.parents[0] if commit.parents else self.repo.tree("4b825dc642cb6eb9a060e54bf8d69288fbee4904")

            changes = []
            diff_index = parent.diff(commit)

            for diff in diff_index:
                status = FileStatus.ERROR
                content = ""
                insertions = 0
                deletions = 0
                try:
                    status, content, insertions, deletions = self._process_file_diff(diff)
                except Exception as e:
                    status = FileStatus.ERROR
                    content = f"[Unexpected error: {str(e)}]"

                changes.append(Change(file=diff.b_path or diff.a_path, status=status, diff=content, insertions=insertions, deletions=deletions))

            return changes
        except git.GitCommandError as e:
            raise git.GitCommandError(f"Failed to get commit changes: {str(e)}", e.status, e.stderr)
