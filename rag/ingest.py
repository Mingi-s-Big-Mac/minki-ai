import json
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from core.llm import get_embeddings

COLLECTION_NAME = "jobs"
DB_PATH = str(Path(__file__).parent.parent / "chroma_db")
DATA_PATH = Path(__file__).parent.parent / "data" / "jobs_rag_text.jsonl"


def ingest():
    jobs = [
        json.loads(line)
        for line in DATA_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    docs = [
        Document(
            page_content=job["text"],
            metadata={"job_id": job["job_id"], "job_name": job["job_name"], "category": job["category"]},
        )
        for job in jobs
    ]

    Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        collection_name=COLLECTION_NAME,
        persist_directory=DB_PATH,
    )

    print(f"적재 완료: {len(docs)}개 직업")


if __name__ == "__main__":
    ingest()
