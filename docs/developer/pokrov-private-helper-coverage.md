# POKROV Private Helper Coverage Matrix

Last updated: 2026-07-21

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
| Private helper rows | 953 |
| Accepted Q-001 policy rows | 953 |
| Rows needing Q-001 owner decision | 0 |
| High risk rows | 5 |
| Medium risk rows | 177 |
| Low risk rows | 771 |

### By Private Helper Area

| Label | Count |
| --- | ---: |
| `client_desktop_host_helper` | 5 |
| `client_feature_copy_or_logic_helper` | 152 |
| `client_private_ui_helper` | 32 |
| `private_implementation_helper` | 739 |
| `webapp_private_ui_helper` | 25 |

### By Risk Tier

| Label | Count |
| --- | ---: |
| `high` | 5 |
| `low` | 771 |
| `medium` | 177 |

### By Language

| Label | Count |
| --- | ---: |
| `dart` | 309 |
| `python` | 607 |
| `tsx` | 37 |

### By Current Status

| Label | Count |
| --- | ---: |
| `source_inventory_only` | 953 |

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
