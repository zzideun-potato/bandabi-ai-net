"""Static HTML fragments aligned with bandabi_purple (4).html — presentation only."""

from __future__ import annotations

import html


def brand_logo_markup(*, size: int = 48) -> str:
    radius = max(12, size // 3)
    return f"""
    <div class="bandabi-brand-logo" style="width:{size}px;height:{size}px;border-radius:{radius}px;" aria-hidden="true">
      <svg viewBox="0 0 138 138" width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="반다비 로고">
        <rect width="138" height="138" rx="20" fill="#4a2d7a"/>
        <path d="M63.75 78.2188V54.7812H68.125V78.2188H63.75ZM79.0625 85.25H72.5V47.75H79.0625V85.25ZM107.5 85.25H100.938V47.75H107.5V85.25Z" fill="white"/>
      </svg>
    </div>
    """


def route_map_svg(*, title: str) -> str:
    safe_title = html.escape(title)
    return f"""
    <div class="bandabi-route-map">
      <svg viewBox="0 0 860 310" role="img" aria-label="추천 경로 데모 지도" style="width:100%;height:auto;">
        <defs>
          <linearGradient id="bandabiRouteGrad" x1="0" x2="1">
            <stop offset="0%" stop-color="#b8acd8"/>
            <stop offset="100%" stop-color="#6b4fa0"/>
          </linearGradient>
        </defs>
        <rect width="860" height="310" rx="24" fill="#f0ecf8"/>
        <path d="M100 205 C205 205, 235 125, 345 125 S 520 195, 625 180 S 730 105, 790 105"
              fill="none" stroke="rgba(184,172,216,.45)" stroke-width="28" stroke-linecap="round"/>
        <path class="bandabi-route-line" d="M100 205 C205 205, 235 125, 345 125 S 520 195, 625 180 S 730 105, 790 105"
              fill="none" stroke="url(#bandabiRouteGrad)" stroke-width="10" stroke-linecap="round"/>
        <circle cx="90" cy="205" r="24" fill="#f0ecf8" stroke="#7868a0" stroke-width="3"/>
        <circle cx="340" cy="125" r="24" fill="#f0ecf8" stroke="#7868a0" stroke-width="3"/>
        <circle cx="625" cy="180" r="24" fill="#f0ecf8" stroke="#7868a0" stroke-width="3"/>
        <circle cx="790" cy="105" r="24" fill="#f0ecf8" stroke="#4a2d7a" stroke-width="3"/>
        <text x="90" y="211" text-anchor="middle" fill="#4a2d7a" font-size="13" font-weight="700">출발</text>
        <text x="340" y="131" text-anchor="middle" fill="#4a2d7a" font-size="13" font-weight="700">탑승</text>
        <text x="625" y="186" text-anchor="middle" fill="#4a2d7a" font-size="13" font-weight="700">하차</text>
        <text x="790" y="111" text-anchor="middle" fill="#4a2d7a" font-size="13" font-weight="700">센터</text>
        <text x="430" y="52" text-anchor="middle" fill="#7868a0" font-size="13">참고 경로 연출 · 실제 경로와 다를 수 있음</text>
        <text x="430" y="290" text-anchor="middle" fill="#7868a0" font-size="14">{safe_title}</text>
      </svg>
    </div>
    """
