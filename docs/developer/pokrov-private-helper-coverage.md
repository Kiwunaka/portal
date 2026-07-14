# POKROV Private Helper Coverage Matrix

Last updated: 2026-07-05

## Purpose

This generated matrix expands the `private_inventory_only` tier from
`pokrov-symbol-coverage-audit.csv` into per-symbol expected behavior,
risk, proof status, and next action. It does not claim dedicated tests for
private helpers; it makes Q-001 measurable if the owner requires stricter
one-test-per-private-helper coverage.

## Canonical Files

- CSV: [pokrov-private-helper-coverage.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-private-helper-coverage.csv)
- Source symbol coverage: [pokrov-symbol-coverage-audit.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-symbol-coverage-audit.csv)
- Low-level inventory: [pokrov-code-function-inventory.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-code-function-inventory.csv)
- Generator: [generate_private_helper_coverage.py](C:/Users/kiwun/Documents/ai/VPN/scripts/generate_private_helper_coverage.py)

## Current Counts

| Metric | Count |
| --- | ---: |
| Private helper rows | 23 |
| Rows needing Q-001 owner decision | 23 |
| High risk rows | 0 |
| Medium risk rows | 2 |
| Low risk rows | 21 |

### By Private Helper Area

| Label | Count |
| --- | ---: |
| `client_private_ui_helper` | 9 |
| `private_implementation_helper` | 14 |

### By Risk Tier

| Label | Count |
| --- | ---: |
| `low` | 21 |
| `medium` | 2 |

### By Language

| Label | Count |
| --- | ---: |
| `dart` | 9 |
| `python` | 12 |
| `tsx` | 2 |

### By Current Status

| Label | Count |
| --- | ---: |
| `source_inventory_only` | 23 |

## Completion Rule

If the owner chooses `ACCEPT_STORY_AND_SYMBOL_TIERS` or
`REQUIRE_PUBLIC_AND_ENTRYPOINT_ONLY`, these rows remain tracked as
`source_inventory_only` and Q-001 can close after the policy decision is
recorded. If the owner chooses `REQUIRE_ONE_TEST_PER_PRIVATE_HELPER`,
each row must receive a dedicated test reference or explicit owner waiver
before Q-001 can close.

## Regeneration

```powershell
python scripts\generate_private_helper_coverage.py
```
