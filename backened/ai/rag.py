from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


BASE_DIR = Path(__file__).resolve().parent.parent

CHROMA_DIR = BASE_DIR / "data" / "chroma"


embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


vector_store = Chroma(
    persist_directory=str(CHROMA_DIR),
    embedding_function=embeddings,
    collection_name="devops_knowledge"
)


def retrieve_context(
    query: str,
    k: int = 4
):

    documents = vector_store.similarity_search(
        query,
        k=k
    )

    if not documents:
        return ""

    context_parts = []

    for document in documents:

        context_parts.append(
            document.page_content
        )

    return "\n\n".join(
        context_parts
    )