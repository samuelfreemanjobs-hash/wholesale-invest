import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from enum import Enum

from ..models import PropertyLead, ScoreBreakdown

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _json_default(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"Not JSON serializable: {type(value)!r}")
DEFAULT_DB = Path(__file__).resolve().parents[3] / "data" / "vault.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DealVault:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(schema)

    def upsert_lead(
        self,
        lead: PropertyLead,
        score: ScoreBreakdown,
        priority_label: str,
    ) -> None:
        now = utc_now()
        payload = self._lead_payload(lead, score, priority_label)
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT property_id FROM properties WHERE property_id = ?",
                (lead.property_id,),
            ).fetchone()
            created = existing["property_id"] if existing else now
            conn.execute(
                """
                INSERT INTO properties (
                    property_id, address, city, state, zip_code, asking_price,
                    beds, baths, verification_status, pipeline_status,
                    score_total, priority_label, risk_class, hard_stop,
                    created_at, updated_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(property_id) DO UPDATE SET
                    address=excluded.address,
                    city=excluded.city,
                    zip_code=excluded.zip_code,
                    asking_price=excluded.asking_price,
                    verification_status=excluded.verification_status,
                    pipeline_status=excluded.pipeline_status,
                    score_total=excluded.score_total,
                    priority_label=excluded.priority_label,
                    risk_class=excluded.risk_class,
                    hard_stop=excluded.hard_stop,
                    updated_at=excluded.updated_at,
                    payload_json=excluded.payload_json
                """,
                (
                    lead.property_id,
                    lead.address,
                    lead.city,
                    lead.state,
                    lead.zip_code,
                    lead.asking_price,
                    lead.beds,
                    lead.baths,
                    lead.verification.value,
                    lead.pipeline_status.value,
                    score.total,
                    priority_label,
                    score.risk_class.value,
                    1 if score.hard_stop else 0,
                    created,
                    now,
                    json.dumps(payload, default=_json_default),
                ),
            )
            conn.execute("DELETE FROM sources WHERE property_id = ?", (lead.property_id,))
            for src in lead.sources:
                conn.execute(
                    """
                    INSERT INTO sources (property_id, channel, url, retrieved_at, snippet)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        lead.property_id,
                        src.channel,
                        src.url,
                        src.retrieved_at.isoformat(),
                        src.snippet,
                    ),
                )
            conn.commit()

    def _lead_payload(
        self,
        lead: PropertyLead,
        score: ScoreBreakdown,
        priority_label: str,
    ) -> dict[str, Any]:
        uw = lead.underwriting
        return {
            "lead": {
                "property_id": lead.property_id,
                "address": lead.address,
                "city": lead.city,
                "asking_price": lead.asking_price,
                "motivation_evidence": lead.motivation_evidence,
                "buyer_match_ids": lead.buyer_match_ids,
                "risk_notes": lead.risk_notes,
                "metadata": lead.metadata,
            },
            "underwriting": asdict(uw) if uw else None,
            "comps": asdict(lead.comps) if lead.comps else None,
            "rehab": asdict(lead.rehab) if lead.rehab else None,
            "score": asdict(score),
            "priority_label": priority_label,
            "sources": [s.to_dict() for s in lead.sources],
        }

    def list_qualified(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM properties
                WHERE hard_stop = 0 AND pipeline_status = 'qualified'
                ORDER BY score_total DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]