from pydantic import BaseModel

from agent.roadmap import RoadmapStep


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


class Source(BaseModel):
    id: int
    title: str  # e.g. "직업정보 — 소프트웨어개발자 (IT·정보통신)"


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


class SessionInfo(BaseModel):
    conversation_id: str
    title: str
    created_at: str
    last_active: str
    last_message: str


class RoadmapRequest(BaseModel):
    grade: str
    major: str
    job: str
    skills: list[str] = []


class RoadmapResponse(BaseModel):
    timeline: list[RoadmapStep]
