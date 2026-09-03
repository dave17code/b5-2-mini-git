from __future__ import annotations

import shlex
from datetime import datetime
from typing import Callable, Optional, TypeVar


T = TypeVar("T")


class Commit:
    """A commit node in the Mini Git DAG."""

    def __init__(
        self,
        commit_hash: str,
        message: str,
        author: str,
        timestamp: datetime,
        parents: list[str],
    ) -> None:
        self.hash = commit_hash
        self.message = message
        self.author = author
        self.timestamp = timestamp
        self.parents = parents


class Algorithms:
    """Graph traversal and custom sorting algorithms used by Mini Git."""

    @staticmethod
    def merge_sort(items: list[T], key: Callable[[T], object]) -> list[T]:
        """Stable merge sort. Python's built-in sorting APIs are not used."""
        if len(items) <= 1:
            return items[:]

        middle = len(items) // 2
        left = Algorithms.merge_sort(items[:middle], key)
        right = Algorithms.merge_sort(items[middle:], key)
        return Algorithms._merge(left, right, key)

    @staticmethod
    def _merge(left: list[T], right: list[T], key: Callable[[T], object]) -> list[T]:
        merged: list[T] = []
        left_index = 0
        right_index = 0

        while left_index < len(left) and right_index < len(right):
            # Choosing the left item on equality keeps the algorithm stable.
            if key(left[left_index]) <= key(right[right_index]):
                merged.append(left[left_index])
                left_index += 1
            else:
                merged.append(right[right_index])
                right_index += 1

        while left_index < len(left):
            merged.append(left[left_index])
            left_index += 1

        while right_index < len(right):
            merged.append(right[right_index])
            right_index += 1

        return merged

    @staticmethod
    def parent_first_order(commits: dict[str, Commit]) -> list[str]:
        """Return a DFS-based topological-style order: every parent before its child."""
        visited: set[str] = set()
        result: list[str] = []

        def dfs(commit_hash: str) -> None:
            if commit_hash in visited:
                return

            visited.add(commit_hash)
            commit = commits[commit_hash]
            for parent_hash in commit.parents:
                dfs(parent_hash)
            result.append(commit_hash)

        # dict preserves insertion order, so output is deterministic for a session.
        for commit_hash in commits:
            dfs(commit_hash)

        return result

    @staticmethod
    def ancestors(commits: dict[str, Commit], start_hash: str) -> list[str]:
        """Return all ancestors reachable by repeatedly following parent links."""
        visited: set[str] = set()
        result: list[str] = []

        def dfs(commit_hash: str) -> None:
            commit = commits[commit_hash]
            for parent_hash in commit.parents:
                if parent_hash in visited:
                    continue
                visited.add(parent_hash)
                result.append(parent_hash)
                dfs(parent_hash)

        dfs(start_hash)
        return result

    @staticmethod
    def shortest_path_undirected(
        commits: dict[str, Commit], start_hash: str, end_hash: str
    ) -> Optional[list[str]]:
        """BFS shortest path where commit-parent connections are treated as undirected.

        When several shortest paths exist, neighbors are visited in lexical hash order.
        With FIFO BFS this makes the first discovered shortest path lexicographically
        smallest for this fixed-format hash representation.
        """
        if start_hash == end_hash:
            return [start_hash]

        adjacency: dict[str, list[str]] = {commit_hash: [] for commit_hash in commits}

        for child_hash, commit in commits.items():
            for parent_hash in commit.parents:
                adjacency[child_hash].append(parent_hash)
                adjacency[parent_hash].append(child_hash)

        # Sort every adjacency list using our own merge sort, never built-in sorting.
        for commit_hash in adjacency:
            adjacency[commit_hash] = Algorithms.merge_sort(
                adjacency[commit_hash], key=lambda value: value
            )

        queue: list[str] = [start_hash]
        queue_index = 0
        visited: set[str] = {start_hash}
        previous: dict[str, Optional[str]] = {start_hash: None}

        while queue_index < len(queue):
            current = queue[queue_index]
            queue_index += 1

            for neighbor in adjacency[current]:
                if neighbor in visited:
                    continue

                visited.add(neighbor)
                previous[neighbor] = current

                if neighbor == end_hash:
                    path: list[str] = []
                    cursor: Optional[str] = end_hash
                    while cursor is not None:
                        path.append(cursor)
                        cursor = previous[cursor]
                    path.reverse()
                    return path

                queue.append(neighbor)

        return None


class MiniGit:
    """In-memory Mini Git repository focused on graph, search, and sorting concepts."""

    def __init__(self) -> None:
        self.initialized = False
        self.current_user: Optional[str] = None
        self.current_branch: Optional[str] = None
        self.commits: dict[str, Commit] = {}
        self.branches: dict[str, Optional[str]] = {}
        self.keyword_index: dict[str, list[str]] = {}
        self.author_index: dict[str, list[str]] = {}
        self._commit_counter = 0

    def init(self, user_name: str) -> None:
        """Reset and initialize the repository with a main branch and current user."""
        self.initialized = True
        self.current_user = user_name
        self.current_branch = "main"
        self.commits = {}
        self.branches = {"main": None}
        self.keyword_index = {}
        self.author_index = {}
        self._commit_counter = 0

        print("Initialized repository.")
        print("Current branch: main")
        print(f"Current user: {user_name}")

    def branch(self, branch_name: str) -> None:
        """Create a branch pointing at the current branch's HEAD commit."""
        if branch_name in self.branches:
            print(f"Branch already exists: {branch_name}")
            return

        assert self.current_branch is not None
        self.branches[branch_name] = self.branches[self.current_branch]
        print(f"Created branch: {branch_name}")

    def switch(self, branch_name: str) -> None:
        """Move HEAD to another existing branch."""
        if branch_name not in self.branches:
            print(f"Unknown branch: {branch_name}")
            return

        self.current_branch = branch_name
        print(f"Switched to branch: {branch_name}")

    def commit(self, message: str) -> None:
        """Create a commit, move the current branch, and update inverted indexes."""
        assert self.current_branch is not None
        assert self.current_user is not None

        parent_hash = self.branches[self.current_branch]
        parents = [] if parent_hash is None else [parent_hash]

        commit_hash = self._next_unique_hash()
        commit = Commit(
            commit_hash=commit_hash,
            message=message,
            author=self.current_user,
            timestamp=datetime.now(),
            parents=parents,
        )

        self.commits[commit_hash] = commit
        self.branches[self.current_branch] = commit_hash
        self._update_indexes(commit)

        print(f"[{self.current_branch} {commit_hash}] {message}")

    def log(self, sort_by: Optional[str] = None) -> None:
        """Print commits in parent-first order or with a custom merge-sort criterion."""
        if not self.commits:
            print("No commits")
            return

        if sort_by is None:
            hashes = Algorithms.parent_first_order(self.commits)
            commits_to_print = [self.commits[commit_hash] for commit_hash in hashes]
        elif sort_by == "date":
            commits_to_print = Algorithms.merge_sort(
                list(self.commits.values()), key=lambda commit: commit.timestamp
            )
        elif sort_by == "author":
            commits_to_print = Algorithms.merge_sort(
                list(self.commits.values()), key=lambda commit: commit.author.lower()
            )
        else:
            print("Invalid args")
            return

        for commit in commits_to_print:
            self._print_commit(commit)

    def path(self, start_hash: str, end_hash: str) -> None:
        """Print the lexicographically smallest shortest undirected commit path."""
        if start_hash not in self.commits:
            print(f"Unknown commit: {start_hash}")
            return
        if end_hash not in self.commits:
            print(f"Unknown commit: {end_hash}")
            return

        path = Algorithms.shortest_path_undirected(
            self.commits, start_hash, end_hash
        )
        if path is None:
            print("No path")
            return

        print("Path: " + " -> ".join(path))

    def ancestors(self, commit_hash: str) -> None:
        """Print every ancestor of the given commit."""
        if commit_hash not in self.commits:
            print(f"Unknown commit: {commit_hash}")
            return

        ancestor_hashes = Algorithms.ancestors(self.commits, commit_hash)
        if not ancestor_hashes:
            print("No ancestors")
            return

        print(f"Ancestors of {commit_hash}:")
        for ancestor_hash in ancestor_hashes:
            commit = self.commits[ancestor_hash]
            print(f"- {commit.hash}: {commit.message}")

    def search_keyword(self, keyword: str) -> None:
        """Search only through inverted-index candidates, never all commits."""
        tokens = self._tokens(keyword)
        if not tokens:
            print("Invalid args")
            return

        first_candidates = self.keyword_index.get(tokens[0], [])
        candidate_hashes = first_candidates[:]

        # Intersect index posting lists while preserving the first list's order.
        for token in tokens[1:]:
            allowed = set(self.keyword_index.get(token, []))
            candidate_hashes = [
                commit_hash
                for commit_hash in candidate_hashes
                if commit_hash in allowed
            ]

        self._print_search_results(candidate_hashes)

    def search_author(self, author: str) -> None:
        """Search commits by normalized author through the author inverted index."""
        candidate_hashes = self.author_index.get(author.lower(), [])
        self._print_search_results(candidate_hashes)

    def _next_unique_hash(self) -> str:
        """Generate a session-unique counter-based pseudo hash."""
        while True:
            self._commit_counter += 1
            commit_hash = f"c{self._commit_counter:06d}"
            if commit_hash not in self.commits:
                return commit_hash

    def _update_indexes(self, commit: Commit) -> None:
        """Update keyword->hash and author->hash inverted indexes for one commit."""
        seen_tokens: set[str] = set()
        for token in self._tokens(commit.message):
            if token in seen_tokens:
                continue
            seen_tokens.add(token)
            self.keyword_index.setdefault(token, []).append(commit.hash)

        author_key = commit.author.lower()
        self.author_index.setdefault(author_key, []).append(commit.hash)

    @staticmethod
    def _tokens(text: str) -> list[str]:
        """Minimum required normalization: whitespace split + lowercase."""
        return [token.lower() for token in text.split() if token]

    def _print_commit(self, commit: Commit) -> None:
        labels = [
            branch_name
            for branch_name, pointed_hash in self.branches.items()
            if pointed_hash == commit.hash
        ]
        label_text = ""
        if labels:
            label_text = " [" + ", ".join(labels) + "]"

        timestamp_text = commit.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f"commit {commit.hash}{label_text}")
        print(f"Author: {commit.author}")
        print(f"Date: {timestamp_text}")
        print(f"Parents: {', '.join(commit.parents) if commit.parents else '-'}")
        print(f"Message: {commit.message}")
        print()

    def _print_search_results(self, commit_hashes: list[str]) -> None:
        count = len(commit_hashes)
        print(f"Found {count} commit{'s' if count != 1 else ''}:")
        for commit_hash in commit_hashes:
            commit = self.commits[commit_hash]
            print(f"- {commit.hash}: {commit.message}")


class CommandProcessor:
    """Parse CLI input and dispatch commands to the MiniGit repository."""

    def __init__(self, repository: MiniGit) -> None:
        self.repository = repository

    def execute(self, raw_line: str) -> bool:
        """Execute one command. Return False when the REPL should terminate."""
        try:
            tokens = shlex.split(raw_line)
        except ValueError:
            print("Invalid args")
            return True

        if not tokens:
            return True

        command = tokens[0].lower()

        if command in ("exit", "quit"):
            if len(tokens) != 1:
                print("Invalid args")
                return True
            return False

        if command == "init":
            if len(tokens) != 2 or not tokens[1]:
                print("Invalid args")
                return True
            self.repository.init(tokens[1])
            return True

        if not self.repository.initialized:
            print("Repository not initialized.")
            return True

        if command == "branch":
            if len(tokens) != 2 or not tokens[1]:
                print("Invalid args")
            else:
                self.repository.branch(tokens[1])
            return True

        if command == "switch":
            if len(tokens) != 2 or not tokens[1]:
                print("Invalid args")
            else:
                self.repository.switch(tokens[1])
            return True

        if command == "commit":
            if len(tokens) != 2 or not tokens[1]:
                print("Invalid args")
            else:
                self.repository.commit(tokens[1])
            return True

        if command == "log":
            if len(tokens) == 1:
                self.repository.log()
            elif len(tokens) == 2 and tokens[1].lower().startswith("--sort-by="):
                sort_by = tokens[1].split("=", 1)[1].lower()
                if sort_by not in ("date", "author"):
                    print("Invalid args")
                else:
                    self.repository.log(sort_by=sort_by)
            else:
                print("Invalid args")
            return True

        if command == "path":
            if len(tokens) != 3:
                print("Invalid args")
            else:
                self.repository.path(tokens[1], tokens[2])
            return True

        if command == "ancestors":
            if len(tokens) != 2:
                print("Invalid args")
            else:
                self.repository.ancestors(tokens[1])
            return True

        if command == "search":
            if len(tokens) != 2 or not tokens[1]:
                print("Invalid args")
            elif tokens[1].lower().startswith("--author="):
                author = tokens[1].split("=", 1)[1]
                if not author:
                    print("Invalid args")
                else:
                    self.repository.search_author(author)
            else:
                self.repository.search_keyword(tokens[1])
            return True

        print(f"Unknown command: {tokens[0]}")
        return True


def main() -> None:
    """Run the Mini Git REPL."""
    repository = MiniGit()
    processor = CommandProcessor(repository)

    while True:
        try:
            raw_line = input("mini-git> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not processor.execute(raw_line):
            break


if __name__ == "__main__":
    main()
