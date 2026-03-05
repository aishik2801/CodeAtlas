import os

# ── File extensions we actually want to process ──
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".go", ".cpp", ".c", ".h",
    ".rs", ".rb", ".php", ".swift", ".kt",
}

# ── Directories that should be completely ignored ──
IGNORED_DIRS = {
    "node_modules", "dist", "build", "__pycache__",
    ".env", "logs", ".git", ".github", ".vscode",
    "venv", "env", ".idea", "target", "bin", "obj",
    ".next", "coverage", ".tox", "egg-info",
}

# ── Individual file-names to skip ──
IGNORED_FILES = {
    "package-lock.json", "yarn.lock", "poetry.lock",
    ".DS_Store", "Thumbs.db",
}


def filter_files(tree_items: list[dict]) -> list[str]:
    """Filter repository tree items to only meaningful code files.

    Args:
        tree_items: List of dicts from GitHub tree API, each with
                    'path', 'type', and 'size' keys.

    Returns:
        List of file paths worth processing.
    """
    filtered = []
    for item in tree_items:
        if item.get("type") != "blob":
            continue

        path = item.get("path", "")
        _, ext = os.path.splitext(path)

        # Skip unsupported extensions
        if ext.lower() not in SUPPORTED_EXTENSIONS:
            continue

        # Skip files inside ignored directories
        parts = path.split("/")
        if any(part in IGNORED_DIRS for part in parts):
            continue

        # Skip ignored file names
        if os.path.basename(path) in IGNORED_FILES:
            continue

        # Skip very large files (>500 KB likely auto-generated)
        size = item.get("size", 0)
        if size > 500_000:
            continue

        filtered.append(path)

    return filtered
