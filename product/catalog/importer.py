"""Idempotent, fail-closed importer for the synthetic catalog dataset.

Rules (BATCH1 B2-4 / DATA_MODEL §2.4):
- The file must declare `is_synthetic: true`; otherwise nothing is written.
- Published version content is immutable: re-importing the same
  (resource_key, version_label) with different content is rejected; a new
  version needs a new version_label. Re-importing identical content is a no-op.
- All writes happen in one transaction: any rejection leaves the DB untouched.
"""
import hashlib
import json
from datetime import datetime, timezone

from django.db import transaction

from .models import HouseholdScopeDefinition, ImportRun, Region, Resource, ResourceVersion, Source

SYNTHETIC_HOST = "example.invalid"
VERSION_FIELDS = ["version_label", "status", "verification_level", "regions", "effective_from", "effective_to",
                  "effective_unknown", "application_window", "summary_plain", "amount_or_service", "how_to_apply",
                  "capacity_status", "capacity_confirmed_at", "stacking_rules", "source_ids", "conflict_status"]


class ImportRejected(Exception):
    """Raised before or during import; the transaction is rolled back."""


def canonical_hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def _date(v):
    return None if v in (None, "") else datetime.strptime(v, "%Y-%m-%d").date()


def validate_dataset(data: dict) -> None:
    if not isinstance(data, dict) or data.get("is_synthetic") is not True:
        raise ImportRejected("dataset does not declare is_synthetic: true; refusing to import")
    for s in data.get("sources", []):
        ref = s.get("url_or_ref", "")
        if ref.startswith(("http://", "https://")) and SYNTHETIC_HOST not in ref.split("/")[2]:
            raise ImportRejected(f"source {s.get('id')} points outside {SYNTHETIC_HOST}; refusing non-synthetic data")
    for r in data.get("resources", []):
        v = r.get("version", {})
        if not r.get("resource_key", "").startswith("TW-DEMO-"):
            raise ImportRejected(f"resource {r.get('resource_key')} is not a TW-DEMO synthetic key")
        if bool(v.get("effective_unknown")) != (v.get("effective_to") in (None, "")):
            raise ImportRejected(f"{r['resource_key']}: effective_unknown must equal (effective_to is null)")
        if v.get("status") not in ResourceVersion.STATUSES:
            raise ImportRejected(f"{r['resource_key']}: unknown version status {v.get('status')}")
        for sid in v.get("source_ids", []):
            if sid not in {s["id"] for s in data.get("sources", [])}:
                raise ImportRejected(f"{r['resource_key']}: unknown source {sid}")


def import_dataset(path: str) -> ImportRun:
    started = datetime.now(timezone.utc)
    with open(path, "rb") as fh:
        raw = fh.read()
    data = json.loads(raw.decode("utf-8"))
    validate_dataset(data)
    created = {"regions": 0, "sources": 0, "scopes": 0, "resources": 0, "versions": 0}
    unchanged = {"regions": 0, "sources": 0, "scopes": 0, "resources": 0, "versions": 0}

    with transaction.atomic():
        regions = data.get("regions", {})
        # parents first
        for code, spec in sorted(regions.items(), key=lambda kv: 0 if "parent" not in kv[1] else 1):
            parent = Region.objects.get(code=spec["parent"]) if spec.get("parent") else None
            obj, was_created = Region.objects.get_or_create(code=code, defaults={"name": spec["name"], "parent": parent})
            if was_created:
                created["regions"] += 1
            elif obj.name != spec["name"] or obj.parent != parent:
                raise ImportRejected(f"region {code} differs from the stored definition; regions are not rewritten")
            else:
                unchanged["regions"] += 1

        for s in data.get("sources", []):
            fields = {"url_or_ref": s["url_or_ref"], "source_type": s["source_type"], "tier": s["tier"],
                      "retrieved_at": datetime.fromisoformat(s["retrieved_at"]), "status": s["status"]}
            obj, was_created = Source.objects.get_or_create(source_id=s["id"], defaults=fields)
            if was_created:
                created["sources"] += 1
            elif any(getattr(obj, k) != v for k, v in fields.items()):
                raise ImportRejected(f"source {s['id']} differs from the stored record; sources are not rewritten by import")
            else:
                unchanged["sources"] += 1

        for sc in data.get("household_scopes", []):
            fields = {"label_plain": sc["label_plain"], "member_inclusion": sc["member_inclusion"],
                      "income_definition": sc["income_definition"], "source_ref": sc["source_ref"]}
            obj, was_created = HouseholdScopeDefinition.objects.get_or_create(scope_key=sc["scope_key"], defaults=fields)
            if was_created:
                created["scopes"] += 1
            elif any(getattr(obj, k) != v for k, v in fields.items()):
                raise ImportRejected(f"scope {sc['scope_key']} differs from the stored record")
            else:
                unchanged["scopes"] += 1

        for r in data.get("resources", []):
            rfields = {"canonical_name": r["canonical_name"], "level": r["level"], "categories": r["categories"], "risk_tier": r["risk_tier"]}
            res, was_created = Resource.objects.get_or_create(resource_key=r["resource_key"], defaults=rfields)
            if was_created:
                created["resources"] += 1
            elif any(getattr(res, k) != v for k, v in rfields.items()):
                raise ImportRejected(f"resource {r['resource_key']} header differs from the stored record")
            else:
                unchanged["resources"] += 1

            v = r["version"]
            vhash = canonical_hash({k: v.get(k) for k in VERSION_FIELDS})
            existing = ResourceVersion.objects.filter(resource=res, version_label=v["version_label"]).first()
            if existing is not None:
                if existing.content_hash != vhash:
                    raise ImportRejected(
                        f"{r['resource_key']} version {v['version_label']} already exists with different content; "
                        "published versions are immutable — add a new version_label instead")
                unchanged["versions"] += 1
                continue
            ver = ResourceVersion.objects.create(
                resource=res, version_label=v["version_label"], status=v["status"],
                verification_level=v["verification_level"], regions=v["regions"],
                effective_from=_date(v.get("effective_from")), effective_to=_date(v.get("effective_to")),
                effective_unknown=bool(v.get("effective_unknown")), application_window=v["application_window"],
                summary_plain=v["summary_plain"], amount_or_service=v.get("amount_or_service"),
                how_to_apply=v["how_to_apply"], capacity_status=v.get("capacity_status", "UNKNOWN"),
                capacity_confirmed_at=_date(v.get("capacity_confirmed_at")), stacking_rules=v.get("stacking_rules"),
                conflict_status=v.get("conflict_status", "NONE"), content_hash=vhash)
            ver.sources.set(Source.objects.filter(source_id__in=v["source_ids"]))
            created["versions"] += 1

        return ImportRun.objects.create(started_at=started, file_sha256=hashlib.sha256(raw).hexdigest(),
                                        created=created, unchanged=unchanged)
