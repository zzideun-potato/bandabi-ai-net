from __future__ import annotations

import os
import sqlite3

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.database import get_connection, init_db
from backend.schemas import (
    AuthResponse,
    LoginRequest,
    RouteAnalysisRequest,
    SelectRoleRequest,
    SignupRequest,
    UserPublic,
)
from backend.security import create_access_token, decode_access_token, hash_password, verify_password

app = FastAPI(title="Bandabi Auth API", version="1.0.0")

_default_cors = "http://localhost:8501,http://127.0.0.1:8501,null"
_cors_raw = os.getenv("CORS_ORIGINS", _default_cors).strip()
if _cors_raw == "*":
    _cors_origins = ["*"]
    _cors_credentials = False
else:
    _cors_origins = [origin.strip() for origin in _cors_raw.split(",") if origin.strip()]
    if "null" not in _cors_origins:
        _cors_origins.append("null")
    _cors_credentials = True
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

bearer_scheme = HTTPBearer(auto_error=False)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def _row_to_user(row: sqlite3.Row) -> UserPublic:
    return UserPublic(
        id=row["id"],
        email=row["email"],
        name=row["name"],
        role=row["role"],
    )


def _auth_response(row: sqlite3.Row) -> AuthResponse:
    user = _row_to_user(row)
    token = create_access_token(
        user_id=user.id,
        email=str(user.email),
        name=user.name,
        role=user.role,
    )
    return AuthResponse(access_token=token, user=user)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> sqlite3.Row:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다.")

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="세션이 만료되었습니다.") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 세션입니다.")

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (int(user_id),)).fetchone()

    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="계정을 찾을 수 없습니다.")

    return row


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/status")
def api_status() -> dict[str, object]:
    """Safe API configuration and public-data probe status (no secret values)."""
    try:
        from modules.api_clients import (
            data_go_kr_status,
            fetch_weather_short_forecast,
            test_vworld_geocode_connection,
            vworld_status,
        )
        from modules.config import list_config_status
        from modules.emailer import email_status
        from modules.vision import vision_status

        vworld = vworld_status()
        data_go = data_go_kr_status()
        email = email_status()
        vision = vision_status()
        weather = fetch_weather_short_forecast()
        vworld_sample = test_vworld_geocode_connection("김포 구래역")

        return {
            "status": "ok",
            "vworld": {
                "data_status": vworld.get("data_status", "missing"),
                "configured": bool(vworld.get("configured")),
            },
            "data_go_kr": {
                "data_status": data_go.get("data_status", "missing"),
                "configured": bool(data_go.get("configured")),
            },
            "weather": {"data_status": weather.get("status", "fallback")},
            "bus_route": {"data_status": "via_route_analysis"},
            "email": {"data_status": email.get("data_status", "disabled")},
            "vision": {"data_status": vision.get("data_status", "missing_key")},
            "config": list_config_status(),
            "vworld_sample": {
                "ok": bool(vworld_sample.get("ok")),
                "status": vworld_sample.get("status", "mock_fallback"),
            },
        }
    except Exception:
        return {"status": "degraded", "message": "status_check_failed"}


@app.post("/api/route-analysis")
def route_analysis(body: RouteAnalysisRequest) -> dict[str, object]:
    """Run Python route modules; returns UI-safe JSON without secrets."""
    try:
        from components.route_engine import analyze_route_for_api

        return analyze_route_for_api(body.origin, body.destination, body.disability)
    except Exception:
        return {"ok": False, "error": "analysis_failed"}


@app.post("/auth/signup", response_model=AuthResponse)
def signup(body: SignupRequest) -> AuthResponse:
    email = str(body.email).strip().lower()
    name = body.name.strip()
    password_hash = hash_password(body.password)

    with get_connection() as conn:
        try:
            conn.execute(
                "INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)",
                (email, name, password_hash),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 이메일입니다.",
            ) from exc

        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if row is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="회원가입 처리 중 오류가 발생했습니다.")

    return _auth_response(row)


@app.post("/auth/login", response_model=AuthResponse)
def login(body: LoginRequest) -> AuthResponse:
    email = str(body.email).strip().lower()

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    return _auth_response(row)


@app.get("/auth/me", response_model=UserPublic)
def me(current_user: sqlite3.Row = Depends(get_current_user)) -> UserPublic:
    return _row_to_user(current_user)


@app.post("/auth/select-role", response_model=AuthResponse)
def select_role(
    body: SelectRoleRequest,
    current_user: sqlite3.Row = Depends(get_current_user),
) -> AuthResponse:
    with get_connection() as conn:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (body.role, current_user["id"]))
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (current_user["id"],)).fetchone()

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="계정을 찾을 수 없습니다.")

    return _auth_response(row)


@app.post("/auth/logout")
def logout() -> dict[str, str]:
    return {"message": "logged out"}
