"""Generate and validate the observability/support data inventory against code."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_ROOT = REPO_ROOT / "portal_bot"
EVENT_SCHEMA_PATH = (
    REPO_ROOT / "shared/contracts/observability/observability-event.schema.json"
)
OUTPUT_PATH = REPO_ROOT / "shared/contracts/observability/data-inventory.json"

if str(PORTAL_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTAL_ROOT))

import models  # noqa: E402


def _group(
    surface: str,
    group: str,
    fields: list[str],
    *,
    purpose: str,
    modes: list[str],
    retention: str,
    owner: str,
) -> dict[str, Any]:
    return {
        "surface": surface,
        "group": group,
        "fields": sorted(fields),
        "purpose": purpose,
        "modes": modes,
        "retention": retention,
        "owner": owner,
    }


GROUPS = [
    _group(
        "operational_event_envelope",
        "event_identity_and_taxonomy",
        [
            "component",
            "event_id",
            "name",
            "occurred_at_utc",
            "outcome",
            "privacy_class",
            "schema_version",
            "severity",
            "stage",
            "subsystem",
        ],
        purpose="Bounded lifecycle/failure classification and deduplication.",
        modes=["local_operational", "release_health", "support_bundle"],
        retention="local_android_7d_windows_14d; remote_release_health_90d",
        owner="observability",
    ),
    _group(
        "operational_event_envelope",
        "correlation",
        [
            "correlation.attempt_id",
            "correlation.generation",
            "correlation.parent_span_id",
            "correlation.run_id",
            "correlation.sequence",
            "correlation.span_id",
            "correlation.trace_id",
        ],
        purpose="Order one local attempt without account or device identity.",
        modes=["local_operational", "support_bundle"],
        retention="local_android_7d_windows_14d; bundle_profile_ttl",
        owner="client_runtime",
    ),
    _group(
        "operational_event_envelope",
        "build_identity",
        [
            "build.app_version",
            "build.architecture",
            "build.build_number",
            "build.candidate_label",
            "build.channel",
            "build.core_abi",
            "build.core_version",
            "build.git_revision",
            "build.platform",
        ],
        purpose="Separate exact build/platform/channel/Core cohorts.",
        modes=["local_operational", "release_health", "support_bundle"],
        retention="local_android_7d_windows_14d; remote_release_health_90d",
        owner="release_engineering",
    ),
    _group(
        "operational_event_envelope",
        "error_identity",
        ["error.code", "error.origin"],
        purpose="Bind a failure to the canonical safe error catalog.",
        modes=["local_operational", "release_health", "support_bundle"],
        retention="local_android_7d_windows_14d; remote_release_health_90d",
        owner="observability",
    ),
    _group(
        "operational_event_envelope",
        "allowlisted_attributes",
        [
            "attributes.artifact_kind",
            "attributes.bundle_item_count",
            "attributes.bundle_size_bytes",
            "attributes.bytes_in",
            "attributes.bytes_out",
            "attributes.contract_sha256",
            "attributes.contract_version",
            "attributes.core_abi",
            "attributes.crash_signature",
            "attributes.dns_ready",
            "attributes.dropped_count",
            "attributes.duration_ms",
            "attributes.effective_mtu",
            "attributes.egress_ready",
            "attributes.error_count",
            "attributes.from_version",
            "attributes.interface_ready",
            "attributes.journal_kind",
            "attributes.manifest_version",
            "attributes.network_class",
            "attributes.operation",
            "attributes.permission_state",
            "attributes.phase",
            "attributes.queue_depth",
            "attributes.reason_class",
            "attributes.retention_days",
            "attributes.retry_after_ms",
            "attributes.retry_count",
            "attributes.routes_ready",
            "attributes.segment_number",
            "attributes.status_class",
            "attributes.support_mode",
            "attributes.to_version",
            "attributes.update_channel",
        ],
        purpose="Bounded local/support evidence; never arbitrary metadata.",
        modes=["local_operational", "support_bundle"],
        retention="local_android_7d_windows_14d; bundle_profile_ttl",
        owner="observability",
    ),
    _group(
        "operational_event_envelope",
        "android_routing_count_only",
        ["attributes.selected_app_count"],
        purpose=(
            "Measure only the bounded number of selected Android routing apps; "
            "package names and identifiers remain device-local."
        ),
        modes=["local_operational", "release_health", "support_bundle"],
        retention="local_android_7d; remote_release_health_90d",
        owner="client_runtime",
    ),
    _group(
        "release_health_events",
        "persisted_projection",
        [
            "app_version",
            "architecture",
            "build_number",
            "candidate_label",
            "channel",
            "component",
            "core_abi",
            "core_version",
            "error_code",
            "error_origin",
            "event_id",
            "event_name",
            "git_revision",
            "id",
            "occurred_at",
            "outcome",
            "platform",
            "received_at",
            "schema_version",
            "selected_app_count",
            "severity",
            "stage",
            "subsystem",
        ],
        purpose="Identity-free exact-build release health and regression deltas.",
        modes=["aggregate_release_health"],
        retention="90_days",
        owner="release_observability",
    ),
    _group(
        "release_health_ingest_counters",
        "payload_free_counters",
        ["count", "reason", "updated_at"],
        purpose="Measure accept/quarantine health without retaining payloads.",
        modes=["server_security_audit"],
        retention="aggregate_counter_lifetime",
        owner="security_observability",
    ),
    _group(
        "release_known_issues",
        "version_scoped_issue_evidence",
        [
            "app_version",
            "build_number",
            "candidate_label",
            "created_at",
            "created_by_tg_id",
            "error_code",
            "id",
            "incident_ref",
            "issue_code",
            "platform",
            "release_ref",
            "safe_summary",
            "severity",
            "status",
            "title",
            "updated_at",
            "updated_by_tg_id",
        ],
        purpose="Track safe version/platform/error evidence and operator custody.",
        modes=["operator_support", "release_health"],
        retention="until_resolved_and_owner_reviewed",
        owner="release_operations",
    ),
    _group(
        "support_bundle_uploads",
        "case_binding_integrity_and_summary",
        [
            "app_version",
            "architecture",
            "build_number",
            "bundle_id",
            "completed_at",
            "content_type",
            "created_at",
            "diagnostic_profile",
            "expected_sha256",
            "expected_size_bytes",
            "expires_at",
            "failure_code",
            "id",
            "idempotency_key",
            "last_error_code",
            "last_phase",
            "object_name",
            "observed_attempts",
            "owner_account_id",
            "owner_binding_hash",
            "owner_tg_id",
            "platform",
            "proof_outcome",
            "received_size_bytes",
            "retention_held_at",
            "retention_hold",
            "retention_hold_reason",
            "status",
            "ticket_id",
            "updated_at",
            "upload_id",
            "validated_at",
        ],
        purpose="Authorize one case-bound encrypted object and expose a safe summary.",
        modes=["support_bundle"],
        retention="accepted_30d; rejected_7d; incomplete_until_expiry_plus_1d; hold_override",
        owner="support_security",
    ),
    _group(
        "support_bundle_chunks",
        "opaque_resumable_chunks",
        ["created_at", "id", "offset_bytes", "sha256", "size_bytes", "stored_name", "upload_id"],
        purpose="Resume an opaque encrypted upload and verify chunk integrity.",
        modes=["support_bundle"],
        retention="until_validation_or_upload_expiry",
        owner="support_ingest",
    ),
    _group(
        "support_bundle_access_audits",
        "privileged_access_custody",
        [
            "access_token_hash",
            "action",
            "actor_role",
            "actor_tg_id",
            "created_at",
            "expires_at",
            "grant_id",
            "id",
            "reason_code",
            "retention_hold",
            "ticket_id",
            "upload_id",
            "used_at",
        ],
        purpose="Audit actor-bound, reason-bound, single-use ciphertext access.",
        modes=["server_security_audit"],
        retention="365_days; hold_override",
        owner="security",
    ),
]


MODEL_SURFACES = {
    "release_health_events": models.ReleaseHealthEvent,
    "release_health_ingest_counters": models.ReleaseHealthIngestCounter,
    "release_known_issues": models.ReleaseKnownIssue,
    "support_bundle_uploads": models.SupportBundleUpload,
    "support_bundle_chunks": models.SupportBundleChunk,
    "support_bundle_access_audits": models.SupportBundleAccessAudit,
}


def _event_fields() -> set[str]:
    schema = json.loads(EVENT_SCHEMA_PATH.read_text(encoding="utf-8"))
    fields = {
        name
        for name in schema["properties"]
        if name not in {"correlation", "build", "error", "attributes"}
    }
    for prefix, definition in (
        ("correlation", "correlation"),
        ("build", "buildIdentity"),
        ("error", "errorIdentity"),
        ("attributes", "attributes"),
    ):
        fields.update(
            f"{prefix}.{name}"
            for name in schema["$defs"][definition]["properties"]
        )
    return fields


def _actual_fields(surface: str) -> set[str]:
    if surface == "operational_event_envelope":
        return _event_fields()
    model = MODEL_SURFACES[surface]
    return {column.name for column in model.__table__.columns}


def build_inventory() -> dict[str, Any]:
    by_surface: dict[str, set[str]] = {}
    for group in GROUPS:
        fields = set(group["fields"])
        if len(fields) != len(group["fields"]):
            raise ValueError(f"duplicate inventory field in {group['group']}")
        current = by_surface.setdefault(group["surface"], set())
        overlap = current & fields
        if overlap:
            raise ValueError(f"duplicate inventory ownership: {sorted(overlap)}")
        current.update(fields)
    for surface, fields in by_surface.items():
        actual = _actual_fields(surface)
        if fields != actual:
            raise ValueError(
                f"{surface} inventory drift: missing={sorted(actual - fields)} "
                f"extra={sorted(fields - actual)}"
            )
    if set(by_surface) != {"operational_event_envelope", *MODEL_SURFACES}:
        raise ValueError("inventory surface set is incomplete")
    return {
        "schema_version": 1,
        "contract_id": "pokrov.observability-data-inventory.v1",
        "threat_model": {
            "forbidden_assets": [
                "account_or_device_identity_in_release_health",
                "credentials_tokens_private_keys_or_raw_profiles",
                "destination_domains_ips_urls_or_selected_app_names",
                "plaintext_support_bundle_content",
            ],
            "threats": [
                "identity_correlation",
                "destination_leakage",
                "forged_build_or_error_evidence",
                "decompression_or_archive_abuse",
                "privileged_bundle_access_abuse",
                "unbounded_retention_or_volume",
            ],
            "controls": [
                "closed_schemas_and_error_catalog",
                "identity_free_release_health_projection",
                "android_routing_count_only_projection",
                "encrypted_case_bound_bundle",
                "rate_size_decompression_and_idempotency_limits",
                "actor_reason_ttl_and_audit_bound_access",
                "tested_retention_and_hold_policy",
            ],
        },
        "field_groups": sorted(GROUPS, key=lambda item: (item["surface"], item["group"])),
    }


def render_inventory() -> str:
    return json.dumps(build_inventory(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rendered = render_inventory()
        output = args.output.resolve()
        if args.write:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8", newline="\n")
            print(f"WROTE {output}")
            return 0
        if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
            print(f"STALE {output}", file=sys.stderr)
            return 1
        print(f"PASS {output}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
