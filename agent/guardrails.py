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
