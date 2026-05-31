"""Vision tab helpers — presentation only; engine lives in modules/vision.py."""

from __future__ import annotations

import base64
from typing import Any

# 1×1 PNG (purple-ish pixel) for demo analysis without user upload
DEMO_IMAGE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

REPORT_TYPES = [
    "점자블록",
    "경사로",
    "출입구",
    "주차·주차장",
    "보행 장애물",
    "장애인 화장실",
    "안내표지",
    "기타",
]

OFFICIAL_NOTICE = (
    "본 결과는 접근성 점검 보조자료이며, 공식 판정 아님. "
    "법적 인증·행정처분·시설 적합 판정을 대체하지 않습니다."
)

FORBIDDEN_VISION_PRECISE = ("96.8%", "96.8", "단절 96")


def is_model_output(result: dict[str, Any]) -> bool:
    return str(result.get("source", "")) == "vision_model" and bool(result.get("ok"))


def result_source_badge(result: dict[str, Any]) -> str:
    if is_model_output(result):
        return "AI 모델 출력"
    return "예시(참고용)"


def qualitative_grade(result: dict[str, Any]) -> tuple[str, str]:
    """Return (grade label, css badge class) — text badge, not color-only."""
    if is_model_output(result):
        return ("관리자 확인 필요", "warn")

    level = str(result.get("risk_level", "중간"))
    mapping = {
        "높음": ("주의", "warn"),
        "중간": ("보통", "accent"),
        "낮음": ("양호", "ok"),
    }
    return mapping.get(level, ("보통", "accent"))


def risk_icon(grade: str) -> str:
    if grade == "주의":
        return "⚠"
    if grade == "양호":
        return "✓"
    return "◉"


def demo_scan_svg_markup(*, scanning: bool = False, show_demo_bbox: bool = False) -> str:
    scan_line = (
        '<line x1="0" y1="125" x2="500" y2="125" stroke="#b8acd8" stroke-width="2" '
        'stroke-dasharray="8 6" opacity="0.9"/>'
        if scanning
        else ""
    )
    bbox = ""
    if show_demo_bbox:
        bbox = (
            '<rect x="200" y="95" width="100" height="60" rx="12" fill="none" '
            'stroke="#7868a0" stroke-width="3" stroke-dasharray="6 4"/>'
            '<text x="250" y="88" text-anchor="middle" fill="#7868a0" font-size="11" font-weight="700">'
            "데모 연출 · 좌표 아님"
            "</text>"
            '<span></span>'
        )
    return f"""
    <svg viewBox="0 0 500 250" role="img" aria-label="접근성 점검 데모 미리보기 연출"
         style="width:100%;height:auto;border-radius:14px;">
      <rect width="500" height="250" fill="#f0ecf8"/>
      <rect x="55" y="110" width="58" height="58" rx="5" fill="#b8acd8"/>
      <rect x="130" y="110" width="58" height="58" rx="5" fill="#b8acd8"/>
      <rect x="205" y="110" width="58" height="58" rx="5" fill="none" stroke="#7868a0" stroke-width="3" stroke-dasharray="8 6"/>
      <rect x="330" y="110" width="58" height="58" rx="5" fill="#b8acd8"/>
      <rect x="405" y="110" width="58" height="58" rx="5" fill="#b8acd8"/>
      <text x="250" y="205" text-anchor="middle" fill="#7868a0" font-size="14">
        김포 반다비 1층 로비 점자블록 (데모 연출)
      </text>
      {scan_line}
      {bbox}
    </svg>
    """
