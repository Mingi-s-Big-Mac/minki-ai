# minki-ai — 진로 상담 AI 서비스

학생의 진로 고민을 실제 공공 직업 데이터에 근거해 상담하고, 학기 단위 진로 로드맵을 자동 생성하는 **RAG 기반 AI API 서버**입니다. Amazon Bedrock(Claude) + Titan 임베딩 + ChromaDB 벡터 검색으로 구현되어 있으며, FastAPI로 HTTP API를 제공합니다.

이 저장소는 더 큰 진로 지원 웹 서비스(로그인·대시보드·진로검색·직무비교 등, `FRS.md` 참고)의 **AI 파트**에 해당합니다.

---

## 1. 기술 스택

| 구분 | 사용 기술 |
|------|-----------|
| 언어/런타임 | Python >= 3.13 |
| 패키지 관리 | uv (`pyproject.toml`, `uv.lock`) |
| API 서버 | FastAPI (+ uvicorn) |
| 에이전트 | LangGraph (툴 호출형 대화 그래프) |
| LLM 프레임워크 | LangChain |
| LLM / 임베딩 | Amazon Bedrock — Claude(추론 프로필), Titan Embeddings v2 |
| 벡터 DB | ChromaDB (`langchain-chroma`) |
| 설정 관리 | pydantic-settings, python-dotenv |

---

## 2. 디렉터리 구조 및 파일별 역할

```
minki-ai/
├── api/                 # HTTP API 계층
│   ├── main.py          # FastAPI 앱 생성 + API 키 인증 미들웨어
│   ├── routes.py        # 엔드포인트 (/chat, /chat/sessions, /roadmap)
│   └── schemas.py       # 요청/응답 Pydantic 모델
├── agent/               # AI 에이전트 로직
│   ├── chat.py          # LangGraph 기반 진로 상담 챗봇 (툴 호출 + 세션 메모리)
│   ├── roadmap.py       # 진로 로드맵 구조화 생성 (structured output + RAG)
│   ├── tools.py         # search_jobs 툴 (RAG 검색을 LLM 툴로 노출)
│   └── guardrails.py    # 입력 검증 (프롬프트 인젝션/무관 질문 차단)
├── core/                # 공통 인프라
│   ├── config.py        # 환경설정 (모델명, AWS, API 키 등)
│   └── llm.py           # LLM/임베딩 팩토리 (Bedrock 연결)
├── rag/                 # 검색 증강 생성(RAG)
│   ├── ingest.py        # 직업 데이터 → 임베딩 → ChromaDB 적재
│   └── retriever.py     # ChromaDB 벡터 검색기
├── data/
│   └── jobs_rag_text.jsonl   # 직업 데이터 600건 (RAG 원천 데이터)
├── main.py              # 스텁 진입점 (실제 서버는 api.main:app 사용)
├── pyproject.toml       # 의존성 정의
├── .env.example         # 환경변수 템플릿
├── .github/workflows/ci.yml  # CI (상위 모노레포용, 아래 참고)
├── FRS.md               # 전체 서비스 기능 요구사항 명세
├── claude.md            # LLM 코딩 가이드라인
└── HANDOFF.md           # 백엔드 연동용 API 명세
```

### 파일 상세

**api/main.py**
- FastAPI 앱을 만들고 `/api` prefix로 라우터를 등록.
- `api_key_auth` 미들웨어: `API_KEY`가 설정돼 있으면 `/api/*` 요청에 `X-API-Key` 헤더 일치를 요구(불일치 시 401). 미설정 시 인증 생략(로컬 개발용).
- 시작 시 `load_dotenv()`로 `.env` 로드.

**api/routes.py**
- `POST /api/chat`: 입력 가드레일 검증 → LangGraph 에이전트 호출 → 답변 + 출처(sources) 반환. `conversation_id`별 세션 메타데이터를 메모리에 유지.
- `GET /api/chat/sessions`: 세션 목록(최근 활동순).
- `DELETE /api/chat/sessions/{conversation_id}`: 세션 삭제.
- `POST /api/roadmap`: 프로필(학년/전공/직무/스킬) 기반 로드맵 생성.

**api/schemas.py**
- `ChatRequest/ChatResponse`, `Source`, `SessionInfo`, `RoadmapRequest/RoadmapResponse` 등 요청·응답 스키마 정의.

**agent/chat.py**
- LangGraph `StateGraph`로 "에이전트 ↔ 툴" 순환 그래프 구성.
- `search_jobs` 툴을 바인딩해 실제 직업 데이터를 근거로 답변.
- 보안 지침이 포함된 시스템 프롬프트 사용, 사용자 입력을 `[사용자 질문]` 태그로 감싸 데이터로만 취급.
- `MemorySaver`로 `thread_id`(=conversation_id)별 대화 맥락 유지.

**agent/roadmap.py**
- `RoadmapStep`/`RoadmapOutput` Pydantic 스키마로 **구조화 출력**(`with_structured_output`).
- 리트리버로 관련 직업 정보를 검색해 프롬프트 컨텍스트로 주입.
- 반환: 기간별 `tasks`, `certifications`, `skills`, `source` 목록.

**agent/tools.py**
- `@tool search_jobs(query)`: 리트리버로 직업 정보를 검색해 텍스트로 반환. LLM이 필요 시 호출.

**agent/guardrails.py**
- `validate_input(text)` → `(is_safe, reason)`.
- 입력 길이 제한(1000자), 영어/한국어 프롬프트 인젝션·탈옥 패턴 정규식 차단.

**core/config.py**
- `pydantic-settings` 기반 `Settings`. `.env`에서 로드, 미정의 키는 무시(`extra="ignore"`).
- 주요 값: `chat_model`, `roadmap_model`, `embedding_model`, `aws_region`, AWS 자격증명, `api_key`.

**core/llm.py**
- `get_llm(model, temperature)`: provider에 따라 LLM 생성. **Bedrock 사용 시 `ChatBedrockConverse`**.
- `get_embeddings()`: **Bedrock 사용 시 `BedrockEmbeddings`(Titan)**.
- `_bedrock_credentials()`: `.env`에 키가 있으면 사용, 없으면 boto3 기본 체인(EC2 IAM 역할 등).

**rag/ingest.py**
- `data/jobs_rag_text.jsonl`을 읽어 Document로 변환 → 임베딩 → `chroma_db/`에 적재. (직업 600건)
- 실행: `python -m rag.ingest`

**rag/retriever.py**
- `chroma_db/`를 로드해 벡터 검색기(`as_retriever`)를 제공. `lru_cache`로 단일 인스턴스 유지.

**data/jobs_rag_text.jsonl**
- RAG 원천 데이터. 각 줄은 `{job_id, job_name, category, text}` 형태(연봉·하는 일·준비 방법 등 포함).

---

## 3. 동작 흐름

**채팅 (`POST /api/chat`)**
```
요청 → 가드레일 검증 → LangGraph 에이전트
     → (필요 시) search_jobs 툴로 ChromaDB 검색
     → Bedrock Claude가 근거 기반 답변 생성
     → 답변 + 출처(sources) 반환
```

**로드맵 (`POST /api/roadmap`)**
```
프로필 입력 → 리트리버로 관련 직업 정보 검색
           → 프롬프트에 컨텍스트 주입
           → Bedrock Claude가 구조화된 타임라인(JSON) 생성
```

---

## 4. 환경변수 (`.env`)

| 변수 | 설명 | 예시 |
|------|------|------|
| `CHAT_MODEL` | 채팅용 Bedrock 모델 | `eu.anthropic.claude-haiku-4-5-20251001-v1:0` |
| `ROADMAP_MODEL` | 로드맵용 Bedrock 모델 | `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| `EMBEDDING_MODEL` | 임베딩 모델 | `amazon.titan-embed-text-v2:0` |
| `AWS_REGION` | Bedrock 리전 | `eu-central-1` |
| `AWS_ACCESS_KEY_ID` 등 | 자격증명(비우면 IAM 역할 사용) | (빈 값) |
| `API_KEY` | API 인증 키(비우면 인증 없음) | (비밀값) |

> eu-central-1 에서는 Claude 계열이 **크로스리전 추론 프로필(`eu.` 접두사)** 형태로만 호출됩니다.

---

## 5. API 엔드포인트 요약

| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| POST | `/api/chat` | X-API-Key | 진로 상담 채팅 |
| GET | `/api/chat/sessions` | X-API-Key | 세션 목록 |
| DELETE | `/api/chat/sessions/{id}` | X-API-Key | 세션 삭제 |
| POST | `/api/roadmap` | X-API-Key | 진로 로드맵 생성 |

에러: 400(가드레일 차단), 401(키 불일치), 404(세션 없음), 422(바디 형식 오류).
자세한 요청/응답 스키마는 `HANDOFF.md` 참고.

---

## 6. 로컬 실행

```bash
uv sync                       # 의존성 설치
cp .env.example .env          # 환경변수 설정 (AWS 자격증명/모델)
python -m rag.ingest          # 최초 1회 벡터 DB 구축
uv run uvicorn api.main:app --reload   # 개발 서버
```

> RAG 데이터를 바꾸면 `python -m rag.ingest`로 재인덱싱이 필요합니다(임베딩 모델이 바뀌어도 재인덱싱 필요).

---

## 7. 배포 (현재 운영 상태)

- **환경**: AWS EC2 (eu-central-1), Ubuntu, 인스턴스 IAM 역할 `gsm-ec2-role`로 Bedrock 호출.
- **실행**: `systemd` 서비스 `minki-ai` — uvicorn을 `0.0.0.0:8000`에 바인딩, 부팅 자동 시작·크래시 자동 재시작.
- **인증**: `API_KEY` 설정으로 `/api/*` 보호.
- 관리 명령: `sudo systemctl status|restart minki-ai`, 로그 `sudo journalctl -u minki-ai -f`.

---

## 8. 알아둘 점 / 개선 여지

- **의존성 정리됨**: Bedrock 전환으로 `langchain-anthropic`, `langchain-ollama`, `langchain-huggingface`, `sentence-transformers`는 `pyproject.toml`에서 제거됨. 단, `core/config.py`·`core/llm.py`에는 아직 ollama/anthropic/huggingface 분기 코드가 lazy import로 남아 있습니다(Bedrock만 쓰면 실행되지 않음). 완전 정리하려면 해당 분기 제거 가능.
- **CI 불일치**: `.github/workflows/ci.yml`은 `auth-service`, `dashboard-service`, `ai-service`, `llm-server` 등 상위 모노레포의 여러 서비스 경로를 대상으로 하며, 이 단독 저장소 구조와 맞지 않습니다(테스트 디렉터리 부재). 이 저장소 기준으로 재작성 필요.
- **보안**: 현재 평문 HTTP + 보안그룹 전체 공개. 운영 시 HTTPS 적용과 보안그룹 IP 제한 권장.
- **퍼블릭 IP**: 자동할당 IP는 인스턴스 재시작 시 변경될 수 있음 → **Elastic IP 고정** 권장.
- **세션 저장**: 대화 세션은 프로세스 메모리(`MemorySaver`, `_sessions` dict)에 저장 → 서버 재시작 시 초기화됨. 영속화가 필요하면 외부 저장소 연동 필요.
