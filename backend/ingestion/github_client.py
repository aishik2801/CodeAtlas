import os
import json
import base64
import requests
from dotenv import load_dotenv

load_dotenv()


class GitHubClient:
    """Handles GitHub API interactions for repository ingestion."""

    BASE_URL = "https://api.github.com"

    def __init__(self, repo_url: str):
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN not found in .env")
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.owner, self.repo = self._parse_url(repo_url)

    @staticmethod
    def _parse_url(url: str) -> tuple:
        """Extract owner and repo name from GitHub URL."""
        url = url.rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]
        parts = url.replace("https://github.com/", "").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {url}")
        return parts[0], parts[1]

    def fetch_repo_tree(self, branch: str = "main") -> list[dict]:
        """Fetch the full repository file tree recursively.

        Tries 'main' branch first, falls back to 'master'.
        Saves result to data/repo_tree.json.
        """
        for ref in [branch, "master"]:
            url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/git/trees/{ref}?recursive=1"
            resp = requests.get(url, headers=self.headers, timeout=30)
            if resp.status_code == 200:
                tree = resp.json().get("tree", [])
                self._save_tree(tree)
                return tree
        raise RuntimeError(
            f"Failed to fetch repo tree for {self.owner}/{self.repo}. "
            f"Status: {resp.status_code}"
        )

    def _save_tree(self, tree: list[dict]):
        """Persist the repo tree to data/repo_tree.json."""
        os.makedirs("data", exist_ok=True)
        with open("data/repo_tree.json", "w", encoding="utf-8") as f:
            json.dump(tree, f, indent=2)

    def download_file(self, file_path: str) -> str:
        """Download a single file's content from the repository."""
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/contents/{file_path}"
        resp = requests.get(url, headers=self.headers, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to download {file_path}: {resp.status_code}")
        content = resp.json().get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="replace")

    def download_all_files(self, file_paths: list[str], batch_size: int = 50) -> dict:
        """Download multiple files with local caching.

        Returns dict mapping file_path -> file_content.
        """
        cache_dir = os.path.join("data", "repo_cache", self.repo)
        os.makedirs(cache_dir, exist_ok=True)
        results = {}

        for i, path in enumerate(file_paths):
            cached = os.path.join(cache_dir, path.replace("/", os.sep))

            # Return from cache if available
            if os.path.exists(cached):
                with open(cached, "r", encoding="utf-8", errors="replace") as f:
                    results[path] = f.read()
                continue

            try:
                content = self.download_file(path)
                # Cache locally
                os.makedirs(os.path.dirname(cached), exist_ok=True)
                with open(cached, "w", encoding="utf-8") as f:
                    f.write(content)
                results[path] = content
            except Exception as e:
                print(f"[WARN] Skipping {path}: {e}")

            if (i + 1) % batch_size == 0:
                print(f"  Downloaded {i + 1}/{len(file_paths)} files...")

        print(f"  Downloaded {len(results)}/{len(file_paths)} files total.")
        return results
