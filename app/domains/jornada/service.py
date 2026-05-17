"""Jornada service — session tracking and daily report generation."""

import json
import os
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.shared.models.test_result import TestResult

SESSION_MARKER = "/tmp/analizavet-session-start"

# Category definitions: (key, icon_and_name, test_type_code_filter)
_CATEGORIES = [
    ("perfiles", "🔬 Perfiles básicos", "CHEM"),
    ("coprologicos", "🦠 Coprológicos", "COPROSC"),
    ("coprologicos_seriados", "🦠🔬 Coprológicos seriados", "COPROSC_SERIADO"),
    ("citoquimicos", "💛 Citoquímicos", "CITO"),
]


def read_session_start() -> float | None:
    """Read the Unix timestamp from the session marker file.

    Returns the timestamp as a float (seconds since epoch),
    or None if the marker file does not exist or cannot be read.
    """
    try:
        with open(SESSION_MARKER) as f:
            raw = f.read().strip()
            if not raw:
                return None
            return float(raw)
    except (FileNotFoundError, ValueError, OSError):
        return None


def _group_results(results: list[dict]) -> dict[str, list[dict]]:
    """Group result dicts into the four jornada categories.

    Returns a dict mapping category_key -> list of result dicts.
    """
    grouped: dict[str, list[dict]] = {
        "perfiles": [],
        "coprologicos": [],
        "coprologicos_seriados": [],
        "citoquimicos": [],
    }

    for result_dict in results:
        code = (result_dict.get("test_type_code") or "").strip().upper()

        if code == "CHEM":
            grouped["perfiles"].append(result_dict)
        elif code == "COPROSC":
            test_type = (result_dict.get("test_type") or "").lower()
            if "seriado" in test_type:
                grouped["coprologicos_seriados"].append(result_dict)
            else:
                grouped["coprologicos"].append(result_dict)
        elif code == "CITO":
            grouped["citoquimicos"].append(result_dict)

    return grouped


_DAYS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def _format_category(category_name: str, items: list[dict]) -> str:
    """Format a single category section of the report.

    Returns empty string if there are no items (caller decides whether to skip).
    """
    if not items:
        return ""
    lines = [f"\n{category_name}:"]
    for item in items:
        lines.append(
            f"  • {item['name']} — {item['species']} — tutor: {item['owner']} — {item['doctor']}"
        )
    return "\n".join(lines)


def format_report(grouped: dict[str, list[dict]]) -> str:
    """Build the full text/plain jornada report from grouped results.

    Args:
        grouped: dict from _group_results() with category_key -> list of dicts.

    Returns:
        Plain text report as a single string.
    """
    total = sum(len(items) for items in grouped.values())
    if total == 0:
        return (
            "🐾 Reporte de jornada — Huellas Lab\n"
            "No hay reportes generados en esta sesión."
        )

    # Collect unique dates from every item across all categories
    dates_set: set[str] = set()
    for items in grouped.values():
        for item in items:
            date_str = item.get("date")
            if date_str:
                dates_set.add(date_str)

    # Build date line with weekday names
    if dates_set:
        formatted_dates: list[str] = []
        for ds in sorted(dates_set):
            try:
                dt = datetime.strptime(ds, "%Y-%m-%d")
                weekday = _DAYS_ES[dt.weekday()]
                formatted_dates.append(f"{weekday} {dt.strftime('%d/%m/%Y')}")
            except (ValueError, IndexError):
                formatted_dates.append(ds)
        dates_line = f"📅 Reportes del día {', '.join(formatted_dates)}"
    else:
        dates_line = ""

    parts = ["🐾 Reporte de jornada — Huellas Lab"]
    if dates_line:
        parts.append(dates_line)

    # Only show categories that have results
    category_configs = [
        ("perfiles", "🔬 Perfiles básicos del día"),
        ("coprologicos", "🦠 Coprológicos"),
        ("coprologicos_seriados", "🦠🔬 Coprológicos seriados"),
        ("citoquimicos", "💛 Citoquímicos"),
    ]

    for key, display_name in category_configs:
        items = grouped.get(key, [])
        if not items:
            continue  # skip empty categories entirely
        if key == "perfiles":
            header = f"{display_name} ({len(items)})"
        else:
            header = display_name
        parts.append(_format_category(header, items))

    parts.append(f"\n✅ Total: {total} reportes generados")
    return "\n".join(parts)


async def get_session_results(
    session_start: float, db_session: AsyncSession
) -> dict[str, list[dict]]:
    """Query TestResult rows and PatientArchive rows created after session_start and group by category.

    Args:
        session_start: Unix timestamp (seconds since epoch).
        db_session: Async SQLAlchemy session.

    Returns:
        Dict mapping category_key -> list of result dicts.
    """
    from app.shared.models.patient_archive import PatientArchive

    start_dt = datetime.fromtimestamp(session_start, tz=timezone.utc)
    all_results: list[dict] = []

    # Active TestResults (PDF not yet downloaded)
    stmt = (
        select(TestResult)
        .options(selectinload(TestResult.patient))
        .where(TestResult.created_at >= start_dt)
        .order_by(TestResult.created_at.asc())
    )
    result = await db_session.execute(stmt)
    rows = result.scalars().all()

    for tr in rows:
        patient = tr.patient
        all_results.append({
            "id": tr.id,
            "name": patient.name if patient else "?",
            "species": patient.species if patient else "?",
            "owner": patient.owner_name if patient else "?",
            "doctor": tr.doctor_name or "Sin médico",
            "test_type": tr.test_type,
            "test_type_code": tr.test_type_code,
            "date": tr.created_at.date().isoformat() if tr.created_at else None,
        })

    # Archived patients (PDF was downloaded during this session)
    archive_stmt = (
        select(PatientArchive)
        .where(PatientArchive.archived_at >= start_dt)
        .order_by(PatientArchive.archived_at.asc())
    )
    archive_result = await db_session.execute(archive_stmt)
    archive_rows = archive_result.scalars().all()

    for archive in archive_rows:
        snapshot = json.loads(archive.snapshot_data) if archive.snapshot_data else {}
        test_result_data = snapshot.get("test_result", {})

        all_results.append({
            "id": archive.original_test_result_id or archive.id,
            "name": archive.patient_name or "?",
            "species": archive.species or "?",
            "owner": archive.owner_name or "?",
            "doctor": test_result_data.get("doctor_name") or "Sin médico",
            "test_type": test_result_data.get("test_type") or "Examen",
            "test_type_code": test_result_data.get("test_type_code") or "",
            "date": archive.archived_at.date().isoformat() if archive.archived_at else None,
        })

    return _group_results(all_results)
