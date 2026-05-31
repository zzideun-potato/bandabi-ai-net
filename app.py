"""Streamlit iframe shell with server-side Python engine data injection."""

from __future__ import annotations

import json
import logging
import os
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

logger = logging.getLogger("bandabi.server_data")

STATUS_LABELS = {
    "configured": "연결 설정됨",
    "missing": "미설정",
    "real_csv": "CSV 로드됨",
    "read_error": "CSV 읽기 오류",
    "mock_fallback": "대체 응답 사용",
    "real_docs": "문서 준비됨",
    "empty_docs": "문서 없음",
    "ready": "준비됨",
    "fallback": "대체 응답",
    "bm25": "BM25 검색",
    "keyword_fallback": "키워드 검색",
    "disabled": "비활성",
    "missing_config": "설정 미완료",
    "enabled_ready": "발송 준비(미실행)",
    "missing_key": "API Key 미설정",
    "missing_model": "모델 미설정",
    "no_data": "데이터 없음",
}

JS_GRADE_MAP = {
    "이동 가능": "원활",
    "주의": "주의",
    "지원 필요": "지원 권장",
    "확인 불가": "대체 경로 권장",
}

DISABILITY_SCORING_INPUTS = {
    "physical": {
        "accessibility_support_type": "보행 보조",
        "mobility_support_needed": True,
        "companion_needed": False,
        "weather_enabled": True,
        "public_transport_available": True,
        "destination": "김포 반다비체육센터",
    },
    "visual": {
        "accessibility_support_type": "시각",
        "mobility_support_needed": False,
        "companion_needed": True,
        "weather_enabled": True,
        "public_transport_available": True,
        "destination": "김포 반다비체육센터",
    },
    "developmental": {
        "accessibility_support_type": "발달",
        "mobility_support_needed": True,
        "companion_needed": True,
        "weather_enabled": False,
        "public_transport_available": True,
        "destination": "김포 반다비체육센터",
    },
    "senior": {
        "accessibility_support_type": "고령",
        "mobility_support_needed": True,
        "companion_needed": False,
        "weather_enabled": True,
        "public_transport_available": True,
        "destination": "김포 반다비체육센터",
    },
}

RAG_SAMPLE_QUERIES = [
    "김포 반다비 생활체육 다음 참여 가이드",
    "교통약자 이동지원",
]

ROUTE_CACHE_SPECS: list[tuple[str, str, str]] = [
    ("김포 구래역 1번 출구", "김포 반다비체육센터", "physical"),
    ("김포 구래역 1번 출구", "김포 반다비체육센터", "visual"),
    ("김포 구래역 1번 출구", "김포 반다비체육센터", "developmental"),
    ("김포 구래역 1번 출구", "김포 반다비체육센터", "senior"),
    ("성남역", "김포 반다비체육센터", "physical"),
]


def _resolve_api_base() -> str:
    """Public FastAPI URL from Streamlit secrets / env (empty on Cloud if not deployed)."""
    try:
        from modules.config import get_secret

        raw = str(get_secret("BACKEND_API_URL", "") or "").strip().rstrip("/")
        return raw
    except Exception:
        return ""


def _build_route_analysis_cache() -> dict[str, Any]:
    """Precompute Python route analysis for Streamlit Cloud (no browser → localhost)."""
    cache: dict[str, Any] = {}
    try:
        from components.route_engine import analyze_route_for_api

        for origin, destination, disability in ROUTE_CACHE_SPECS:
            key = f"{disability}|{origin}|{destination}"
            result, _ = _safe_call(
                f"route_analysis:{key}",
                lambda o=origin, d=destination, dis=disability: analyze_route_for_api(o, d, dis),
                {"ok": False},
            )
            if isinstance(result, dict):
                cache[key] = result
    except Exception:
        logger.warning("route_analysis_cache build failed:\n%s", traceback.format_exc())
    return cache


def _label(status: str) -> str:
    return STATUS_LABELS.get(str(status), str(status))


def _safe_call(name: str, fn, default: Any = None) -> tuple[Any, str]:
    try:
        return fn(), "ok"
    except Exception as exc:
        logger.warning("Module call failed [%s]: %s", name, exc)
        return default, f"error:{exc.__class__.__name__}"


def _csv_inventory_rows() -> list[dict[str, Any]]:
    try:
        from modules.data_loader import load_csv_inventory

        frame = load_csv_inventory()
        if frame is None or frame.empty:
            return []
        return [
            {
                "file_name": str(row.get("file_name", "")),
                "rows": int(row.get("rows", 0) or 0),
                "columns": int(row.get("columns", 0) or 0),
                "status": str(row.get("data_status", row.get("status", "missing"))),
                "display": _label(str(row.get("data_status", row.get("status", "missing")))),
            }
            for row in frame.to_dict(orient="records")
        ]
    except Exception:
        return []


def _csv_bundle(name: str, loader) -> dict[str, Any]:
    result, import_status = _safe_call(name, loader, {})
    if not isinstance(result, dict):
        return {"name": name, "data_status": "missing", "rows": 0, "display": _label("missing"), "import_status": import_status}
    frame = result.get("data")
    rows = int(len(frame)) if frame is not None and hasattr(frame, "__len__") else 0
    status = str(result.get("data_status", "missing"))
    path = result.get("path")
    return {
        "name": name,
        "data_status": status,
        "rows": rows,
        "file_name": Path(path).name if path else None,
        "display": _label(status),
        "import_status": import_status,
    }


def _build_scoring_samples(vworld_data_status: str) -> dict[str, Any]:
    try:
        from modules.scoring import calculate_viable_path_score
    except Exception:
        return {"by_disability": {}, "import_status": "import_failed"}

    by_disability: dict[str, Any] = {}
    for disability, base in DISABILITY_SCORING_INPUTS.items():
        payload = {
            **base,
            "origin_geocode_status": vworld_data_status if vworld_data_status == "configured" else "mock_fallback",
            "destination_geocode_status": vworld_data_status if vworld_data_status == "configured" else "mock_fallback",
        }
        try:
            result = calculate_viable_path_score(payload)
            mobility = str(result.get("mobility_level", ""))
            by_disability[disability] = {
                "score": int(result.get("score", 0)),
                "mobility_level": mobility,
                "display_grade": JS_GRADE_MAP.get(mobility, mobility),
                "explanation": str(result.get("explanation", "")),
                "recommended_actions": list(result.get("recommended_actions", []))[:3],
                "source": "modules.scoring",
            }
        except Exception:
            by_disability[disability] = {"score": 80, "display_grade": "주의", "explanation": "점수 엔진 fallback", "source": "fallback"}

    return {"by_disability": by_disability, "import_status": "ok"}


def _build_rag_payload() -> dict[str, Any]:
    try:
        from modules.rag_bm25 import answer_with_rag, build_index
    except Exception:
        return {"status": "fallback", "display": _label("fallback"), "exercise_guides": {}, "import_status": "import_failed"}

    index, index_status = _safe_call("rag.build_index", lambda: build_index("docs"), None)
    ready = bool(index and getattr(index, "ready", False))
    data_status = getattr(index, "data_status", "fallback") if index else "fallback"
    search_status = getattr(index, "search_status", "fallback") if index else "fallback"
    rag_status = "ready" if ready and data_status == "real_docs" else "fallback"

    exercise_guides: dict[str, str] = {}
    samples: list[dict[str, Any]] = []
    for query in RAG_SAMPLE_QUERIES:
        answer_result, _ = _safe_call(
            f"rag.answer:{query[:20]}",
            lambda q=query: answer_with_rag(q, top_k=3, docs_dir="docs"),
            {},
        )
        if isinstance(answer_result, dict):
            samples.append(
                {
                    "query": query,
                    "answer": str(answer_result.get("answer", ""))[:500],
                    "ok": bool(answer_result.get("ok")),
                    "data_status": str(answer_result.get("data_status", data_status)),
                    "search_status": str(answer_result.get("search_status", search_status)),
                    "source": str(answer_result.get("source", "fallback")),
                }
            )
            if "반다비" in query or "생활체육" in query:
                exercise_guides["physical"] = str(answer_result.get("answer", ""))[:280]
                exercise_guides["visual"] = str(answer_result.get("answer", ""))[:280]
                exercise_guides["developmental"] = str(answer_result.get("answer", ""))[:280]
                exercise_guides["senior"] = str(answer_result.get("answer", ""))[:280]

    if not exercise_guides and samples:
        text = samples[0].get("answer", "")
        for key in ("physical", "visual", "developmental", "senior"):
            exercise_guides[key] = text[:280]

    return {
        "status": rag_status,
        "display": _label("ready" if rag_status == "ready" else "fallback"),
        "data_status": data_status,
        "search_status": search_status,
        "document_count": len(getattr(index, "documents", []) or []) if index else 0,
        "chunk_count": len(getattr(index, "chunks", []) or []) if index else 0,
        "samples": samples,
        "exercise_guides": exercise_guides,
        "import_status": index_status,
    }


def _build_public_api_cards(
    vworld: dict[str, Any],
    data_go: dict[str, Any],
    rag: dict[str, Any],
    vision: dict[str, Any],
    email: dict[str, Any],
    csv_inventory: list[dict[str, Any]],
    *,
    route_cache_ok: int = 0,
    api_base: str = "",
) -> list[dict[str, str]]:
    csv_loaded = sum(1 for row in csv_inventory if row.get("status") == "real_csv")
    csv_display = f"CSV {csv_loaded}/{len(csv_inventory)} 로드" if csv_inventory else "CSV 없음"
    if route_cache_ok:
        route_display = f"Python 엔진 · 서버 캐시 {route_cache_ok}건 (경로 분석 버튼)"
    elif api_base:
        route_display = f"FastAPI 연동 · {api_base}"
    else:
        route_display = "클라이언트 mock fallback"
    return [
        {"label": "VWorld 주소검색", "status": vworld.get("data_status", "missing"), "display": _label(vworld.get("data_status", "missing"))},
        {"label": "data.go.kr 공공데이터", "status": data_go.get("data_status", "missing"), "display": _label(data_go.get("data_status", "missing"))},
        {"label": "CSV 데이터", "status": "real_csv" if csv_loaded else "missing", "display": csv_display},
        {"label": "RAG 문서검색", "status": rag.get("status", "fallback"), "display": rag.get("display", _label("fallback"))},
        {"label": "Vision 모델", "status": vision.get("data_status", "missing_key"), "display": _label(vision.get("data_status", "missing_key"))},
        {"label": "SendGrid", "status": email.get("data_status", "disabled"), "display": _label(email.get("data_status", "disabled"))},
        {"label": "경로 분석 엔진", "status": "ready" if route_cache_ok else "fallback", "display": route_display},
        {"label": "버스 도착 정보", "status": "no_data", "display": "실시간 도착 · no_data fallback"},
        {"label": "기상 단기예보", "status": vworld.get("data_status", "missing"), "display": _label(vworld.get("data_status", "missing"))},
        {"label": "접근성 제보", "status": "configured", "display": "프론트 세션 저장"},
    ]


def build_server_data() -> dict[str, Any]:
    """Build safe server-side payload for window.BANDABI_SERVER_DATA (no secrets)."""
    import_status: dict[str, str] = {}
    modules_ok: list[str] = []
    modules_failed: list[str] = []

    for mod_name in ("api_clients", "scoring", "rag_bm25", "vision", "emailer", "data_loader", "config"):
        try:
            __import__(f"modules.{mod_name}")
            modules_ok.append(mod_name)
            import_status[mod_name] = "ok"
        except Exception as exc:
            modules_failed.append(mod_name)
            import_status[mod_name] = f"import_failed:{exc.__class__.__name__}"

    vworld, vworld_call = _safe_call("vworld_status", lambda: __import__("modules.api_clients", fromlist=["vworld_status"]).vworld_status(), {})
    data_go, data_go_call = _safe_call("data_go_kr_status", lambda: __import__("modules.api_clients", fromlist=["data_go_kr_status"]).data_go_kr_status(), {})
    config_status, config_call = _safe_call("list_config_status", lambda: __import__("modules.config", fromlist=["list_config_status"]).list_config_status(), {})
    import_status["vworld_status"] = vworld_call
    import_status["data_go_kr_status"] = data_go_call
    import_status["list_config_status"] = config_call

    csv_inventory = _csv_inventory_rows()
    mobility = _csv_bundle("mobility_center", lambda: __import__("modules.data_loader", fromlist=["load_mobility_center_data"]).load_mobility_center_data())
    protected = _csv_bundle("protected_zone", lambda: __import__("modules.data_loader", fromlist=["load_protected_zone_data"]).load_protected_zone_data())
    low_floor = _csv_bundle("low_floor_bus", lambda: __import__("modules.data_loader", fromlist=["load_low_floor_bus_data"]).load_low_floor_bus_data())

    vworld_status_value = str((vworld or {}).get("data_status", "missing"))
    scoring = _build_scoring_samples(vworld_status_value)
    rag = _build_rag_payload()

    vision_status_data, vision_call = _safe_call("vision_status", lambda: __import__("modules.vision", fromlist=["vision_status"]).vision_status(), {})
    vision_demo, vision_demo_call = _safe_call(
        "demo_vision_fallback",
        lambda: __import__("modules.vision", fromlist=["demo_vision_fallback"]).demo_vision_fallback("점자블록", "점자블록 단절 의심"),
        {},
    )
    import_status["vision_status"] = vision_call
    import_status["vision_demo"] = vision_demo_call

    email_status_data, email_call = _safe_call("email_status", lambda: __import__("modules.emailer", fromlist=["email_status"]).email_status(), {})
    import_status["email_status"] = email_call

    official_draft, draft_call = _safe_call(
        "build_official_draft",
        lambda: __import__("modules.emailer", fromlist=["build_official_draft"]).build_official_draft(
            title="김포 반다비체육센터 접근성 개선 검토 요청",
            body="AI 점검 보조 결과를 바탕으로 접근성 개선 검토를 요청드립니다.",
            location="김포 반다비체육센터",
            recipient="담당 부서",
            sender="반다비 AI 운영팀",
        ),
        "",
    )
    import_status["build_official_draft"] = draft_call

    route_analysis_cache = _build_route_analysis_cache()
    route_cache_ok = sum(1 for row in route_analysis_cache.values() if isinstance(row, dict) and row.get("ok"))
    api_base = _resolve_api_base()

    public_api_cards = _build_public_api_cards(
        vworld or {},
        data_go or {},
        rag,
        vision_status_data or {},
        email_status_data or {},
        csv_inventory,
        route_cache_ok=route_cache_ok,
        api_base=api_base,
    )

    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "modules_ok": modules_ok,
            "modules_failed": modules_failed,
            "import_status": import_status,
            "api_base": api_base,
            "route_engine": "server_cache" if route_cache_ok else "client_fallback",
            "route_cache_entries": route_cache_ok,
            "note": "Streamlit Cloud: 경로 분석은 서버 캐시 우선. BACKEND_API_URL 설정 시 FastAPI 실시간 호출.",
        },
        "route_analysis_cache": route_analysis_cache,
        "api_status": {
            "vworld": vworld or {"data_status": "missing"},
            "data_go_kr": data_go or {"data_status": "missing"},
            "config": config_status or {},
        },
        "csv": {
            "inventory": csv_inventory,
            "mobility_center": mobility,
            "protected_zone": protected,
            "low_floor_bus": low_floor,
            "loaded_count": sum(1 for row in csv_inventory if row.get("status") == "real_csv"),
            "total_files": len(csv_inventory),
        },
        "scoring": scoring,
        "rag": rag,
        "vision": {
            "status": vision_status_data or {"data_status": "missing_key"},
            "demo_fallback": vision_demo or {},
        },
        "email": {
            "status": email_status_data or {"data_status": "disabled"},
            "official_draft": {
                "subject": "김포 반다비체육센터 접근성 개선 검토 요청",
                "body": official_draft if isinstance(official_draft, str) else "",
            },
        },
        "public_api_cards": public_api_cards,
        "dashboard": {
            "csv_inventory": csv_inventory,
            "csv_summary": f"CSV {sum(1 for r in csv_inventory if r.get('status') == 'real_csv')}/{len(csv_inventory)} 파일 로드",
            "mobility_rows": mobility.get("rows", 0),
            "protected_zone_rows": protected.get("rows", 0),
            "low_floor_bus_rows": low_floor.get("rows", 0),
        },
    }

    logger.info(
        "server_data ok modules=%s csv_files=%s rag=%s vworld=%s",
        len(modules_ok),
        len(csv_inventory),
        rag.get("status"),
        vworld_status_value,
    )
    return payload


def inject_server_data(html: str, server_data: dict[str, Any]) -> str:
    json_text = json.dumps(server_data, ensure_ascii=False)
    json_text = json_text.replace("<", "\\u003c").replace(">", "\\u003e")
    script = f"<script>window.BANDABI_SERVER_DATA = {json_text};</script>"
    if "</head>" in html:
        return html.replace("</head>", script + "\n</head>", 1)
    return html.replace("</body>", script + "\n</body>", 1)


@st.cache_data(show_spinner=False)
def load_render_html() -> str:
    html_path = ROOT / "bandabi_purple.html"
    if not html_path.exists():
        return ""
    try:
        server_data = build_server_data()
    except Exception:
        logger.error("build_server_data failed:\n%s", traceback.format_exc())
        server_data = {
            "meta": {"generated_at": datetime.now(timezone.utc).isoformat(), "error": "build_failed"},
            "public_api_cards": [],
        }
    return inject_server_data(html_path.read_text(encoding="utf-8"), server_data)


st.set_page_config(
    page_title="반다비 AI",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    #MainMenu, header, footer { visibility: hidden; height: 0 !important; }
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stAppViewContainer"] > .main > div {
      padding-top: 0 !important;
      padding-bottom: 0 !important;
    }
    .stApp {
      margin: 0 !important;
      padding: 0 !important;
      background: #e8e2f4;
    }
    .block-container {
      padding: 0 !important;
      margin: 0 !important;
      max-width: 100% !important;
    }
    div[data-testid="stVerticalBlock"] { gap: 0 !important; }
    iframe {
      display: block;
      width: 100% !important;
      border: 0 !important;
      min-height: 100vh;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

html = load_render_html()
if not html:
    st.error("bandabi_purple.html 파일을 찾을 수 없습니다.")
else:
    components.html(html, height=1400, scrolling=True)
