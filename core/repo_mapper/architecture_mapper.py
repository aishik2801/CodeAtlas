import json
import os


class ArchitectureMapper:
    """Generates a formatted repository architecture tree."""

    def generate_tree(self, repo_tree: list[dict]) -> str:
        """Build a pretty-printed directory tree from GitHub tree API data.

        Args:
            repo_tree: List of dicts with 'path' and 'type' keys.

        Returns:
            Formatted tree string.
        """
        # Build nested dict
        root: dict = {}
        for item in repo_tree:
            parts = item["path"].split("/")
            node = root
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            if item.get("type") == "tree":
                node.setdefault(parts[-1], {})
            else:
                node[parts[-1]] = None  # leaf file

        lines: list[str] = []
        self._render(root, "", lines, is_last=True, is_root=True)
        return "\n".join(lines)

    def _render(self, node: dict, prefix: str, lines: list[str],
                is_last: bool = True, is_root: bool = False):
        items = sorted(node.keys(), key=lambda k: (node[k] is None, k))
        for i, name in enumerate(items):
            last = i == len(items) - 1
            connector = "└── " if last else "├── "
            lines.append(f"{prefix}{connector}{name}{'/' if node[name] is not None else ''}")
            if node[name] is not None:
                extension = "    " if last else "│   "
                self._render(node[name], prefix + extension, lines, last)

    def generate_folder_map(self, repo_tree: list[dict]) -> dict:
        """Group files by their top-level folder.

        Returns dict[folder_name -> list of file paths].
        """
        folder_map: dict[str, list[str]] = {}
        for item in repo_tree:
            if item.get("type") != "blob":
                continue
            path = item["path"]
            parts = path.split("/")
            folder = parts[0] if len(parts) > 1 else "root"
            folder_map.setdefault(folder, []).append(path)
        return folder_map
