# 진로 AI API 연동 명세 (백엔드 전달용)

> 다른 VPC / 다른 EC2의 백엔드에서 이 AI 서버를 호출하기 위한 연동 문서입니다.
> AI 서버는 퍼블릭 IP로 공개되어 있어, VPC 경계와 무관하게 인터넷을 통해 서버-투-서버로 호출합니다.

## 1. 접속 정보

| 항목 | 값 |
|------|-----|
| Base URL | `http://3.78.183.100:8000` |
| 인증 헤더 | `X-API-Key: SytPVRCYywy7A8cmwEVR34-MYNVALI1vYSALza3A21w` |
| Content-Type | `application/json` |
| API 문서(Swagger) | `http://3.78.183.100:8000/docs` |

- `X-API-Key`는 `/api/*` 모든 경로에 필요합니다.
- Base URL과 API 키는 백엔드의 **환경변수/시크릿**으로 관리하세요. 코드나 깃에 하드코딩 금지.

```
AI_BASE_URL=http://3.78.183.100:8000
AI_API_KEY=SytPVRCYywy7A8cmwEVR34-MYNVALI1vYSALza3A21w
```

## 2. 엔드포인트

### POST `/api/chat` — 진로 상담 채팅
요청
```json
{ "conversation_id": "user-123", "message": "백엔드 개발자 연봉 알려줘" }
```
응답 (200)
```json
{
  "answer": "백엔드 개발자의 평균연봉은 ...",
  "sources": [
    { "id": 1, "title": "직업정보 — 백엔드개발자 (IT·정보통신)" }
  ]
}
```
- `conversation_id`: 대화 세션 키. **같은 값으로 계속 보내면 대화 맥락이 이어집니다**(서버가 세션별 히스토리를 메모리에 유지). 사용자/대화별 고유값 부여 권장.
- `sources`: 답변 근거로 사용된 직업정보 목록.
- 진로와 무관하거나 프롬프트 인젝션으로 판단된 입력은 **400**으로 거부됩니다.

### POST `/api/roadmap` — 진로 로드맵 생성
요청
```json
{ "grade": "2학년", "major": "컴퓨터공학", "job": "백엔드 개발자", "skills": ["Python", "Git"] }
```
응답 (200)
```json
{
  "timeline": [
    {
      "period": "2학년 2학기",
      "tasks": ["자료구조 심화 학습", "개인 프로젝트 진행"],
      "certifications": ["정보처리기사 필기"],
      "skills": ["SQL", "REST API"],
      "source": "NCS 학습모듈 — 응용SW엔지니어링"
    }
  ]
}
```
- `skills`는 생략 가능(기본값 `[]`).

### GET `/api/chat/sessions` — 세션 목록
```json
200 → [
  {
    "conversation_id": "user-123",
    "title": "백엔드 개발자 연봉...",
    "created_at": "2026-07-23T05:00:00",
    "last_active": "2026-07-23T05:10:00",
    "last_message": "정보처리기사 어떻게 준비해?"
  }
]
```

### DELETE `/api/chat/sessions/{conversation_id}` — 세션 삭제
```json
200 → {"ok": true}
404 → {"detail": "세션을 찾을 수 없습니다."}
```

## 3. 에러 코드

| 코드 | 의미 | 응답 예시 |
|------|------|-----------|
| 400 | 진로 무관/금지 입력 (가드레일 차단) | `{"detail":"허용되지 않는 입력입니다. 진로 관련 질문을 입력해 주세요."}` |
| 401 | API 키 없음/불일치 | `{"detail":"유효하지 않은 API 키입니다."}` |
| 404 | 세션 없음 | `{"detail":"세션을 찾을 수 없습니다."}` |
| 422 | 요청 바디 형식 오류(필드 누락 등) | FastAPI 기본 검증 응답 |

## 4. 호출 예시

### curl
```bash
curl -X POST http://3.78.183.100:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: SytPVRCYywy7A8cmwEVR34-MYNVALI1vYSALza3A21w" \
  -d '{"conversation_id":"user-123","message":"간호사 진로 알려줘"}'
```

### Node.js (axios)
```js
const { data } = await axios.post(
  `${process.env.AI_BASE_URL}/api/chat`,
  { conversation_id: userId, message: text },
  { headers: { "X-API-Key": process.env.AI_API_KEY }, timeout: 60000 }
);
// data.answer, data.sources
```

### Spring (WebClient)
```java
webClient.post()
  .uri(aiBaseUrl + "/api/chat")
  .header("X-API-Key", aiApiKey)
  .contentType(MediaType.APPLICATION_JSON)
  .bodyValue(Map.of("conversation_id", userId, "message", text))
  .retrieve()
  .bodyToMono(ChatResponse.class);
```

## 5. 백엔드가 알아둘 점

- **응답 지연**: LLM 호출이라 채팅·로드맵은 수 초 ~ 수십 초 소요될 수 있음 → **read timeout 60초 이상** 권장.
- **평문 HTTP**: 현재 HTTPS 미적용. 공용 인터넷을 지나가므로 필요 시 HTTPS(도메인 + Nginx/ALB) 적용 권장.
- **CORS 미설정**: 백엔드가 서버-사이드에서 호출하면 문제없음. **브라우저 프론트가 이 API를 직접 호출**할 경우 CORS 허용 설정 추가 필요.
- **보안그룹**: 현재 8000 포트가 전체 공개(`0.0.0.0/0`). 백엔드 EC2의 퍼블릭 IP가 확정되면 해당 IP만 허용으로 좁히면 더 안전.

## 6. 서버 정보 (참고)

| 항목 | 값 |
|------|-----|
| 인스턴스 | `i-0213beb80c24e9b2c` (eu-central-1) |
| 실행 방식 | systemd 서비스 `minki-ai` (부팅 시 자동 시작, 크래시 시 자동 재시작) |
| 포트 | `8000` |
| LLM | Amazon Bedrock — 채팅 `eu.anthropic.claude-haiku-4-5`, 로드맵 `eu.anthropic.claude-sonnet-4-5` |
| 임베딩 | Amazon Titan `amazon.titan-embed-text-v2:0` |
| 자격 증명 | EC2 IAM 역할 `gsm-ec2-role` (키 하드코딩 없음) |
