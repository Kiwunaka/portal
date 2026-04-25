# Tech Debt Register

Status: draft

| ID | Area | Debt | Impact | Owner | Status |
|---|---|---|---|---|---|
| TD-001 | git | Platform candidate inherits a large dirty local beta patch. | Promotion/rebase risk. | W10 | open |
| TD-002 | git | Platform local base is behind `origin/master`. | Public release branch may need rebase/merge before push. | W10 | open |
| TD-003 | client | Public Android release requires physical audit and signing not available in repo. | Android cannot be public-ready from local code alone. | W07/W09 | open |
| TD-004 | payments | Provider live acceptance/webhook proof is external. | Checkout cannot be public-ready without live evidence or disabled state. | W06 | open |
| TD-005 | ops | Brain-origin/RU-origin checks require access. | Release evidence may be blocked by access. | W08 | open |

