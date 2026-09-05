"""Read-only structural check for this imported work-order package."""

import csv
import hashlib
import json
import re
from pathlib import Path


package = Path(__file__).resolve().parent
manifest = json.loads((package / "evidence/import-manifest.json").read_text(encoding="utf-8"))
assert len(manifest["files"]) == 13
for entry in manifest["files"]:
    content = (package / entry["name"]).read_text(encoding="utf-8").encode("utf-8")
    assert hashlib.sha256(content).hexdigest() == entry["sha256"], entry["name"]


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
print(f"PASS: 13 imported section hashes, 83 R12 IDs, 378 retained legacy IDs and ledger hash, {checked} local file links")
