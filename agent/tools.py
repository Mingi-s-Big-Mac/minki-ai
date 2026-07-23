from langchain_core.tools import tool

from rag.retriever import get_retriever


@tool
def search_jobs(query: str) -> str:
    """진로 관련 직업 정보를 검색합니다. 직업명, 하는 일, 연봉, 준비 방법, 전망 등을 찾을 때 사용하세요."""
    docs = get_retriever(k=4).invoke(query)
    parts = [
        f"[직업: {doc.metadata['job_name']} / 분야: {doc.metadata['category']}]\n{doc.page_content}"
        for doc in docs
    ]
    return "\n\n---\n\n".join(parts)
