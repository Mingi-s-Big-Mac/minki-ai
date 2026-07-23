from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma

from core.llm import get_embeddings

COLLECTION_NAME = "jobs"
DB_PATH = str(Path(__file__).parent.parent / "chroma_db")


@lru_cache(maxsize=1)
def _get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=DB_PATH,
    )


def get_retriever(k: int = 3):
    return _get_vectorstore().as_retriever(search_kwargs={"k": k})
