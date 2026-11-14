# wholesale-invest

Metro Detroit residential wholesaling — **Lead Generation Agent v4.5** configuration and prompts.

## Repository layout

| Path | Purpose |
|------|---------|
| `agents/lead_gen_v4_5.md` | Drop-in system prompt for the lead gen agent |
| `config/lead_gen.yml` | Default `LeadGenConfig` and NL override examples |
| `config/markets.yml` | Top 20 tiers, phases, motivation keywords, risk hints |
| `config/scoring.yml` | Final Score v4.5 components and priority bands |
| `notion/lead_schema.json` | Column order + JSON Schema for Sheets/Notion |
| `examples/phase1_sample_run.md` | EXAMPLE/TRAINING output shape (Phase 1) |

## Quick start

1. Point your agent runtime at `agents/lead_gen_v4_5.md` as the system prompt.
2. Load or merge `config/lead_gen.yml` for each run; override with natural language (see `examples` in that file).
3. Import rows using column order from `notion/lead_schema.json`.
4. Connect live sourcing (Zillow FSBO, Marketplace, Craigslist) in your worker layer; until then use `examples/phase1_sample_run.md` for format QA only.

## Phase map

- **Phase 1:** Ypsilanti + Warren (default)
- **Phase 2:** + Sterling Heights + Detroit (one ZIP)
- **Phase 3:** + Royal Oak + Westland
- **Phase 4:** All Top 20 markets (`config/markets.yml`)

## Safety

Live runs must not invent addresses, seller names, or phone numbers. Tag unsourced rows with `RunMetadata.dataClassification: EXAMPLE` or `TRAINING`.