from typing import List, Dict, NamedTuple, Optional
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

        Raises:
            IOError: If there is an error reading a file
            git.GitCommandError: If there is an error executing a git command
        """
        changes = []

        # Get modified files
        modified_files = [item.a_path for item in self.repo.index.diff(None)]

        # Get untracked files
        untracked_files = self.repo.untracked_files

        for file_path in modified_files + untracked_files:
            try:
                file_path_obj = Path(file_path)

                if file_path in modified_files:
                    try:
                        diff = self.git.diff(file_path)
                        status = "modified"
                    except git.exc.GitCommandError:
                        status = "deleted"
                        diff = "[File deleted]"
                else:
                    if file_path_obj.is_file():
                        try:
                            # check if the file is binary
                            with open(file_path, "rb") as f:
                                content = f.read(1024 * 1024)
                                if b"\0" in content:
                                    diff = "[Binary file]"
                                    status = "new file (binary)"
                                else:
                                    # file is not binary
                                    with open(file_path, "r",
                                              encoding="utf-8") as f:
                                        diff = f.read()
                                    status = "new file"
                        except UnicodeDecodeError:
                            diff = "[Binary file]"
                            status = "new file (binary)"
                    else:
                        diff = "[File not found]"
                        status = "error"

                # Count insertions and deletions
                insertions = len(
                    [i_l for i_l in diff.split("\n") if i_l.startswith("+")])
                deletions = len(
                    [d_l for d_l in diff.split("\n") if d_l.startswith("-")])

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

    def stage_files(self, files: List[str]) -> None:
        """Stage specified files

        Args:
            files: List of files to stage

        Raises:
            git.GitCommandError: If there is an error staging the files
        """
        try:
            self.repo.index.add(files)
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
