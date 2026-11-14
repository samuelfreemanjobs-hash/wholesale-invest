# wholesale-invest

Metro Detroit residential wholesaling — **Lead Generation v4.5** prompts plus **Acquisition Intelligence System v6.0** (hybrid app path).

## v6.0 — Acquisition Command Center (Milestone 1)

| Path | Purpose |
|------|---------|
| `agents/v6/commander.md` | Orchestrator system prompt |
| `agents/v6/roles.md` | Twelve specialized module roles |
| `config/acquisition_v6.yml` | v6 defaults (markets, scoring, gates, compliance) |
| `config/buyers.yml` | Buyer demand DB (human-verify `active_ready`) |
| `src/acquisition/` | Python engine: underwriting, scoring, gates, vault, CLI |
| `data/vault.db` | Deal Intelligence Vault (SQLite, gitignored) |
| `notion/deal_vault_schema.json` | Export schema for Sheets/Notion/CRM |

### Run today's acquisitions

```bash
pip install -e .
python -m acquisition run
```

Outputs: `exports/acquisition_brief_<date>.csv` and `.json`, vault upserts.

**Milestone 1 behavior:** Uses `ManualCandidatesConnector` (re-underwrite samples from Phase 1 live research). Wire Firecrawl/Zillow/FSBO connectors in Milestone 2; Craigslist sales and Facebook Marketplace remain human or permitted-API only.

### v6 scoring & underwriting

- **100-point** weighted score (`config/acquisition_v6.yml`) — risk via hard stops, not buried in motivation points.
- **MAO:** `ARV × (1 − C) − Rehab − AssignmentFee` (`src/acquisition/underwriting.py`).
- **Gates:** Comps, rehab doc, economics, contact path (`src/acquisition/gates.py`).

### Legal / ops

- `human_approval_required: true` — no auto messages or offers.
- Review Michigan assignment/brokerage rules with a qualified attorney before production outreach.

## v4.5 (legacy prompt pack)

| Path | Purpose |
|------|---------|
| `agents/lead_gen_v4_5.md` | Lead gen agent system prompt |
| `config/lead_gen.yml` | Phase 1 defaults |
| `config/markets.yml` | Top 20 tiers |
| `config/scoring.yml` | Final Score v4.5 |
| `notion/lead_schema.json` | v4.5 export columns |
| `examples/` | Sample / live run markers |

## Roadmap

1. **Milestone 1** — vault, scoring, MAO, gates, CSV (this repo state)
2. **Milestone 2** — comp/rehab modules, live connectors, buyer matching
3. **Milestone 3** — Streamlit dashboard + CRM pipeline
4. **Milestone 4** — scheduled discovery + notifications
5. **Milestone 5** — outcome calibration