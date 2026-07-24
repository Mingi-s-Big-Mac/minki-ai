# minki-ai — 진로 상담 AI 서비스

학생의 진로 고민을 **실제 공공 직업 데이터**에 근거해 상담하고, 학기 단위 **진로 로드맵**을 자동 생성하는 RAG 기반 AI API 서버입니다. Amazon Bedrock(Claude) + Titan 임베딩 + ChromaDB 벡터 검색으로 구현했으며, FastAPI로 HTTP API를 제공합니다.

이 저장소는 진로 지원 웹 서비스(로그인·대시보드·진로검색·직무비교 등)의 **AI 파트**에 해당하며, 별도 백엔드(Express)와 서버-투-서버로 통신합니다.

---

## ✨ 주요 기능

- **진로 상담 챗봇** — 질문을 실제 직업 데이터에서 검색(RAG)해 연봉·직업만족도·필요 역량·준비 방법 등 **근거 있는 답변과 출처**를 제공. 대화 맥락 유지.
- **맞춤형 진로 로드맵** — 학년·전공·관심 직무·보유 스킬을 입력하면 취업까지 **학기별 단계 계획(학습·자격증·스킬)**을 자동 생성.
- **가드레일** — 프롬프트 인젝션·주제 이탈 입력을 차단해 진로 상담 목적에 맞는 답변만 제공(한국어/영어 패턴 대응).

---

## 🧱 기술 스택

| 구분 | 기술 |
|------|------|
| 언어/런타임 | Python >= 3.13 |
| 패키지 관리 | uv |
| API 서버 | FastAPI (+ uvicorn) |
| 에이전트 | LangGraph (툴 호출형 대화 그래프) |
| LLM 프레임워크 | LangChain |
| LLM / 임베딩 | Amazon Bedrock — Claude(추론 프로필), Titan Embeddings v2 |
| 벡터 DB | ChromaDB |
| 설정 관리 | pydantic-settings, python-dotenv |

---

## 🏗 아키텍처

```
[백엔드 EC2 · VPC-A]                       [AI 서버 EC2 · VPC-B (eu-central-1)]
 Express (Node.js)                          minki-ai (FastAPI, :8000)
   │ AI_BASE_URL / AI_API_KEY                 │ systemd 상시 실행
   └── POST + X-API-Key ────────────────────►├─ 가드레일 → LangGraph 에이전트 → RAG
                                              └─ Amazon Bedrock (Claude, Titan)
```

- 두 서버는 다른 VPC·다른 EC2. 하나의 compose로 합치지 않고 **공용 인터넷을 통한 서버-투-서버 HTTP**로 통신.
- Express는 AI 로직을 몰라도 되며 **HTTP 엔드포인트만 호출**.

---

## 📁 프로젝트 구조

```
minki-ai/
├── api/                 # HTTP API 계층
│   ├── main.py          # FastAPI 앱 + API 키 인증 미들웨어
│   ├── routes.py        # /chat, /chat/sessions, /roadmap
│   └── schemas.py       # 요청/응답 Pydantic 모델
├── agent/               # AI 에이전트
│   ├── chat.py          # LangGraph 챗봇 (툴 호출 + 세션 메모리)
│   ├── roadmap.py       # 로드맵 구조화 생성 (structured output + RAG)
│   ├── tools.py         # search_jobs 툴 (RAG 검색)
│   └── guardrails.py    # 입력 검증 (인젝션/무관 질문 차단)
├── core/
│   ├── config.py        # 환경설정 (모델, AWS, API 키, max_tokens)
│   └── llm.py           # Bedrock LLM/임베딩 팩토리
├── rag/
│   ├── ingest.py        # 직업 데이터 → 임베딩 → ChromaDB 적재
│   └── retriever.py     # ChromaDB 벡터 검색기
├── data/
│   └── jobs_rag_text.jsonl   # 직업 데이터 600건 (RAG 원천)
├── pyproject.toml
└── .env.example
```

---

## 🚀 로컬 실행

```bash
uv sync                                # 의존성 설치
cp .env.example .env                   # 환경변수 설정 (AWS 자격증명/모델)
python -m rag.ingest                   # 최초 1회 벡터 DB 구축
uv run uvicorn api.main:app --reload   # 개발 서버
```

> RAG 데이터를 바꾸면 `python -m rag.ingest`로 재인덱싱이 필요합니다.

### 환경변수 (`.env`)

| 변수 | 설명 | 예시 |
|------|------|------|
| `CHAT_MODEL` | 채팅용 Bedrock 모델 | `eu.anthropic.claude-haiku-4-5-20251001-v1:0` |
| `ROADMAP_MODEL` | 로드맵용 Bedrock 모델 | `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| `EMBEDDING_MODEL` | 임베딩 모델 | `amazon.titan-embed-text-v2:0` |
| `AWS_REGION` | Bedrock 리전 | `eu-central-1` |
| `MAX_TOKENS` | 응답 최대 출력 토큰 | `16384` |
| `AWS_ACCESS_KEY_ID` 등 | 자격증명(비우면 IAM 역할 사용) | (빈 값) |
| `API_KEY` | API 인증 키(비우면 인증 없음) | (비밀값) |

> eu-central-1에서는 Claude 계열이 **크로스리전 추론 프로필(`eu.` 접두사)**로만 호출됩니다.

---

## ☁️ 배포 (AWS EC2)

- **인프라**: EC2(Ubuntu, eu-central-1). 인스턴스에 IAM 역할 부착 → 키 하드코딩 없이 Bedrock 호출.
- **실행**: `systemd` 서비스 `minki-ai` — uvicorn을 `0.0.0.0:8000`에 바인딩, 부팅 자동 시작·크래시 자동 재시작.

### 배포 절차

```bash
# 1) 소스 전송 (예: scp/tar) 후 EC2에서
sudo apt-get install -y python3-venv
python3 -m venv .venv && . .venv/bin/activate
pip install boto3 langchain-aws langchain langchain-chroma chromadb \
            langgraph "fastapi[standard]" pydantic-settings python-dotenv

# 2) .env 작성 (모델/리전/API_KEY/MAX_TOKENS)
# 3) 벡터 DB 구축
python -m rag.ingest
```

### systemd 유닛 (`/etc/systemd/system/minki-ai.service`)

```ini
[Unit]
Description=minki-ai FastAPI server
After=network-online.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/minki-ai
ExecStart=/home/ubuntu/minki-ai/.venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now minki-ai      # 등록 + 시작
sudo systemctl status  minki-ai           # 상태
sudo systemctl restart minki-ai           # 코드/설정 변경 후 재시작
sudo journalctl -u minki-ai -f            # 실시간 로그
```

---

## 🔌 API 명세

Base URL: `http://<서버 주소>:8000` · 인증: `/api/*`에 헤더 `X-API-Key` 필요.

### `POST /api/chat` — 진로 상담 채팅
```json
// 요청
{ "conversation_id": "user-123", "message": "백엔드 개발자 연봉 알려줘" }
// 응답 (200)
{ "answer": "...", "sources": [ { "id": 1, "title": "직업정보 — 백엔드개발자 (IT·정보통신)" } ] }
```
- `conversation_id`: 같은 값으로 계속 보내면 대화 맥락 유지.

### `POST /api/roadmap` — 진로 로드맵 생성
```json
// 요청
{ "grade": "2학년", "major": "컴퓨터공학", "job": "백엔드 개발자", "skills": ["Python", "Git"] }
// 응답 (200)
{ "timeline": [ { "period": "...", "tasks": [...], "certifications": [...], "skills": [...], "source": "..." } ] }
```
- `skills` 생략 가능(기본 `[]`).

### 기타
- `GET /api/chat/sessions` — 세션 목록
- `DELETE /api/chat/sessions/{conversation_id}` — 세션 삭제

### 에러 코드

| 코드 | 의미 |
|------|------|
| 400 | 진로 무관/인젝션 입력 (가드레일 차단) |
| 401 | API 키 없음/불일치 |
| 404 | 세션 없음 |
| 422 | 요청 바디 형식 오류 |

---

## 🔗 Express 백엔드 연동

### 환경변수
```
AI_BASE_URL=http://<서버 주소>:8000
AI_API_KEY=<AI 서버 API 키>
```

### AI 클라이언트 (`aiClient.js`)
```js
const axios = require("axios");

const ai = axios.create({
  baseURL: process.env.AI_BASE_URL,
  headers: { "X-API-Key": process.env.AI_API_KEY },
  timeout: 90000, // LLM 응답 대기 (채팅 ~20초, 로드맵 ~35초)
});

async function chat(conversationId, message) {
  const { data } = await ai.post("/api/chat", { conversation_id: conversationId, message });
  return data; // { answer, sources }
}

async function roadmap(grade, major, job, skills = []) {
  const { data } = await ai.post("/api/roadmap", { grade, major, job, skills });
  return data; // { timeline: [...] }
}

module.exports = { chat, roadmap };
```

### Express 라우터 (`routes/ai.js`)
```js
const router = require("express").Router();
const aiClient = require("../aiClient");

router.post("/chat", async (req, res) => {
  try {
    const { conversationId, message } = req.body;
    res.json(await aiClient.chat(conversationId, message));
  } catch (err) {
    res.status(err.response?.status || 500).json({ error: err.response?.data || "AI 서버 오류" });
  }
});

module.exports = router;
```

### 통신 흐름
```
사용자 → Express (인증/세션 처리) → POST {AI_BASE_URL}/api/chat (X-API-Key)
      → AI 서버: 가드레일 → LangGraph → RAG 검색 → Bedrock 답변
      → Express ← { answer, sources } ← 사용자
```

> **타임아웃**: LLM 응답이 수십 초 걸리므로 HTTP 클라이언트 read timeout을 **60~90초**로 설정하세요.

---

## 🔒 보안 · 운영 참고

- **인증**: API 키(`X-API-Key`)로 백엔드만 호출 가능.
- **보안그룹**: 8000 인바운드를 백엔드 EC2 IP만 허용으로 제한 권장.
- **HTTPS**: 공용 인터넷 경유이므로 도메인 + TLS(Nginx/ALB) 적용 권장.
- **고정 IP**: 자동할당 퍼블릭 IP는 EC2 재시작 시 변경됨 → **Elastic IP 고정** 권장(변경 시 `AI_BASE_URL`도 갱신).
- **CORS**: Express 경유 시 불필요. 브라우저가 AI 서버를 직접 호출할 때만 CORS 설정 필요.
- **세션 저장**: 대화 세션은 프로세스 메모리에 저장 → 서버 재시작 시 초기화(영속화 필요 시 외부 저장소 연동).
