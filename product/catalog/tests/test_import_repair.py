"""D1A-01 / D1A-02 regression tests: per-record synthetic flags and source URL validation.

Each negative case asserts (a) ImportRejected with the expected reason and (b) that every table
and ImportRun keep their pre-import counts — both on an empty DB and on a DB that already holds
the legal dataset.
"""
import json
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from catalog.importer import ImportRejected, import_dataset, source_ref_problem, validate_dataset
from catalog.models import HouseholdScopeDefinition, ImportRun, Region, Resource, ResourceVersion, Source

DATASET = Path(settings.STP_SYNTHETIC_DATASET)


def _data():
    return json.loads(DATASET.read_text(encoding="utf-8"))


def _write(data):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(data, tmp, ensure_ascii=False)
    tmp.close()
    return tmp.name


def _counts():
    return (Region.objects.count(), Source.objects.count(), HouseholdScopeDefinition.objects.count(),
            Resource.objects.count(), ResourceVersion.objects.count(), ImportRun.objects.count())


# (label, mutate) — one per importable record type, with false and with illegal non-boolean values
FLAG_CASES = []
for bad in (False, "true", 1, None, "false", 0):
    FLAG_CASES += [
        (f"region={bad!r}", lambda d, b=bad: d["regions"]["DEMO-A"].__setitem__("is_synthetic", b)),
        (f"source={bad!r}", lambda d, b=bad: d["sources"][2].__setitem__("is_synthetic", b)),
        (f"scope={bad!r}", lambda d, b=bad: d["household_scopes"][1].__setitem__("is_synthetic", b)),
        (f"resource={bad!r}", lambda d, b=bad: d["resources"][0].__setitem__("is_synthetic", b)),
        (f"version={bad!r}", lambda d, b=bad: d["resources"][4]["version"].__setitem__("is_synthetic", b)),
        (f"rule={bad!r}", lambda d, b=bad: d["resources"][1]["rule"].__setitem__("is_synthetic", b)),
    ]

URL_REJECT = {
    "https://example.invalid.attacker.invalid/path": "is not exactly example.invalid",
    "https://attacker.invalid/example.invalid": "is not exactly example.invalid",
    "https://sub.example.invalid/x": "is not exactly example.invalid",
    "https://example.invalid./x": "is not exactly example.invalid",
    "https://example.invalid@attacker.invalid/x": "userinfo",
    "https://user:pw@example.invalid/x": "userinfo",
    "https://example.invalid:443/x": "explicit port",
    "https://example.invalid:99999/x": "unparseable URL",
    "ftp://example.invalid/x": "scheme 'ftp' not allowed",
    "javascript:alert(1)": "scheme 'javascript' not allowed",
    "file:///etc/passwd": "scheme 'file' not allowed",
    "https:///no-host": "no hostname",
    "https://[::1/x": "unparseable URL",
    "https://example.invalid\\@attacker.invalid/": "backslash",
    "https://example.invalid/a b": "whitespace",
    "https://example.invalid/\tx": "control character",
    "見官網 https://attacker.invalid/x": "embedded URL",
    "www.attacker.invalid/x": "embedded URL",
    "": "empty",
}
URL_ACCEPT = [
    "https://example.invalid/demo-county/x",
    "http://example.invalid/",
    "HTTPS://EXAMPLE.INVALID/Case",          # scheme/host are case-insensitive by RFC 3986 → normalised
    "https://example.invalid",
    "電話確認：示範食物互助協會 服務組 2026-10-02（合成）",   # existing synthetic non-URL reference
]


class PerRecordSyntheticFlagTests(TestCase):
    def test_original_fixture_is_unchanged_and_still_imports(self):
        # compatibility path: the fixture declares is_synthetic only at file level
        self.assertEqual(sum("is_synthetic" in r for r in _data()["resources"]), 0)
        run = import_dataset(str(DATASET))
        self.assertEqual(run.created, {"regions": 3, "sources": 6, "scopes": 2, "resources": 6, "versions": 6})
        self.assertEqual(run.inherited_flag, {"regions": 3, "sources": 6, "scopes": 2, "resources": 6, "versions": 6})
        for model in (Region, Source, HouseholdScopeDefinition, Resource, ResourceVersion, ImportRun):
            self.assertEqual(model.objects.filter(is_synthetic=False).count(), 0)
        # second import: idempotent, nothing new
        run2 = import_dataset(str(DATASET))
        self.assertEqual(run2.created, {"regions": 0, "sources": 0, "scopes": 0, "resources": 0, "versions": 0})

    def test_explicit_true_per_record_is_accepted(self):
        d = _data()
        for r in d["resources"]:
            r["is_synthetic"] = True
            r["version"]["is_synthetic"] = True
        for s in d["sources"]:
            s["is_synthetic"] = True
        run = import_dataset(_write(d))
        self.assertEqual(run.created["resources"], 6)
        self.assertNotIn("resources", run.inherited_flag)
        self.assertNotIn("sources", run.inherited_flag)

    def test_explicit_false_or_illegal_flag_rejected_on_empty_db(self):
        for label, mutate in FLAG_CASES:
            with self.subTest(case=label):
                d = _data()
                mutate(d)
                with self.assertRaisesRegex(ImportRejected, "is_synthetic"):
                    import_dataset(_write(d))
                self.assertEqual(_counts(), (0, 0, 0, 0, 0, 0))

    def test_explicit_false_rejected_on_populated_db_without_any_change(self):
        import_dataset(str(DATASET))
        before = _counts()
        for label, mutate in FLAG_CASES:
            with self.subTest(case=label):
                d = _data()
                mutate(d)
                d["resources"][0]["version"]["version_label"] = "2027-new"   # would otherwise be a new row
                with self.assertRaisesRegex(ImportRejected, "is_synthetic"):
                    import_dataset(_write(d))
                self.assertEqual(_counts(), before)

    def test_orm_default_cannot_relabel(self):
        # the validator runs before any write; even if it were bypassed, writes pass the record's flag
        from catalog import importer
        d = _data()
        d["resources"][0]["is_synthetic"] = False
        orig = importer.validate_dataset
        importer.validate_dataset = lambda data: None   # simulate a missing validator
        try:
            with self.assertRaises(Exception):          # DB CHECK rejects the explicit False
                import_dataset(_write(d))
        finally:
            importer.validate_dataset = orig
        self.assertEqual(Resource.objects.count(), 0)


class SourceUrlTests(TestCase):
    def test_reason_for_each_rejected_reference(self):
        for ref, reason in URL_REJECT.items():
            with self.subTest(ref=ref):
                problem = source_ref_problem(ref)
                self.assertIsNotNone(problem)
                self.assertIn(reason, problem)

    def test_accepted_references(self):
        for ref in URL_ACCEPT:
            with self.subTest(ref=ref):
                self.assertIsNone(source_ref_problem(ref))

    def test_rejected_url_writes_nothing_on_empty_and_populated_db(self):
        for populated in (False, True):
            if populated:
                import_dataset(str(DATASET))
            before = _counts()
            for ref in URL_REJECT:
                with self.subTest(populated=populated, ref=ref):
                    d = _data()
                    d["sources"][0]["url_or_ref"] = ref
                    d["sources"][0]["id"] = "S-9999"
                    d["resources"][0]["version"]["source_ids"] = ["S-9999"]
                    d["resources"][0]["version"]["version_label"] = "2027-url"
                    with self.assertRaises(ImportRejected):
                        import_dataset(_write(d))
                    self.assertEqual(_counts(), before)

    def test_validator_makes_no_network_calls(self):
        import socket
        orig = socket.socket.connect
        socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(AssertionError("network used"))
        try:
            for ref in list(URL_REJECT) + URL_ACCEPT:
                source_ref_problem(ref)
            d = _data()
            validate_dataset(d)
        finally:
            socket.socket.connect = orig
