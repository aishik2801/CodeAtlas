from dataclasses import dataclass, field
from backend.parsing.code_parser import FileMetadata


@dataclass
class CodeChunk:
    """A single code chunk with rich metadata for embedding."""
    chunk_id: str
    file_path: str
    language: str
    chunk_type: str          # "function", "class", "module"
    name: str                # function/class name or file basename
    code: str
    docstring: str = ""
    dependencies: list[str] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0

    def to_text(self) -> str:
        """Serialize chunk into a text representation for embedding."""
        parts = [
            f"File: {self.file_path}",
            f"Language: {self.language}",
            f"Type: {self.chunk_type}",
            f"Name: {self.name}",
        ]
        if self.docstring:
            parts.append(f"Docstring: {self.docstring}")
        if self.dependencies:
            parts.append(f"Dependencies: {', '.join(self.dependencies)}")
        parts.append(f"Code:\n{self.code}")
        return "\n".join(parts)


class ASTChunker:
    """Produces AST-aware code chunks from parsed file metadata."""

    def __init__(self, max_chunk_lines: int = 200):
        self.max_chunk_lines = max_chunk_lines

    def chunk_file(self, metadata: FileMetadata) -> list[CodeChunk]:
        """Split a parsed file into semantically meaningful chunks.

        Strategy:
        1. Each function  → its own chunk
        2. Each class      → its own chunk (with methods inside)
        3. Remaining code  → one 'module' chunk (imports + top-level code)
        """
        chunks: list[CodeChunk] = []
        covered_lines: set[int] = set()

        # ── Per-function chunks ──
        for func in metadata.functions:
            chunk = CodeChunk(
                chunk_id=f"{metadata.file_path}::func::{func.name}",
                file_path=metadata.file_path,
                language=metadata.language,
                chunk_type="function",
                name=func.name,
                code=func.code,
                docstring=func.docstring,
                dependencies=metadata.imports,
                start_line=func.start_line,
                end_line=func.end_line,
            )
            chunks.append(chunk)
            covered_lines.update(range(func.start_line, func.end_line + 1))

        # ── Per-class chunks ──
        for cls in metadata.classes:
            method_names = [m.name for m in cls.methods]
            chunk = CodeChunk(
                chunk_id=f"{metadata.file_path}::class::{cls.name}",
                file_path=metadata.file_path,
                language=metadata.language,
                chunk_type="class",
                name=cls.name,
                code=cls.code,
                docstring=cls.docstring,
                dependencies=metadata.imports,
                start_line=cls.start_line,
                end_line=cls.end_line,
            )
            chunks.append(chunk)
            covered_lines.update(range(cls.start_line, cls.end_line + 1))

        # ── Module-level chunk (everything not already covered) ──
        lines = metadata.raw_code.split("\n")
        remaining = [
            lines[i] for i in range(len(lines))
            if (i + 1) not in covered_lines
        ]
        remaining_code = "\n".join(remaining).strip()

        if remaining_code:
            chunk = CodeChunk(
                chunk_id=f"{metadata.file_path}::module",
                file_path=metadata.file_path,
                language=metadata.language,
                chunk_type="module",
                name=metadata.file_path.split("/")[-1],
                code=remaining_code,
                docstring=metadata.docstring,
                dependencies=metadata.imports,
                start_line=1,
                end_line=len(lines),
            )
            chunks.append(chunk)

        # ── Split oversized chunks ──
        final_chunks = []
        for chunk in chunks:
            if chunk.code.count("\n") > self.max_chunk_lines:
                final_chunks.extend(self._split_large_chunk(chunk))
            else:
                final_chunks.append(chunk)

        return final_chunks

    def _split_large_chunk(self, chunk: CodeChunk) -> list[CodeChunk]:
        """Split a chunk that exceeds max_chunk_lines into sub-chunks."""
        lines = chunk.code.split("\n")
        sub_chunks = []
        for i in range(0, len(lines), self.max_chunk_lines):
            segment = lines[i:i + self.max_chunk_lines]
            sub = CodeChunk(
                chunk_id=f"{chunk.chunk_id}::part{i // self.max_chunk_lines}",
                file_path=chunk.file_path,
                language=chunk.language,
                chunk_type=chunk.chunk_type,
                name=chunk.name,
                code="\n".join(segment),
                docstring=chunk.docstring if i == 0 else "",
                dependencies=chunk.dependencies,
                start_line=chunk.start_line + i,
                end_line=chunk.start_line + i + len(segment),
            )
            sub_chunks.append(sub)
        return sub_chunks
