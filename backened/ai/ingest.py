from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

KNOWLEDGE_DIR = BASE_DIR / "knowledge"

CHROMA_DIR = BASE_DIR / "data" / "chroma"


# ==================================================
# LOAD DOCUMENTS
# ==================================================

documents = []

for file_path in KNOWLEDGE_DIR.glob("*.md"):

    print(f"Loading: {file_path.name}")

    loader = TextLoader(
        str(file_path),
        encoding="utf-8"
    )

    documents.extend(
        loader.load()
    )


if not documents:

    raise ValueError(
        "No knowledge documents found."
    )


print(
    f"Loaded {len(documents)} document(s)"
)


# ==================================================
# SPLIT DOCUMENTS
# ==================================================

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150
)

chunks = text_splitter.split_documents(
    documents
)


print(
    f"Created {len(chunks)} chunks"
)


# ==================================================
# EMBEDDING MODEL
# ==================================================

print(
    "Loading embedding model..."
)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ==================================================
# CREATE CHROMA DATABASE
# ==================================================

CHROMA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


print(
    "Creating ChromaDB..."
)


vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=str(CHROMA_DIR),
    collection_name="devops_knowledge"
)


print(
    "RAG knowledge base created successfully!"
)

print(
    f"Stored at: {CHROMA_DIR}"
)