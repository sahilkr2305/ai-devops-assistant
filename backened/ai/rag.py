from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# ==================================================
# PATHS
# ==================================================

BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

CHROMA_DIR = (
    BASE_DIR / "data" / "chroma"
)


# ==================================================
# EMBEDDING MODEL
# ==================================================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ==================================================
# CHROMA VECTOR STORE
# ==================================================

vector_store = Chroma(
    persist_directory=str(CHROMA_DIR),
    embedding_function=embeddings,
    collection_name="devops_knowledge"
)


# ==================================================
# RETRIEVE KNOWLEDGE
# ==================================================

def retrieve_context(
    query: str,
    k: int = 4
) -> str:
    """
    Search the DevOps knowledge base and return
    relevant chunks with their source filenames.
    """

    if not query.strip():
        return ""

    documents = vector_store.similarity_search(
        query,
        k=k
    )

    if not documents:
        return ""

    context_parts = []

    for index, document in enumerate(
        documents,
        start=1
    ):
        source = document.metadata.get(
            "source",
            "unknown"
        )

        content = document.page_content.strip()

        context_parts.append(
            f"[Knowledge Source {index}: {source}]\n"
            f"{content}"
        )

    return "\n\n---\n\n".join(
        context_parts
    )