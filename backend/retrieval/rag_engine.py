import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from backend.embeddings.embedding_service import EmbeddingService
from vectorstore.vector_store_manager import VectorStoreManager

load_dotenv()


class RAGEngine:
    """Retrieval-Augmented Generation engine for code Q&A."""

    PROMPT_TEMPLATE = """You are an expert code analyst examining a GitHub repository.
Use ONLY the provided code context to answer the question.
If the answer is not in the context, say so clearly.

Provide:
1. A clear explanation
2. Relevant file paths and function names
3. Code snippets when helpful

--- CODE CONTEXT ---
{context}
--- END CONTEXT ---

Question: {question}

Answer:"""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
        self.llm = ChatGroq(
            api_key=api_key,
            model_name="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=2048,
        )
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreManager()

    def answer(self, query: str, top_k: int = 10) -> dict:
        """Answer a user question using RAG.

        1. Embed the query
        2. Retrieve top-k similar code chunks
        3. Build prompt with context
        4. Call Groq LLM for reasoning

        Returns dict with 'answer', 'sources', and 'chunks'.
        """
        # Step 1: embed query
        query_vec = self.embedding_service.embed_query(query)

        # Step 2: retrieve relevant chunks
        results = self.vector_store.search(query_vec, top_k=top_k)

        # Step 3: build context string
        context_parts = []
        sources = []
        for r in results:
            context_parts.append(
                f"### {r['file_path']} — {r['chunk_type']}: {r['name']}\n"
                f"{r['code']}\n"
            )
            if r["file_path"] not in sources:
                sources.append(r["file_path"])

        context = "\n".join(context_parts)

        # Step 4: call Groq LLM
        prompt = self.PROMPT_TEMPLATE.format(context=context, question=query)
        response = self.llm.invoke(prompt)

        return {
            "answer": response.content,
            "sources": sources,
            "chunks": results,
        }
