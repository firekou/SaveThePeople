"""Minimal catalog subset of DATA_MODEL_AND_STATE_MACHINES §2.1–2.4.

Every table carries `is_synthetic` with a database CHECK constraint that only
accepts True: this product build can never hold a non-synthetic row.
"""
from django.db import models
from django.db.models import Q


class SyntheticOnly(models.Model):
    is_synthetic = models.BooleanField(default=True)

    class Meta:
        abstract = True


def synthetic_constraint(name):
    return models.CheckConstraint(condition=Q(is_synthetic=True), name=name)


class Region(SyntheticOnly):
    code = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=128)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")

    class Meta:
        constraints = [synthetic_constraint("catalog_region_synthetic_only")]

    def ancestors_and_self(self):
        node, out = self, []
        while node is not None:
            out.append(node.code)
            node = node.parent
        return out

    def __str__(self):
        return f"{self.name} ({self.code})"


class Source(SyntheticOnly):
    SOURCE_TYPES = ["WEB_PAGE", "PDF", "ANNOUNCEMENT", "REGULATION", "FORM", "PHONE_CONFIRMATION", "EMAIL_CONFIRMATION", "IN_PERSON"]
    TIERS = ["S1_LAW", "S2_CENTRAL", "S3_LOCAL", "S4_PUBLIC_AGENCY", "S5_NGO", "S6_SECONDARY"]
    STATUSES = ["ACTIVE", "MOVED", "BROKEN", "SUPERSEDED"]

    source_id = models.CharField(max_length=32, unique=True)
    url_or_ref = models.TextField()
    source_type = models.CharField(max_length=32, choices=[(s, s) for s in SOURCE_TYPES])
    tier = models.CharField(max_length=32, choices=[(t, t) for t in TIERS])
    retrieved_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=[(s, s) for s in STATUSES])

    class Meta:
        constraints = [synthetic_constraint("catalog_source_synthetic_only")]
        ordering = ["source_id"]

    @property
    def is_link(self):
        return self.url_or_ref.startswith(("http://", "https://"))

    def __str__(self):
        return self.source_id


class HouseholdScopeDefinition(SyntheticOnly):
    scope_key = models.CharField(max_length=32, unique=True)
    label_plain = models.CharField(max_length=200)
    member_inclusion = models.JSONField()
    income_definition = models.JSONField()
    source_ref = models.CharField(max_length=200)

    class Meta:
        constraints = [synthetic_constraint("catalog_scope_synthetic_only")]
        ordering = ["scope_key"]

    def __str__(self):
        return self.scope_key


class Resource(SyntheticOnly):
    LEVELS = ["CENTRAL", "LOCAL", "PRIVATE"]
    CATEGORIES = ["LIVING", "EMERGENCY", "CHILD_YOUTH", "EDUCATION", "FOOD_GOODS", "HOUSING", "EMPLOYMENT", "HEALTH", "CARE", "LEGAL", "OTHER"]
    RISK_TIERS = ["HIGH", "MEDIUM", "LOW"]

    resource_key = models.CharField(max_length=64, unique=True)
    canonical_name = models.CharField(max_length=200)
    level = models.CharField(max_length=16, choices=[(l, l) for l in LEVELS])
    categories = models.JSONField(default=list)
    risk_tier = models.CharField(max_length=8, choices=[(r, r) for r in RISK_TIERS])

    class Meta:
        constraints = [synthetic_constraint("catalog_resource_synthetic_only")]
        ordering = ["resource_key"]

    @property
    def current_version(self):
        """Most recently imported version (imports never overwrite history)."""
        return self.versions.order_by("-id").first()

    def __str__(self):
        return self.resource_key


class ResourceVersion(SyntheticOnly):
    STATUSES = ["CANDIDATE", "DRAFT", "IN_REVIEW", "PUBLISHED", "NEEDS_RECHECK", "SUSPENDED", "EXPIRED", "SUPERSEDED", "RETIRED"]
    VERIFICATION = ["V0", "V1", "V2", "V3"]
    CAPACITY = ["OPEN", "LIMITED", "FULL", "UNKNOWN"]
    CONFLICT = ["NONE", "OPEN", "RESOLVED"]

    resource = models.ForeignKey(Resource, on_delete=models.PROTECT, related_name="versions")
    version_label = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=[(s, s) for s in STATUSES])
    verification_level = models.CharField(max_length=2, choices=[(v, v) for v in VERIFICATION])
    regions = models.JSONField(default=list)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    effective_unknown = models.BooleanField()
    application_window = models.JSONField()
    summary_plain = models.TextField()
    amount_or_service = models.JSONField(null=True, blank=True)
    how_to_apply = models.JSONField()
    capacity_status = models.CharField(max_length=8, choices=[(c, c) for c in CAPACITY], default="UNKNOWN")
    capacity_confirmed_at = models.DateField(null=True, blank=True)
    stacking_rules = models.JSONField(null=True, blank=True)
    conflict_status = models.CharField(max_length=8, choices=[(c, c) for c in CONFLICT], default="NONE")
    sources = models.ManyToManyField(Source, related_name="versions")
    content_hash = models.CharField(max_length=64)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            synthetic_constraint("catalog_version_synthetic_only"),
            models.UniqueConstraint(fields=["resource", "version_label"], name="catalog_version_unique_label"),
            # effective_unknown must equal "effective_to is null" (DATA_MODEL §2.4.1)
            models.CheckConstraint(
                condition=(Q(effective_unknown=True, effective_to__isnull=True) | Q(effective_unknown=False, effective_to__isnull=False)),
                name="catalog_version_effective_unknown_consistent",
            ),
        ]
        ordering = ["resource__resource_key", "id"]

    @property
    def last_source_retrieved_at(self):
        """Newest source retrieval date, shown as the catalog's 查核日期 for this synthetic set."""
        dates = [s.retrieved_at for s in self.sources.all()]
        return max(dates) if dates else None

    def __str__(self):
        return f"{self.resource.resource_key}@{self.version_label}"


class ImportRun(SyntheticOnly):
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(auto_now_add=True)
    file_sha256 = models.CharField(max_length=64)
    created = models.JSONField(default=dict)
    unchanged = models.JSONField(default=dict)

    class Meta:
        constraints = [synthetic_constraint("catalog_importrun_synthetic_only")]
        ordering = ["-id"]
