import ast
import re
import os
from dataclasses import dataclass, field


@dataclass
class FunctionInfo:
    name: str
    args: list[str] = field(default_factory=list)
    docstring: str = ""
    start_line: int = 0
    end_line: int = 0
    code: str = ""


@dataclass
class ClassInfo:
    name: str
    methods: list[FunctionInfo] = field(default_factory=list)
    docstring: str = ""
    start_line: int = 0
    end_line: int = 0
    code: str = ""


@dataclass
class FileMetadata:
    file_path: str
    language: str
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    docstring: str = ""
    raw_code: str = ""


class CodeParser:
    """Parses source code files to extract structural metadata."""

    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript", ".jsx": "javascript",
        ".ts": "typescript", ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".cpp": "cpp", ".c": "c", ".h": "c",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
    }

    def parse_file(self, code: str, file_path: str) -> FileMetadata:
        """Parse a source file and extract metadata.

        Uses Python AST for .py files, regex fallback for others.
        """
        ext = os.path.splitext(file_path)[1].lower()
        language = self.LANGUAGE_MAP.get(ext, "unknown")

        if language == "python":
            return self._parse_python(code, file_path, language)
        return self._parse_generic(code, file_path, language)

    # ── Python-specific parsing via ast ──────────────────────────

    def _parse_python(self, code: str, file_path: str, language: str) -> FileMetadata:
        lines = code.split("\n")
        meta = FileMetadata(
            file_path=file_path,
            language=language,
            raw_code=code,
        )

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return self._parse_generic(code, file_path, language)

        meta.docstring = ast.get_docstring(tree) or ""
        meta.imports = self._extract_imports(tree)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                meta.functions.append(self._extract_function(node, lines))
            elif isinstance(node, ast.ClassDef):
                meta.classes.append(self._extract_class(node, lines))

        return meta

    def _extract_function(self, node, lines: list[str]) -> FunctionInfo:
        start = node.lineno - 1
        end = node.end_lineno or node.lineno
        return FunctionInfo(
            name=node.name,
            args=[a.arg for a in node.args.args],
            docstring=ast.get_docstring(node) or "",
            start_line=node.lineno,
            end_line=end,
            code="\n".join(lines[start:end]),
        )

    def _extract_class(self, node, lines: list[str]) -> ClassInfo:
        start = node.lineno - 1
        end = node.end_lineno or node.lineno
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._extract_function(item, lines))
        return ClassInfo(
            name=node.name,
            methods=methods,
            docstring=ast.get_docstring(node) or "",
            start_line=node.lineno,
            end_line=end,
            code="\n".join(lines[start:end]),
        )

    @staticmethod
    def _extract_imports(tree) -> list[str]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.append(module)
        return imports

    # ── Generic regex-based parsing for non-Python files ────────

    def _parse_generic(self, code: str, file_path: str, language: str) -> FileMetadata:
        meta = FileMetadata(
            file_path=file_path,
            language=language,
            raw_code=code,
        )

        # Extract imports
        import_patterns = [
            r'^import\s+.+',                          # JS/TS/Java/Go
            r'^from\s+\S+\s+import\s+.+',             # Python-style
            r'^#include\s+[<"].+[>"]',                 # C/C++
            r'^use\s+.+;',                             # Rust
            r'^require\s*\(.+\)',                      # JS require
            r'^using\s+.+;',                           # C#
        ]
        for pattern in import_patterns:
            meta.imports.extend(
                m.group(0) for m in re.finditer(pattern, code, re.MULTILINE)
            )

        # Extract functions
        func_patterns = [
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)',   # JS/TS
            r'(?:public|private|protected)?\s*\w+\s+(\w+)\s*\([^)]*\)\s*\{',  # Java/C++
            r'func\s+(\w+)',                                   # Go
            r'fn\s+(\w+)',                                     # Rust
            r'def\s+(\w+)',                                    # Ruby/Python
        ]
        lines = code.split("\n")
        for pattern in func_patterns:
            for match in re.finditer(pattern, code):
                line_num = code[:match.start()].count("\n") + 1
                meta.functions.append(FunctionInfo(
                    name=match.group(1),
                    start_line=line_num,
                    end_line=min(line_num + 20, len(lines)),
                    code="\n".join(lines[line_num - 1:min(line_num + 20, len(lines))]),
                ))

        # Extract classes
        class_patterns = [
            r'class\s+(\w+)',
            r'struct\s+(\w+)',
            r'interface\s+(\w+)',
        ]
        for pattern in class_patterns:
            for match in re.finditer(pattern, code):
                line_num = code[:match.start()].count("\n") + 1
                meta.classes.append(ClassInfo(
                    name=match.group(1),
                    start_line=line_num,
                    end_line=min(line_num + 30, len(lines)),
                    code="\n".join(lines[line_num - 1:min(line_num + 30, len(lines))]),
                ))

        return meta
