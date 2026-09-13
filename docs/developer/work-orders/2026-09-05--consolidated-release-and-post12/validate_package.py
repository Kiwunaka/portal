"""Read-only structural check for this imported work-order package."""

import csv
import hashlib
import json
import re
from pathlib import Path


package = Path(__file__).resolve().parent
manifest = json.loads((package / "evidence/import-manifest.json").read_text(encoding="utf-8"))
assert len(manifest["files"]) == 13
# These exact owner-approved notices were added after import. Preserve the
# original manifest hashes and verify the remaining imported text unchanged.
owner_notices = {
    "00_START_HERE.md": (
        "Актуальная поправка: [решением владельца от 2026-09-13](OWNER-DECISIONS-2026-09-13.md)\n"
        "AWG2 исключён из обязательной приёмки и дальнейшего развития всей программы;\n"
        "активный AWG-контур — AWG3.1. Старые требования и результаты AWG2 ниже сохранены как история.\n\n"
    ),
    "01_SCOPE_AND_CORRECTIONS.md": (
        "**Поправка владельца 2026-09-13:** активный AWG-контур — AWG3.1; отдельные\n"
        "AWG2 gates и дальнейшее развитие исключены из обязательного объёма.\n"
        "Точные границы и сохранение legacy consumers — в [решении](OWNER-DECISIONS-2026-09-13.md).\n\n"
    ),
}
for entry in manifest["files"]:
    content = (package / entry["name"]).read_text(encoding="utf-8")
    if entry["name"] in owner_notices:
        notice = owner_notices[entry["name"]]
        assert content.count(notice) == 1, entry["name"]
        content = content.replace(notice, "", 1)
    assert hashlib.sha256(content.encode("utf-8")).hexdigest() == entry["sha256"], entry["name"]


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


register = rows(package / "R12-REGISTER.csv")
backlog = (package / "03_RELEASE_BACKLOG_83.md").read_text(encoding="utf-8")
source_ids = re.findall(r"^### (R12-[A-Z]\d+) —", backlog, re.MULTILINE)
assert len(register) == len(source_ids) == len(set(source_ids)) == 83
assert [row["id"] for row in register] == source_ids
legacy_path = package.parent / "2026-08-21--release-1.2.0-megaplan/EXECUTION-LEDGER.csv"
legacy = rows(legacy_path)
references = rows(package / "LEGACY-378-REFERENCE.csv")
assert len(legacy) == len(references) == 378
assert [(r["plan"], r["id"]) for r in legacy] == [(r["plan"], r["id"]) for r in references]
baseline = json.loads((package / "evidence/baseline.json").read_text(encoding="utf-8"))
assert hashlib.sha256(legacy_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest() == baseline["legacy_ledger_utf8_lf_sha256"]

checked = 0
for document in package.glob("*.md"):
    content = re.sub(r"```.*?```", "", document.read_text(encoding="utf-8"), flags=re.DOTALL)
    for link in re.findall(r"\]\(([^)]+)\)", content):
        if link.startswith(("http:", "https:", "mailto:", "#", "/")):
            continue
        target = link.split("#")[0]
        if target:
            assert (document.parent / target).exists(), (document.name, link)
            checked += 1
print(f"PASS: 13 original section hashes and 2 exact owner notices, 83 R12 IDs, 378 retained legacy IDs and ledger hash, {checked} local file links")
