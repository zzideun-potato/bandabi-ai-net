"""Safety wording for public pilot-service output."""

from __future__ import annotations

FORBIDDEN_PHRASES = [
    "자동 배차",
    "배차 완료",
    "배차 확정",
    "차량 호출 완료",
    "예약 확정",
    "민원 자동 접수 완료",
    "공식 민원 접수 완료",
    "행정처분 근거",
    "위반 확정",
    "행정처분 요청 완료",
    "공식 접수 완료",
    "의료 진단",
    "의료 판단",
    "의학적 판단",
    "의료",
    "재활치료",
    "재활",
    "처방",
    "치료",
    "재활 처방",
    "운동 처방",
    "치료 효과",
]

SAFE_REPLACEMENTS = {
    "자동 배차": "이동지원 후보 추천",
    "배차 완료": "운영기관 검토 필요",
    "배차 확정": "운영기관 검토 필요",
    "차량 호출 완료": "이동지원 요청 후보 등록",
    "예약 확정": "이용 가능 여부 확인 필요",
    "민원 자동 접수 완료": "관리자 검증용 공문 초안 생성",
    "공식 민원 접수 완료": "관리자 검증 후 공식 절차 확인 필요",
    "행정처분 근거": "담당 부서 확인 참고자료",
    "위반 확정": "관리자 확인 필요",
    "행정처분 요청 완료": "담당 부서 검토 요청 초안",
    "공식 접수 완료": "공식 절차 확인 필요",
    "의료 진단": "참고 분석 결과",
    "의료 판단": "건강 관련 최종 결정",
    "의학적 판단": "건강 관련 최종 결정",
    "의료": "건강 관련",
    "재활치료": "생활체육 참여 지원",
    "재활": "생활체육",
    "처방": "가이드",
    "치료": "생활체육 참여 지원",
    "재활 처방": "생활체육 추천",
    "운동 처방": "생활체육 가이드",
    "치료 효과": "참여 변화 지표",
}

GENERAL_DISCLAIMER = (
    "이 서비스는 공공데이터와 내부 문서 기반 참고 정보만 제공합니다. "
    "실제 이동지원 실행이나 이용 가능 여부 결정을 의미하지 않으며, 건강 관련 최종 결정을 제공하지 않습니다. "
    "AI 검출 결과는 공식 민원 또는 행정처분 자료가 아니며, 현장 상태와 다를 수 있습니다."
)

MOBILITY_DISCLAIMER = (
    "이동지원 관련 결과는 후보 추천과 운영기관 검토 참고용입니다. "
    "실제 이동지원 실행이나 이용 가능 여부 결정을 의미하지 않으며, 건강 관련 최종 결정을 제공하지 않습니다. "
    "AI 검출 결과는 공식 민원 또는 행정처분 자료가 아니며, 공공데이터 기반 참고 정보는 현장 상태와 다를 수 있습니다."
)

SPORTS_DISCLAIMER = (
    "생활체육 관련 결과는 참여 검토를 돕는 참고 정보입니다. "
    "실제 이동지원 실행이나 이용 가능 여부 결정을 의미하지 않으며, 건강 관련 최종 결정을 제공하지 않습니다. "
    "AI 검출 결과는 공식 민원 또는 행정처분 자료가 아니며, 공공데이터 기반 참고 정보는 현장 상태와 다를 수 있습니다."
)

VISION_DISCLAIMER = (
    "이미지 기반 검출은 현장 확인을 보조하는 참고 정보입니다. "
    "실제 이동지원 실행이나 이용 가능 여부 결정을 의미하지 않으며, 건강 관련 최종 결정을 제공하지 않습니다. "
    "AI 검출 결과는 공식 민원 또는 행정처분 자료가 아니며, 공공데이터 기반 참고 정보는 현장 상태와 다를 수 있습니다."
)

SERVICE_DISCLAIMER = GENERAL_DISCLAIMER
MOBILITY_NOTICE = MOBILITY_DISCLAIMER
SPORTS_NOTICE = SPORTS_DISCLAIMER
VISION_NOTICE = VISION_DISCLAIMER
DATA_FALLBACK_NOTICE = "문서, CSV, references 폴더가 없거나 읽기 실패 상태여도 앱 실행은 유지됩니다."


def sanitize_public_claims(text: str) -> str:
    """Replace prohibited public-service claims with safer pilot-service wording."""
    sanitized = text or ""
    for forbidden in sorted(SAFE_REPLACEMENTS, key=len, reverse=True):
        sanitized = sanitized.replace(forbidden, SAFE_REPLACEMENTS[forbidden])
    return sanitized


def get_disclaimer(kind: str = "general") -> str:
    disclaimers = {
        "mobility": MOBILITY_DISCLAIMER,
        "sports": SPORTS_DISCLAIMER,
        "vision": VISION_DISCLAIMER,
        "general": GENERAL_DISCLAIMER,
    }
    return disclaimers.get((kind or "general").lower(), GENERAL_DISCLAIMER)


def find_forbidden_phrases(text: str) -> list[str]:
    source = text or ""
    return [phrase for phrase in FORBIDDEN_PHRASES if phrase in source]


def sanitize_service_text(text: str) -> str:
    """Backward-compatible alias for earlier modules."""
    return sanitize_public_claims(text)
