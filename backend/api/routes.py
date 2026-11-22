import os
import sys
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()

from backend.ingestion.github_client import GitHubClient
from backend.ingestion.file_filter import filter_files
from backend.parsing.code_parser import CodeParser
from core.chunking.ast_chunker import ASTChunker
from backend.embeddings.embedding_service import EmbeddingService
from vectorstore.vector_store_manager import VectorStoreManager
from backend.retrieval.rag_engine import RAGEngine
from core.repo_mapper.architecture_mapper import ArchitectureMapper
from core.dependency_graph.graph_builder import DependencyGraphBuilder
from core.summarizer.summary_generator import SummaryGenerator

app = FastAPI(title="AI Codebase Summarizer API")

# ── Shared state ─────────────────────────────────────────────
_state: dict = {}


# ── Request / Response models ────────────────────────────────
class IngestRequest(BaseModel):
    repo_url: str


class QueryRequest(BaseModel):
    question: str
    top_k: int = 10


# ── Endpoints ────────────────────────────────────────────────

@app.post("/ingest")
def ingest_repo(req: IngestRequest):
    """Full pipeline: fetch → filter → parse → chunk → embed → index."""
    try:
        # 1. Fetch repo tree
        client = GitHubClient(req.repo_url)
        repo_name = client.repo
        tree = client.fetch_repo_tree()

        # 2. Filter files
        paths = filter_files(tree)
        if not paths:
            raise HTTPException(400, "No supported code files found in this repository.")

        # 3. Download files
        file_contents = client.download_all_files(paths)

        # 4. Parse files
        parser = CodeParser()
        parsed_files = []
        for path, code in file_contents.items():
            meta = parser.parse_file(code, path)
            parsed_files.append(meta)

        # 5. Chunk
        chunker = ASTChunker()
        all_chunks = []
        for meta in parsed_files:
            all_chunks.extend(chunker.chunk_file(meta))

        if not all_chunks:
            raise HTTPException(400, "No code chunks produced after parsing.")

        # 6. Embed
        embed_service = EmbeddingService()
        texts = [c.to_text() for c in all_chunks]
        vectors = embed_service.embed_texts(texts)

        # 7. Store in FAISS
        store = VectorStoreManager()
        store.build_index(all_chunks, vectors)

        # 8. Build dependency graph
        graph_builder = DependencyGraphBuilder()
        graph_builder.build_graph(parsed_files)
        graph_builder.save_json()

        # 9. Architecture map
        mapper = ArchitectureMapper()
        arch_tree = mapper.generate_tree(tree)

        # 10. Multi-level summaries
        summarizer = SummaryGenerator()
        summaries = summarizer.generate_all(parsed_files, tree, repo_name)

        # Cache state for later queries
        _state["repo_name"] = repo_name
        _state["tree"] = tree
        _state["arch_tree"] = arch_tree
        _state["graph_json"] = graph_builder.to_json()
        _state["summaries"] = summaries
        _state["parsed_files"] = len(parsed_files)
        _state["total_chunks"] = len(all_chunks)

        return {
            "status": "success",
            "repo": repo_name,
            "files_processed": len(parsed_files),
            "chunks_created": len(all_chunks),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/query")
def query_code(req: QueryRequest):
    """Answer a question about the ingested codebase."""
    try:
        engine = RAGEngine()
        result = engine.answer(req.question, top_k=req.top_k)
        return result
    except FileNotFoundError:
        raise HTTPException(400, "No codebase ingested yet. Please ingest a repo first.")
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/architecture/{repo}")
def get_architecture(repo: str):
    """Return the repository architecture tree."""
    arch = _state.get("arch_tree")
    if not arch:
        raise HTTPException(404, "Architecture map not available. Ingest a repo first.")
    return {"repo": repo, "tree": arch}


@app.get("/dependencies/{repo}")
def get_dependencies(repo: str):
    """Return the dependency graph JSON."""
    graph = _state.get("graph_json")
    if not graph:
        raise HTTPException(404, "Dependency graph not available. Ingest a repo first.")
    return {"repo": repo, "graph": graph}


@app.get("/summaries/{repo}")
def get_summaries(repo: str):
    """Return multi-level code summaries."""
    summaries = _state.get("summaries")
    if not summaries:
        raise HTTPException(404, "Summaries not available. Ingest a repo first.")
    return {"repo": repo, "summaries": summaries}
