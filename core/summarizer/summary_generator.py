import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from backend.parsing.code_parser import FileMetadata

load_dotenv()


class SummaryGenerator:
    """Generates multi-level code summaries using Groq LLM."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
        self.llm = ChatGroq(
            api_key=api_key,
            model_name="openai/gpt-oss-20b",
            temperature=0.3,
            max_tokens=256,
        )

    def _call_llm(self, prompt: str) -> str:
        """Send a prompt to Groq and return the response text."""
        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception:
            return "(summary unavailable)"

    def generate_all(
        self,
        parsed_files: list[FileMetadata],
        repo_tree: list[dict],
        repo_name: str,
    ) -> dict:
        """Generate multi-level summaries bottom-up:
        function → file → folder → repository.

        Returns a dict with keys: repo, folders, files, functions.
        """
        summaries = {
            "repo": "",
            "folders": {},
            "files": {},
            "functions": {},
        }

        # ── Level 1: Function summaries ──
        for meta in parsed_files:
            for func in meta.functions:
                key = f"{meta.file_path}::{func.name}"
                summaries["functions"][key] = self._summarize_function(func, meta)

            for cls in meta.classes:
                for method in cls.methods:
                    key = f"{meta.file_path}::{cls.name}.{method.name}"
                    summaries["functions"][key] = self._summarize_function(method, meta)

        # ── Level 2: File summaries ──
        for meta in parsed_files:
            func_names = [f.name for f in meta.functions]
            class_names = [c.name for c in meta.classes]
            summaries["files"][meta.file_path] = self._summarize_file(
                meta, func_names, class_names
            )

        # ── Level 3: Folder summaries ──
        folders: dict[str, list[str]] = {}
        for meta in parsed_files:
            folder = os.path.dirname(meta.file_path) or "root"
            folders.setdefault(folder, []).append(meta.file_path)

        for folder, files in folders.items():
            file_summaries = {f: summaries["files"].get(f, "") for f in files}
            summaries["folders"][folder] = self._summarize_folder(folder, file_summaries)

        # ── Level 4: Repository summary ──
        summaries["repo"] = self._summarize_repo(repo_name, summaries["folders"])

        # ── Cache result ──
        os.makedirs("data", exist_ok=True)
        cache_path = f"data/{repo_name}_summaries.json"
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(summaries, f, indent=2)

        return summaries

    # ── Private helpers ──────────────────────────────────────────

    def _summarize_function(self, func, meta: FileMetadata) -> str:
        prompt = (
            f"In one sentence, describe what this function does.\n\n"
            f"Function: {func.name}\n"
            f"File: {meta.file_path}\n"
            f"Code:\n{func.code[:1500]}\n\n"
            f"Summary:"
        )
        return self._call_llm(prompt)

    def _summarize_file(self, meta: FileMetadata, funcs: list, classes: list) -> str:
        prompt = (
            f"In one sentence, describe what this file does.\n\n"
            f"File: {meta.file_path}\n"
            f"Language: {meta.language}\n"
            f"Functions: {', '.join(funcs) if funcs else 'none'}\n"
            f"Classes: {', '.join(classes) if classes else 'none'}\n"
            f"Imports: {', '.join(meta.imports[:20])}\n\n"
            f"Summary:"
        )
        return self._call_llm(prompt)

    def _summarize_folder(self, folder: str, file_summaries: dict) -> str:
        files_desc = "\n".join(f"  {f}: {s}" for f, s in file_summaries.items())
        prompt = (
            f"In one sentence, describe the purpose of this folder.\n\n"
            f"Folder: {folder}\n"
            f"Files:\n{files_desc}\n\n"
            f"Summary:"
        )
        return self._call_llm(prompt)

    def _summarize_repo(self, repo_name: str, folder_summaries: dict) -> str:
        folders_desc = "\n".join(f"  {f}: {s}" for f, s in folder_summaries.items())
        prompt = (
            f"In 2-3 sentences, describe what this repository does.\n\n"
            f"Repository: {repo_name}\n"
            f"Folder summaries:\n{folders_desc}\n\n"
            f"Summary:"
        )
        return self._call_llm(prompt)
