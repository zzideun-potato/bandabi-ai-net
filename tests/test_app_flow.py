"""AppTest + unit assertions for Bandabi single-page flow."""

from __future__ import annotations

from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from components.route_engine import run_route_analysis
from components.session_state import ROLE_B2C, init_session_state
from components.vision_ui import FORBIDDEN_VISION_PRECISE
from modules.rag_bm25 import answer_with_rag
from modules.safety import sanitize_public_claims
from views.tab_main_journey import render_guardian, render_report


FORBIDDEN_PRECISE_ROUTE_STRINGS = ("35분", "300m", "환승 1회")


def _session_get(at: AppTest, key: str, default=None):
    try:
        return at.session_state[key]
    except (KeyError, AttributeError, TypeError):
        return default


def _session_has(at: AppTest, key: str) -> bool:
    try:
        value = at.session_state[key]
        return value is not None
    except (KeyError, AttributeError, TypeError):
        return False


def _all_text(at: AppTest) -> str:
    parts: list[str] = []
    for block in at.main:
        try:
            parts.append(str(block.value))
        except Exception:
            pass
    for collection_name in ("markdown", "caption", "text", "title"):
        for item in getattr(at, collection_name, []) or []:
            try:
                parts.append(str(item.value))
            except Exception:
                pass
    return "\n".join(parts)


def _go_to_vision_tab(at: AppTest) -> AppTest:
    return _click_button(at, key="tab_vision")


def _click_button(at: AppTest, *, label_part: str | None = None, key: str | None = None) -> AppTest:
    for button in at.button:
        if key is not None and button.key == key:
            return button.click().run()
        if label_part and label_part in (button.label or ""):
            return button.click().run()
    labels = [(b.key, b.label) for b in at.button]
    raise AssertionError(f"Button key={key!r} label={label_part!r} not found. Available: {labels}")


def _click_dialog_confirm(at: AppTest) -> AppTest:
    return _click_button(at, key="pending_confirm_ok")


def _assert_no_exception(at: AppTest, step: str) -> None:
    assert not at.exception, f"{step} raised: {at.exception}"


def _login_as_b2c_user(at: AppTest) -> AppTest:
    at = _click_button(at, label_part="로그인")
    _assert_no_exception(at, "auth login entry")
    at = _click_button(at, label_part="계속")
    _assert_no_exception(at, "auth form continue")
    at = _click_button(at, label_part="이용자 모드")
    _assert_no_exception(at, "auth role B2C")
    assert at.session_state["authenticated"] is True
    assert at.session_state["role"] == ROLE_B2C
    return at


class TestNavigationLayout:
    def test_pages_moved_to_reference(self, project_root: Path) -> None:
        assert not (project_root / "pages").exists(), "pages/ must not exist at project root"
        assert (project_root / "_reference" / "pages").is_dir()

    def test_app_initial_render_no_exception(self, app_path: Path) -> None:
        at = AppTest.from_file(str(app_path)).run()
        _assert_no_exception(at, "initial render")


class TestFullUserJourney:
    def test_journey_steps_without_exception(self, app_path: Path) -> None:
        at = AppTest.from_file(str(app_path)).run()
        _assert_no_exception(at, "boot")

        at = _login_as_b2c_user(at)

        at = _click_button(at, key="btn_ai_start")
        _assert_no_exception(at, "route analysis")
        assert at.session_state["main_step"] == "route"

        at = _click_button(at, key="route_confirm")
        _assert_no_exception(at, "route confirm open")
        assert _session_has(at, "pending_confirm")
        at = _click_dialog_confirm(at)
        _assert_no_exception(at, "route confirm apply")
        assert at.session_state["main_step"] == "care"
        assert not _session_has(at, "pending_confirm")

        at = _click_button(at, key="care_confirm")
        at = _click_dialog_confirm(at)
        _assert_no_exception(at, "care confirm")
        assert at.session_state["main_step"] == "class"

        at = _click_button(at, key="class_confirm")
        at = _click_dialog_confirm(at)
        _assert_no_exception(at, "class confirm")
        assert at.session_state["main_step"] == "report"

        at = _click_button(at, key="report_save")
        _assert_no_exception(at, "report save")
        assert at.session_state["main_step"] == "guardian"

        text = _all_text(at)
        assert sanitize_public_claims("실제 외부 전송") in text or "외부 전송" in text


class TestRouteSafetyLabels:
    def test_non_real_api_route_has_reference_badge_not_precise_strings(self) -> None:
        result = run_route_analysis(
            {
                "origin": "김포 구래역 1번 출구",
                "destination": "김포 반다비체육센터",
                "disability_key": "physical",
                "accessibility_support_type": "휠체어 또는 보행 보조 필요",
                "mobility_support_needed": True,
                "companion_needed": False,
                "public_transport_available": True,
                "weather_enabled": True,
            }
        )
        assert result["bus_route"].get("status") != "real_api"
        assert result["travel_metrics"]["badge"] == sanitize_public_claims("예상(참고용)")

        def app() -> None:
            import streamlit as st

            from components.route_engine import run_route_analysis
            from components.session_state import ROLE_B2C, init_session_state
            from views.tab_main_journey import render_route

            init_session_state()
            st.session_state.authenticated = True
            st.session_state.role = ROLE_B2C
            st.session_state.main_step = "route"
            st.session_state.route_analysis_result = run_route_analysis(
                {
                    "origin": "김포 구래역 1번 출구",
                    "destination": "김포 반다비체육센터",
                    "disability_key": "physical",
                    "accessibility_support_type": "휠체어 또는 보행 보조 필요",
                    "mobility_support_needed": True,
                    "companion_needed": False,
                    "public_transport_available": True,
                    "weather_enabled": True,
                }
            )
            render_route()

        at = AppTest.from_function(app).run()
        _assert_no_exception(at, "route render")
        text = _all_text(at)
        assert sanitize_public_claims("예상(참고용)") in text
        for forbidden in FORBIDDEN_PRECISE_ROUTE_STRINGS:
            assert forbidden not in text, f"Found forbidden precise string: {forbidden}"


class TestPendingConfirmLogic:
    def test_apply_pending_confirm_single_action(self) -> None:
        def app() -> None:
            import streamlit as st

            from components.confirm_dialog import open_confirm, process_pending_confirm
            from components.session_state import init_session_state
            from modules.safety import sanitize_public_claims

            init_session_state()
            st.session_state.main_step = "route"
            st.session_state.bt_balance = 3500
            open_confirm(
                title=sanitize_public_claims("운영 확정 요청이 등록되었습니다."),
                subtitle=sanitize_public_claims("예약·이동·동행 플랜이 다음 단계로 연결됩니다."),
                message=sanitize_public_claims("테스트 메시지"),
                bt_delta=500,
                next_step="care",
                on_confirm_key="route",
            )
            pending = st.session_state.pending_confirm
            assert pending is not None
            process_pending_confirm(dialog_confirmed=True)
            assert st.session_state["main_step"] == "care"
            assert st.session_state.get("pending_confirm") is None
            assert st.session_state.get("toast_message")
            assert st.session_state["bt_balance"] == 4000

        at = AppTest.from_function(app).run()
        _assert_no_exception(at, "pending confirm unit")


class TestRagFallback:
    def test_answer_with_rag_non_empty_without_llm_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        result = answer_with_rag("다음 생활체육 참여 가이드", docs_dir="docs")
        assert result.get("answer")
        assert len(str(result["answer"]).strip()) > 0

    def test_report_step_renders_rag_block(self) -> None:
        def app() -> None:
            import streamlit as st

            from components.session_state import ROLE_B2C, init_session_state
            from views.tab_main_journey import render_report

            init_session_state()
            st.session_state.authenticated = True
            st.session_state.role = ROLE_B2C
            st.session_state.main_step = "report"
            render_report()

        at = AppTest.from_function(app).run()
        _assert_no_exception(at, "report render")
        text = _all_text(at)
        assert sanitize_public_claims("다음 생활체육 가이드") in text


class TestGuardianDisclosure:
    def test_guardian_has_external_send_notice_no_diagnosis_terms(self) -> None:
        def app() -> None:
            import streamlit as st

            from components.session_state import ROLE_B2C, init_session_state
            from modules.safety import sanitize_public_claims
            from views.tab_main_journey import render_guardian

            init_session_state()
            st.session_state.authenticated = True
            st.session_state.role = ROLE_B2C
            st.session_state.main_step = "guardian"
            st.session_state.journey = {
                "destination": "김포 반다비체육센터",
                "route_plan": sanitize_public_claims("이동지원 연계 요청 등록(검토 중)"),
                "buddy": sanitize_public_claims("미연결"),
                "instructor": "박강훈",
            }
            render_guardian()

        at = AppTest.from_function(app).run()
        _assert_no_exception(at, "guardian render")
        text = _all_text(at)
        assert sanitize_public_claims("실제 외부 전송은 연결하지 않았습니다") in text
        forbidden_claims = ("의료 진단", "재활치료", "운동 처방", "치료 효과")
        for term in forbidden_claims:
            assert term not in text, f"Forbidden medical claim leaked: {term}"


class TestHighContrastToggle:
    def test_high_contrast_session_flips(self, app_path: Path) -> None:
        at = AppTest.from_file(str(app_path)).run()
        at = _login_as_b2c_user(at)
        before = bool(_session_get(at, "high_contrast", False))
        at = _click_button(at, key="btn_high_contrast")
        _assert_no_exception(at, "high contrast toggle")
        after = bool(_session_get(at, "high_contrast", False))
        assert after is not before


class TestVisionTab:
    def _vision_demo_ready(self, app_path: Path) -> AppTest:
        at = AppTest.from_file(str(app_path)).run()
        at = _login_as_b2c_user(at)
        at = _go_to_vision_tab(at)
        _assert_no_exception(at, "vision tab open")
        at = _click_button(at, key="vision_demo_analyze")
        _assert_no_exception(at, "vision demo analyze")
        assert _session_has(at, "vision_result")
        return at

    def test_demo_analyze_without_api_key_no_exception(self, app_path: Path) -> None:
        at = self._vision_demo_ready(app_path)
        assert at.session_state["vision_result"].get("source") != "vision_model"

    def test_fallback_shows_reference_badge_not_precise_percent(self, app_path: Path) -> None:
        at = self._vision_demo_ready(app_path)
        text = _all_text(at)
        assert sanitize_public_claims("예시(참고용)") in text
        for forbidden in FORBIDDEN_VISION_PRECISE:
            assert forbidden not in text, f"Found forbidden precise string: {forbidden}"

    def test_result_area_has_official_and_mask_notices(self, app_path: Path) -> None:
        at = self._vision_demo_ready(app_path)
        text = _all_text(at)
        assert sanitize_public_claims("공식 판정 아님") in text
        assert sanitize_public_claims("마스킹") in text or "개인정보" in text

    def test_report_type_select_change_still_runs_demo(self, app_path: Path) -> None:
        at = AppTest.from_file(str(app_path)).run()
        at = _login_as_b2c_user(at)
        at = _go_to_vision_tab(at)
        target = sanitize_public_claims("경사로")
        matched = False
        for sb in at.selectbox:
            if sb.key == "vision_report_type":
                sb.set_value(target).run()
                matched = True
                break
        assert matched, "vision_report_type selectbox not found"
        at = _click_button(at, key="vision_demo_analyze")
        _assert_no_exception(at, "vision demo after report type change")
        assert _session_get(at, "vision_last_report_type") == target


class TestDeployNoKeysFallback:
    """Streamlit Cloud 초기 배포( Secrets 없음 )와 동일한 환경 — conftest가 키를 비움."""

    def test_tab1_route_and_journey_fallback_no_exception(self, app_path: Path) -> None:
        at = AppTest.from_file(str(app_path)).run()
        at = _login_as_b2c_user(at)
        at = _click_button(at, key="btn_ai_start")
        _assert_no_exception(at, "deploy: tab1 route without keys")
        route_result = _session_get(at, "route_analysis_result") or {}
        assert route_result.get("bus_route", {}).get("status") != "real_api"
        text = _all_text(at)
        assert sanitize_public_claims("예상(참고용)") in text

        at = _click_button(at, key="route_confirm")
        at = _click_dialog_confirm(at)
        at = _click_button(at, key="care_confirm")
        at = _click_dialog_confirm(at)
        at = _click_button(at, key="class_confirm")
        at = _click_dialog_confirm(at)
        _assert_no_exception(at, "deploy: tab1 report step without keys")
        rag = answer_with_rag("다음 생활체육 참여 가이드", docs_dir="docs")
        assert rag.get("answer")

        at = _click_button(at, key="report_save")
        _assert_no_exception(at, "deploy: tab1 guardian without keys")

    def test_tab3_vision_fallback_badges_no_exception(self, app_path: Path) -> None:
        at = AppTest.from_file(str(app_path)).run()
        at = _login_as_b2c_user(at)
        at = _go_to_vision_tab(at)
        _assert_no_exception(at, "deploy: tab3 open without keys")
        text = _all_text(at)
        assert sanitize_public_claims("대체 데이터") in text

        at = _click_button(at, key="vision_demo_analyze")
        _assert_no_exception(at, "deploy: tab3 demo analyze without keys")
        result = _session_get(at, "vision_result") or {}
        assert result.get("source") != "vision_model"
        text = _all_text(at)
        assert sanitize_public_claims("예시(참고용)") in text
        assert sanitize_public_claims("공식 판정 아님") in text


# Manual verification registry (not asserted as pass)
MANUAL_CHECKS = [
    ("고대비 실제 색 대비 변화", "수동 확인 필요", "AppTest는 session_state만 검증"),
    ("보라 테마 시각적 일치", "수동 확인 필요", "CSS는 inject_purple_theme 담당"),
    ("탭3 bbox·스캔라인 연출 애니메이션", "수동 확인 필요", "SVG 데모 연출은 시각 확인"),
]
