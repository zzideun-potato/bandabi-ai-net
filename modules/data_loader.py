"""CSV discovery and loading helpers with explicit fallback status."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


CSV_ENCODINGS = ("utf-8-sig", "cp949", "euc-kr")
INVENTORY_COLUMNS = ["file_name", "path", "rows", "columns", "status", "data_status"]


def discover_csv_files() -> list[Path]:
    """Find CSV files from ./data/*.csv and ./*.csv without raising exceptions."""
    found: dict[Path, Path] = {}
    for base in (Path("data"), Path(".")):
        try:
            if base.exists() and base.is_dir():
                for path in base.glob("*.csv"):
                    if path.is_file():
                        found[path.resolve()] = path
        except Exception:
            continue
    return sorted(found.values(), key=lambda item: str(item))


def list_csv_files(data_dir: str | Path = "data") -> list[Path]:
    """Backward-compatible CSV listing helper."""
    if str(data_dir) == "data":
        return discover_csv_files()
    base = Path(data_dir)
    try:
        if not base.exists() or not base.is_dir():
            return []
        return sorted(base.glob("*.csv"), key=lambda item: item.name)
    except Exception:
        return []


def safe_read_csv(path: str | Path) -> dict[str, Any]:
    csv_path = Path(path)
    if not csv_path.exists() or not csv_path.is_file():
        return {
            "data": pd.DataFrame(),
            "data_status": "missing",
            "path": str(csv_path),
            "encoding": None,
            "error": "file_missing",
        }

    last_error = ""
    for encoding in CSV_ENCODINGS:
        try:
            frame = pd.read_csv(csv_path, encoding=encoding)
            return {
                "data": frame,
                "data_status": "real_csv",
                "path": str(csv_path),
                "encoding": encoding,
                "error": None,
            }
        except Exception as exc:
            last_error = str(exc)

    return {
        "data": pd.DataFrame(),
        "data_status": "read_error",
        "path": str(csv_path),
        "encoding": None,
        "error": last_error or "read_error",
    }


def read_csv_safely(path: str | Path) -> tuple[pd.DataFrame, str | None]:
    """Backward-compatible wrapper returning a DataFrame and error string."""
    result = safe_read_csv(path)
    error = result["error"] if result["data_status"] != "real_csv" else None
    return result["data"], error


def load_csv_inventory() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for path in discover_csv_files():
        result = safe_read_csv(path)
        frame = result["data"]
        rows.append(
            {
                "file_name": path.name,
                "path": str(path),
                "rows": int(len(frame)) if isinstance(frame, pd.DataFrame) else 0,
                "columns": int(len(frame.columns)) if isinstance(frame, pd.DataFrame) else 0,
                "status": result["data_status"],
                "data_status": result["data_status"],
            }
        )
    return pd.DataFrame(rows, columns=INVENTORY_COLUMNS)


def _find_csv_by_keywords(required_keywords: tuple[str, ...], optional_keywords: tuple[str, ...] = ()) -> Path | None:
    for path in discover_csv_files():
        name = path.name
        required_match = all(keyword in name for keyword in required_keywords)
        optional_match = not optional_keywords or any(keyword in name for keyword in optional_keywords)
        if required_match and optional_match:
            return path
    return None


def _mock_result(name: str, frame: pd.DataFrame, status: str = "mock_fallback", error: str | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "data": frame,
        "data_status": status,
        "path": None,
        "encoding": None,
        "error": error,
    }


def load_mobility_center_data() -> dict[str, Any]:
    path = _find_csv_by_keywords(("교통약자", "이동지원"), ("센터", "정보"))
    if path is not None:
        result = safe_read_csv(path)
        result["name"] = "mobility_center"
        if result["data_status"] == "real_csv":
            return result
        mock = _mobility_center_mock()
        return _mock_result("mobility_center", mock, "read_error", result["error"])

    return _mock_result("mobility_center", _mobility_center_mock())


def load_protected_zone_data() -> dict[str, Any]:
    path = _find_csv_by_keywords(("보호구역",), ("노인", "장애인"))
    if path is not None:
        result = safe_read_csv(path)
        result["name"] = "protected_zone"
        if result["data_status"] == "real_csv":
            return result
        return _mock_result("protected_zone", _protected_zone_mock(), "read_error", result["error"])

    return _mock_result("protected_zone", _protected_zone_mock())


def load_low_floor_bus_data() -> dict[str, Any]:
    path = _find_csv_by_keywords(("저상버스",), ("노선", "운행"))
    if path is not None:
        result = safe_read_csv(path)
        result["name"] = "low_floor_bus"
        if result["data_status"] == "real_csv":
            return result
        return _mock_result("low_floor_bus", _low_floor_bus_mock(), "read_error", result["error"])

    return _mock_result("low_floor_bus", _low_floor_bus_mock())


def _mobility_center_mock() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "기관명": "김포시 교통약자 이동지원센터",
                "운영상태": "시연용 점검 지표",
                "확인필요": "운영기관 검토 필요",
            }
        ]
    )


def _protected_zone_mock() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "구역명": "노인장애인보호구역 예시",
                "상태": "시연용 점검 지표",
                "확인필요": "현장 상태 확인 필요",
            }
        ]
    )


def _low_floor_bus_mock() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "지역": "김포시",
                "항목": "저상버스 운행 노선수",
                "상태": "시연용 점검 지표",
                "확인필요": "공공데이터 최신성 확인 필요",
            }
        ]
    )
