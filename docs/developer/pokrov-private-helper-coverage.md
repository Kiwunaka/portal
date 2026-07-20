# POKROV Private Helper Coverage Matrix

Last updated: 2026-07-20

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
| Private helper rows | 193 |
| Accepted Q-001 policy rows | 193 |
| Rows needing Q-001 owner decision | 0 |
| High risk rows | 0 |
| Medium risk rows | 8 |
| Low risk rows | 185 |

### By Private Helper Area

| Label | Count |
| --- | ---: |
| `client_feature_copy_or_logic_helper` | 1 |
| `client_private_ui_helper` | 17 |
| `private_implementation_helper` | 161 |
| `webapp_private_ui_helper` | 14 |

### By Risk Tier

| Label | Count |
| --- | ---: |
| `low` | 185 |
| `medium` | 8 |

### By Language

| Label | Count |
| --- | ---: |
| `dart` | 18 |
| `python` | 159 |
| `tsx` | 16 |

### By Current Status

| Label | Count |
| --- | ---: |
| `source_inventory_only` | 193 |

## Completion Rule

Owner accepted `ACCEPT_STORY_AND_SYMBOL_TIERS` on 2026-06-28, so
these rows remain tracked as `source_inventory_only`.
Q-001 is answered and nonblocking. If the owner later requires
`REQUIRE_ONE_TEST_PER_PRIVATE_HELPER`, each row must receive a dedicated
test reference or explicit owner waiver under that stricter policy.

## Regeneration

```powershell
python scripts\generate_private_helper_coverage.py
```
