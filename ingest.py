
from pathlib import Path

import yaml
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


ROOT = Path(__file__).resolve().parent


def read_yaml(filename):
    """Read a YAML configuration file."""
    path = ROOT / "config" / filename

    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_documents(folder):
    """Load supported documents recursively."""
    documents = []

    loaders = {
        ".pdf": PyMuPDFLoader,
        ".docx": Docx2txtLoader,
        ".txt": TextLoader,
    }

    folder = Path(folder)

    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue

        extension = path.suffix.lower()
        loader_class = loaders.get(extension)

        if loader_class is None:
            continue

        print(f"Loading: {path.name}")

        if extension == ".txt":
            loader = loader_class(
                str(path),
                encoding="utf-8",
            )
        else:
            loader = loader_class(str(path))

        loaded_docs = loader.load()

        for doc in loaded_docs:
            doc.metadata["source"] = path.name
            doc.metadata["file_type"] = extension[1:]

        documents.extend(loaded_docs)

    return documents


def build_index():
    """Load, split, embed, and index enterprise documents."""

    embedding_cfg = read_yaml("embedding_config.yaml")
    retrieval_cfg = read_yaml("retrieval_config.yaml")

    documents = load_documents(ROOT / "documents")

    if not documents:
        raise RuntimeError(
            "No PDF, DOCX, or TXT documents found in documents/."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=int(retrieval_cfg["chunk_size"]),
        chunk_overlap=int(retrieval_cfg["chunk_overlap"]),
        add_start_index=True,
    )

    chunks = splitter.split_documents(documents)

    if not chunks:
        raise RuntimeError("No chunks were generated.")

    print(f"Documents/pages loaded: {len(documents)}")
    print(f"Chunks generated: {len(chunks)}")
    print("Loading embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name=embedding_cfg["embedding_model"]
    )

    persist_directory = (
        ROOT / embedding_cfg["persist_directory"]
    ).resolve()

    persist_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    db = Chroma(
        collection_name=embedding_cfg["collection_name"],
        persist_directory=str(persist_directory),
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine"},
    )

    # Clean rebuild for this local capstone demo.
    existing_ids = db.get()["ids"]

    if existing_ids:
        db.delete(ids=existing_ids)

    db.add_documents(chunks)

    print("\nINDEXING SUCCESSFUL")
    print(f"Documents/pages loaded: {len(documents)}")
    print(f"Chunks indexed: {len(chunks)}")
    print(f"Database: {persist_directory}")


if __name__ == "__main__":
    build_index()
