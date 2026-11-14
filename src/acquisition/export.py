import csv
import json
from pathlib import Path
from typing import Any

from .models import PropertyLead, ScoreBreakdown


def leads_to_rows(
    leads: list[PropertyLead],
    scores: dict[str, ScoreBreakdown],
    priorities: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lead in leads:
        sc = scores.get(lead.property_id, lead.score)
        uw = lead.underwriting
        rows.append(
            {
                "property_id": lead.property_id,
                "address": lead.address,
                "city": lead.city,
                "zip_code": lead.zip_code,
                "asking_price": lead.asking_price,
                "score": sc.total,
                "priority": priorities.get(lead.property_id, ""),
                "buyer_mao": uw.buyer_mao if uw else None,
                "assignment_feasible": uw.assignment_feasible if uw else None,
                "arv_base": uw.arv_base if uw else None,
                "rehab_base": uw.rehab_base if uw else None,
                "verification": lead.verification.value,
                "pipeline_status": lead.pipeline_status.value,
                "source_url": lead.sources[0].url if lead.sources else "",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")