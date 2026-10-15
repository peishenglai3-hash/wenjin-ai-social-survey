"""
Literature Vector Store — ChromaDB-based semantic search for academic papers.

Supports:
  - Incremental indexing of PaperResult objects
  - Semantic (vector similarity) search
  - Hybrid ranking: vector similarity × keyword relevance
"""
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Lazy imports — chromadb is a heavy dependency not required for basic app startup
_chromadb = None
_ChromaSettings = None


def _get_chromadb():
    global _chromadb, _ChromaSettings
    if _chromadb is None:
        import chromadb as _chromadb
        from chromadb.config import Settings as _ChromaSettings
    return _chromadb, _ChromaSettings


@dataclass
class SemanticSearchResult:
    """A paper matched via semantic search with relevance metadata."""
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    abstract: str = ""
    source: str = "openalex"
    citation_count: int = 0
    journal: str = ""
    methodology_tags: list[str] = field(default_factory=list)
    language: str = "en"
    url: str = ""
    score: float = 0.0  # 0-1 relevance score

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "doi": self.doi,
            "abstract": self.abstract[:500] if self.abstract else "",
            "source": self.source,
            "citation_count": self.citation_count,
            "journal": self.journal,
            "methodology_tags": self.methodology_tags,
            "language": self.language,
            "url": self.url,
            "score": round(self.score, 4),
        }


class LiteratureVectorStore:
    """ChromaDB-backed vector store for academic paper abstracts."""

    COLLECTION_NAME = "wenjin_papers"

    def __init__(self, persist_dir: str = "./chroma_data"):
        chromadb, ChromaSettings = _get_chromadb()
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = None
        self._persist_dir = persist_dir

    @property
    def collection(self):
        if self._collection is None:
            try:
                self._collection = self._client.get_collection(self.COLLECTION_NAME)
            except Exception:
                # Create with default embedding function (all-MiniLM-L6-v2, ~80MB auto-download)
                self._collection = self._client.create_collection(
                    name=self.COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"},
                )
        return self._collection

    def index_papers(self, papers: list, batch_size: int = 50) -> int:
        """Index a list of PaperResult objects into the vector store.

        Returns the number of newly indexed papers.
        """
        if not papers:
            return 0

        col = self.collection
        indexed = 0

        for i in range(0, len(papers), batch_size):
            batch = papers[i:i + batch_size]
            ids: list[str] = []
            documents: list[str] = []
            metadatas: list[dict] = []

            for p in batch:
                doc_id = p.doi or f"paper_{hash(p.title) & 0x7FFFFFFF:08x}"
                # Skip if already indexed
                try:
                    existing = col.get(ids=[doc_id])
                    if existing and existing["ids"]:
                        continue
                except Exception:
                    pass

                ids.append(doc_id)
                # Build a rich searchable document: title + abstract + journal + methodology
                doc_parts = [p.title]
                if p.abstract:
                    doc_parts.append(p.abstract[:1500])
                if p.journal:
                    doc_parts.append(f"[{p.journal}]")
                if p.methodology_tags:
                    doc_parts.append(f"Methods: {', '.join(p.methodology_tags)}")
                documents.append("\n".join(doc_parts))

                metadatas.append({
                    "title": p.title,
                    "year": p.year or 0,
                    "doi": p.doi or "",
                    "source": getattr(p, "source", "unknown"),
                    "citation_count": getattr(p, "citation_count", 0),
                    "language": getattr(p, "language", "en"),
                })

            if ids:
                try:
                    col.add(ids=ids, documents=documents, metadatas=metadatas)
                    indexed += len(ids)
                except Exception as e:
                    logger.warning("Chroma batch insert failed: %s", e)

        return indexed

    def semantic_search(
        self,
        query: str,
        top_n: int = 20,
        where: dict | None = None,
    ) -> list[SemanticSearchResult]:
        """Search papers by semantic similarity to the query string.

        Args:
            query: Natural language search query
            top_n: Maximum number of results
            where: Optional Chroma metadata filter (e.g., {"language": "zh"})
        """
        try:
            col = self.collection
            results = col.query(
                query_texts=[query],
                n_results=min(top_n, col.count()),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.warning("Semantic search failed: %s", e)
            return []

        if not results or not results["ids"] or not results["ids"][0]:
            return []

        papers: list[SemanticSearchResult] = []
        ids_list = results["ids"][0]
        docs_list = results["documents"][0] if results["documents"] else []
        metas_list = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        for idx, doc_id in enumerate(ids_list):
            meta = metas_list[idx] if idx < len(metas_list) else {}
            doc_text = docs_list[idx] if idx < len(docs_list) else ""
            distance = distances[idx] if idx < len(distances) else 1.0

            # Convert cosine distance to similarity score: 1 - distance (cosine)
            score = max(0.0, 1.0 - distance)

            # Extract abstract from document (everything after the title line)
            lines = doc_text.split("\n") if doc_text else []
            abstract = lines[1] if len(lines) > 1 else ""

            papers.append(SemanticSearchResult(
                title=meta.get("title", ""),
                year=meta.get("year") or None,
                doi=meta.get("doi") or None,
                abstract=abstract,
                source=meta.get("source", "unknown"),
                citation_count=meta.get("citation_count", 0),
                journal="",
                language=meta.get("language", "en"),
                url=f"https://doi.org/{meta['doi']}" if meta.get("doi") else "",
                score=score,
            ))

        return papers

    def hybrid_search(
        self,
        query: str,
        top_n: int = 20,
        where: dict | None = None,
        semantic_weight: float = 0.6,
    ) -> list[SemanticSearchResult]:
        """Combine semantic search with keyword-based re-ranking.

        The hybrid score = semantic_weight × vector_score + (1-semantic_weight) × keyword_overlap
        """
        semantic_results = self.semantic_search(query, top_n=top_n * 2, where=where)

        if not semantic_results:
            return []

        query_terms = set(query.lower().split())
        for paper in semantic_results:
            text = (paper.title + " " + paper.abstract).lower()
            text_terms = set(text.split())
            if query_terms:
                keyword_score = len(query_terms & text_terms) / len(query_terms)
            else:
                keyword_score = 0.0
            paper.score = semantic_weight * paper.score + (1 - semantic_weight) * keyword_score

        semantic_results.sort(key=lambda x: x.score, reverse=True)
        return semantic_results[:top_n]

    def count(self) -> int:
        """Return the number of indexed papers."""
        try:
            return self.collection.count()
        except Exception:
            return 0

    def clear(self):
        """Delete and recreate the collection."""
        try:
            self._client.delete_collection(self.COLLECTION_NAME)
        except Exception:
            pass
        self._collection = None


# Singleton
_vector_store: LiteratureVectorStore | None = None


def get_vector_store(persist_dir: str = "./chroma_data") -> LiteratureVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = LiteratureVectorStore(persist_dir=persist_dir)
    return _vector_store
