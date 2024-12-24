import os
from typing import List, Dict, NamedTuple, Optional, Tuple
import git
from git import Repo
from rich.console import Console
from pathlib import Path

console = Console()


class Change(NamedTuple):
    """Represents a change in a Git repository"""

    file: str
    status: str
    diff: str
    insertions: int
    deletions: int


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
            raise git.InvalidGitRepositoryError(
                f"'{repo_path}' is not a valid Git repository")
        except git.NoSuchPathError:
            raise git.NoSuchPathError(f"Path '{repo_path}' does not exist")

    def get_unstaged_changes(self) -> List[Change]:
        """Get all unstaged changes in the repository

        Returns:
            List[Change]: List of changes in the repository
            - status can be one of:
                "modified", "deleted", "new file", "new file (binary)", "error"
            - diff contains the actual changes or special messages:
                "[File deleted]", "[Binary file]"

        Raises:
            IOError: If there is an error reading a file
            git.GitCommandError: If there is an error executing a git command
        """
        changes = []

        # Get modified files
        modified_files = {item.a_path for item in self.repo.index.diff(None)}

        # Get untracked files
        untracked_files = set(self.repo.untracked_files)

        for file_path in modified_files.union(untracked_files):
            try:
                file_path_obj = Path(file_path)
                status = ""
                diff = ""

                if file_path in modified_files:
                    status, diff = self._handle_modified_file(
                        file_path, file_path_obj)
                else:
                    status, diff = self._handle_untracked_file(
                        file_path, file_path_obj)

                if diff and not diff.startswith("["):
                    insertions, deletions = self._calculate_diff_stats(diff)
                else:
                    insertions = deletions = 0

                changes.append(
                    Change(
                        file=file_path,
                        status=status,
                        diff=diff,
                        insertions=insertions,
                        deletions=deletions,
                    ))
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not process {file_path}: {str(e)}[/yellow]"
                )

        return changes

    def get_staged_changes(self) -> List[Change]:
        """Get all staged changes in the repository

        Returns:
            List[Change]: List of changes in the repository
            - status can be one of:
                "modified", "deleted", "new file", "new file (binary)", "error"
            - diff contains the actual changes or special messages:
                "[File deleted]", "[Binary file]"
            - insertions and deletions contain the number of added/removed lines

        Raises:
            IOError: If there is an error reading a file
            git.GitCommandError: If there is an error executing a git command
        """
        changes = []
        diff_index = self.repo.index.diff(None, staged=True)

        for diff in diff_index:
            status = "error"
            content = ""
            insertions = 0
            deletions = 0

            try:
                status, content, insertions, deletions = self._process_file_diff(
                    diff)
            except Exception as e:
                status = "error"
                content = f"[Unexpected error: {str(e)}]"

            changes.append(
                Change(file=diff.b_path or diff.a_path,
                       status=status,
                       diff=content,
                       insertions=insertions,
                       deletions=deletions))

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
        status = ""
        content = ""
        insertions = 0
        deletions = 0

        if diff.deleted_file:
            status = "deleted"
            content = "[File deleted]"
            insertions, deletions = 0, len(
                diff.a_blob.data_stream.read().decode('utf-8').splitlines())
        elif diff.new_file:
            if diff.b_blob and diff.b_blob.mime_type != "text/plain":
                status = "new file (binary)"
                content = "[Binary file]"
            else:
                status = "new file"
                file_path = os.path.join(self.repo.working_dir, diff.b_path)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    insertions = len(content.splitlines())
                    deletions = 0
                except IOError as e:
                    content = f"[Error reading file: {str(e)}]"
        else:
            status = "modified"
            try:
                # Check if the file is modified in the staging area
                staged_diff = self.repo.git.diff("--cached", diff.a_path)
                if staged_diff:
                    content = staged_diff
                    #stats = self.repo.git.diff("--cached", "--numstat",diff.a_path).split()
                else:
                    # If the file is not modified in the staging area, compare with the parent commit
                    content = self.repo.git.diff("HEAD^", "HEAD", diff.a_path)
                    #stats = self.repo.git.diff("HEAD^", "HEAD", "--numstat",diff.a_path).split()

                insertions, deletions = self._calculate_diff_stats(content)
            except git.GitCommandError as e:
                content = f"[Error getting diff: {str(e)}]"

        return status, content, insertions, deletions

    def _calculate_diff_stats(self, diff_content: str) -> Tuple[int, int]:
        """Caculates the number of inserted and deleted lines in a diff content"""
        insertions = deletions = 0
        for line in diff_content.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                insertions += 1
            elif line.startswith('-') and not line.startswith('---'):
                deletions += 1
        return insertions, deletions

    def _handle_modified_file(self, file_path: str,
                              file_path_obj: Path) -> Tuple[str, str]:
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
            return "modified", diff
        except git.exc.GitCommandError:
            # If file doesn't exist, treat it as deleted
            if not file_path_obj.exists():
                return "deleted", "[File deleted]"
            # If file exists but diff failed, something else is wrong
            raise IOError(f"Failed to get diff for {file_path}")

    def _handle_untracked_file(self, file_path: str,
                               file_path_obj: Path) -> Tuple[str, str]:
        """Handle untracked file status and content reading

        Args:
            file_path (str): Path to the file
            file_path_obj (Path): Path object for the file

        Returns:
            Tuple[str, str]: (status, content)
        """
        if not file_path_obj.is_file():
            return "deleted", "[File deleted]"

        try:
            # Check if file is binary
            with open(file_path, "rb") as f:
                content = f.read(
                    1024 * 1024)  # Read first MB to check for binary content
                if b"\0" in content:
                    return "new file (binary)", "[Binary file]"

            # File is not binary, try to read as text
            with open(file_path, "r", encoding="utf-8") as f:
                return "new file", f.read()
        except UnicodeDecodeError:
            return "new file (binary)", "[Binary file]"

    def stage_files(self, files: List[str]) -> None:
        """Stage specified files

        Args:
            files: List of files to stage

        Raises:
            git.GitCommandError: If there is an error staging the files
        """
        try:
            # Get current status of files
            status = self.repo.git.status("--porcelain").splitlines()

            for file in files:
                # Find status for this file
                file_status = next(
                    (s for s in status if s.split()[-1] == file), None)
                if file_status and file_status.startswith(" D"):
                    # File is deleted, use remove
                    self.repo.index.remove([file])
                else:
                    # File is modified or new, use add
                    self.repo.index.add([file])
        except git.GitCommandError as e:
            raise git.GitCommandError(f"Failed to stage files: {str(e)}",
                                      e.status, e.stderr)

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
            raise git.GitCommandError(f"Failed to commit changes: {str(e)}",
                                      e.status, e.stderr)

    def push_changes(self,
                     remote: str = "origin",
                     branch: Optional[str] = None) -> None:
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
            raise git.GitCommandError(f"Failed to push changes: {str(e)}",
                                      e.status, e.stderr)

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
            raise git.GitCommandError(
                f"Failed to get current branch: {str(e)}", e.status, e.stderr)

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
            raise git.GitCommandError(f"Failed to checkout branch: {str(e)}",
                                      e.status, e.stderr)

    def get_commit_history(self, max_count: int = 10) -> List[Dict]:
        """Get commit history

        Args:
            max_count: Maximum number of commits to return

        Returns:
            List[Dict]: List of commits with their details

        Raises:
            git.GitCommandError: If there is an error getting the commit history
        """
        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=max_count):
                commits.append({
                    "hash": commit.hexsha,
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": commit.committed_datetime.isoformat(),
                })
            return commits
        except git.GitCommandError as e:
            raise git.GitCommandError(
                f"Failed to get commit history: {str(e)}", e.status, e.stderr)

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
            parent = commit.parents[0] if commit.parents else self.repo.tree(
                "4b825dc642cb6eb9a060e54bf8d69288fbee4904")

            changes = []
            diff_index = parent.diff(commit)

            for diff in diff_index:
                status = "error"
                content = ""
                insertions = 0
                deletions = 0
                try:
                    status, content, insertions, deletions = self._process_file_diff(
                        diff)
                except Exception as e:
                    status = "error"
                    content = f"[Unexpected error: {str(e)}]"

                changes.append(
                    Change(file=diff.b_path or diff.a_path,
                           status=status,
                           diff=content,
                           insertions=insertions,
                           deletions=deletions))

            return changes
        except git.GitCommandError as e:
            raise git.GitCommandError(
                f"Failed to get commit changes: {str(e)}", e.status, e.stderr)
