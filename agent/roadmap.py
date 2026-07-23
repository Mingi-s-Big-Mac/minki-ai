from functools import lru_cache

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from core.config import get_settings
from core.llm import get_llm
from rag.retriever import get_retriever


class RoadmapStep(BaseModel):
    period: str = Field(description="기간 (예: '2학년 2학기', '졸업 후 1년차')")
    tasks: list[str] = Field(description="이 기간에 수행할 구체적인 학습/활동 목록")
    certifications: list[str] = Field(description="취득 목표 자격증 (없으면 빈 리스트)")
    skills: list[str] = Field(description="이 기간에 습득·강화할 기술 스킬 (없으면 빈 리스트)")
    source: str = Field(description="참고 출처 (예: 'NCS 학습모듈 — 응용SW엔지니어링', '워크넷 채용동향')")


class RoadmapOutput(BaseModel):
    timeline: list[RoadmapStep] = Field(description="현재 학년부터 취업까지 순서대로 나열된 진로 로드맵")


_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "당신은 진로 로드맵 전문가입니다. "
        "사용자의 프로필과 직업 데이터를 바탕으로 실현 가능한 단계별 진로 로드맵을 작성하세요.",
    ),
    (
        "human",
        """[사용자 프로필]
- 현재 학년: {grade}
- 전공: {major}
- 관심 직무: {job}
- 보유 스킬: {skills}

[관련 직업 정보]
{context}

현재 학년부터 취업까지 학기/연도 단위의 현실적인 진로 로드맵을 작성해주세요.""",
    ),
])


@lru_cache(maxsize=1)
def _build_resources():
    settings = get_settings()
    llm = get_llm(settings.roadmap_model, temperature=0.2).with_structured_output(RoadmapOutput)
    retriever = get_retriever(k=5)
    return _PROMPT | llm, retriever


def generate_roadmap(grade: str, major: str, job: str, skills: list[str]) -> RoadmapOutput:
    chain, retriever = _build_resources()

    docs = retriever.invoke(f"{major} {job} 진로 준비 방법 자격증")
    context = "\n\n".join(
        f"[{d.metadata['job_name']} / {d.metadata['category']}]\n{d.page_content[:600]}"
        for d in docs
    )

    return chain.invoke({
        "grade": grade,
        "major": major,
        "job": job,
        "skills": ", ".join(skills) if skills else "없음",
        "context": context,
    })
