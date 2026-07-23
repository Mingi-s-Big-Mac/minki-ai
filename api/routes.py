import re
from datetime import datetime

from fastapi import APIRouter, HTTPException
from langchain_core.messages import ToolMessage

from agent.chat import get_chat_agent
from agent.guardrails import validate_input
from agent.roadmap import generate_roadmap
from api.schemas import (
    ChatRequest,
    ChatResponse,
    RoadmapRequest,
    RoadmapResponse,
    SessionInfo,
    Source,
)

router = APIRouter()

_sessions: dict[str, dict] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    is_safe, reason = validate_input(req.message)
    if not is_safe:
        raise HTTPException(status_code=400, detail=reason)

    agent = get_chat_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": req.message}]},
        config={"configurable": {"thread_id": req.conversation_id}},
    )

    messages = result["messages"]

    # 최종 답변 추출
    last_content = messages[-1].content
    answer = (
        last_content
        if isinstance(last_content, str)
        else "".join(b.get("text", "") for b in last_content if isinstance(b, dict))
    )

    # 현재 턴의 출처만 추출 (마지막 HumanMessage 이후 ToolMessage 파싱)
    last_human_idx = max(i for i, m in enumerate(messages) if m.type == "human")
    sources: list[Source] = []
    seen: set[str] = set()
    for msg in messages[last_human_idx + 1:]:
        if isinstance(msg, ToolMessage):
            for job_name, category in re.findall(
                r"\[직업: (.+?) / 분야: (.+?)\]", msg.content
            ):
                if job_name not in seen:
                    seen.add(job_name)
                    sources.append(
                        Source(
                            id=len(sources) + 1,
                            title=f"직업정보 — {job_name} ({category})",
                        )
                    )

    # 세션 메타데이터 갱신
    now = datetime.now().isoformat()
    if req.conversation_id not in _sessions:
        _sessions[req.conversation_id] = {
            "conversation_id": req.conversation_id,
            "title": req.message[:30] + ("..." if len(req.message) > 30 else ""),
            "created_at": now,
        }
    _sessions[req.conversation_id]["last_active"] = now
    _sessions[req.conversation_id]["last_message"] = req.message[:50]

    return ChatResponse(answer=answer, sources=sources)


@router.get("/chat/sessions", response_model=list[SessionInfo])
async def list_sessions():
    return sorted(_sessions.values(), key=lambda x: x["last_active"], reverse=True)


@router.delete("/chat/sessions/{conversation_id}")
async def delete_session(conversation_id: str):
    if conversation_id not in _sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    _sessions.pop(conversation_id)
    return {"ok": True}


@router.post("/roadmap", response_model=RoadmapResponse)
async def roadmap(req: RoadmapRequest):
    result = generate_roadmap(
        grade=req.grade,
        major=req.major,
        job=req.job,
        skills=req.skills,
    )
    return RoadmapResponse(timeline=result.timeline)
