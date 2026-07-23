import re

_INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above|prior)\s+instructions?",
    r"forget\s+(previous|all|above|your)\s+instructions?",
    r"disregard\s+(previous|all|above|your)\s+instructions?",
    r"(override|bypass|jailbreak)\s+(your|the|all)?\s*(instructions?|rules?|safety|restrictions?)",
    r"you\s+are\s+now\s+(a|an|the)\s+",
    r"new\s+(role|persona|instructions?|system\s+prompt)",
    r"pretend\s+(you\s+are|to\s+be)",
    r"act\s+as\s+(if\s+you\s+are|a|an)\s+",
    r"\bDAN\b",
    r"do\s+anything\s+now",
    r"system\s*prompt\s*(is|=|:|override)",
    r"<\s*(system|instructions?|prompt)\s*>",
    r"\[system\]",
    r"###\s*system",
    # --- 한국어 프롬프트 인젝션 / 탈옥 패턴 ---
    # "(이전/위/모든/기존) 지시/명령/규칙/프롬프트 ... 무시/잊어/무효화"
    r"(이전|위|앞|모든|기존|상단)\s*(의)?\s*(지시|명령|규칙|프롬프트|지침).{0,8}(무시|잊어|무효|해제)",
    # 순서가 반대인 경우: "무시하고 ... 지시/프롬프트"
    r"(무시|잊어버려|잊어|무효화|해제)\s*(하고|하라|해라|해|하세요|해줘)?.{0,8}(지시|명령|규칙|프롬프트|지침)",
    # "시스템 프롬프트 무시/변경/바꿔/잊어/해제/우회"
    r"시스템\s*프롬프트.{0,10}(무시|변경|바꿔|바꾸|잊|해제|우회|알려|출력|보여)",
    # 역할/페르소나 변경 요구
    r"(역할|페르소나).{0,8}(바꿔|바꾸|변경|잊|해제)",
    r"너는\s*이제",
    r"(인|처럼|척).{0,3}(행동|굴어|말해|대답|응답)\s*(해|하라|해라|하세요|해줘)",
    # 탈옥 / 제한 해제 / 개발자 모드
    r"탈옥",
    r"개발자\s*모드",
    r"제한\s*(을|를)?\s*(해제|풀어|없애|무시|무효)",
    r"(안전|보안)\s*(장치|규칙|지침)?\s*(을|를)?\s*(무시|해제|우회|끄)",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]

MAX_INPUT_LENGTH = 1000


def validate_input(text: str) -> tuple[bool, str]:
    """(is_safe, reason) 반환. is_safe=False 이면 요청을 거부해야 합니다."""
    if len(text) > MAX_INPUT_LENGTH:
        return False, f"입력은 {MAX_INPUT_LENGTH}자 이내여야 합니다."
    if any(pat.search(text) for pat in _compiled):
        return False, "허용되지 않는 입력입니다. 진로 관련 질문을 입력해 주세요."
    return True, ""
