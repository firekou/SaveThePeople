"""D1-A product tests. Run against the private PostgreSQL 16 cluster (see README)."""
import json
import tempfile
from datetime import date
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.utils import OperationalError
from django.test import TestCase

from catalog.importer import ImportRejected, import_dataset
from catalog.models import HouseholdScopeDefinition, ImportRun, Region, Resource, ResourceVersion, Source
from catalog.visibility import catalog_visibility

DATASET = Path(settings.STP_SYNTHETIC_DATASET)
LISTED = ["TW-DEMO-LIVING-001", "TW-DEMO-EMERG-002", "TW-DEMO-EDU-003", "TW-DEMO-CHILD-004", "TW-DEMO-FOOD-005"]
AS_OF = "2026-10-13"


def _counts():
    return (Region.objects.count(), Source.objects.count(), HouseholdScopeDefinition.objects.count(),
            Resource.objects.count(), ResourceVersion.objects.count(), ImportRun.objects.count())


def _write_variant(mutate):
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    mutate(data)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(data, tmp, ensure_ascii=False)
    tmp.close()
    return tmp.name


class ImportTests(TestCase):
    def test_import_is_idempotent_and_keeps_history(self):
        run1 = import_dataset(str(DATASET))
        self.assertEqual(run1.created, {"regions": 3, "sources": 6, "scopes": 2, "resources": 6, "versions": 6})
        before = _counts()
        run2 = import_dataset(str(DATASET))
        self.assertEqual(run2.created["versions"], 0)
        self.assertEqual(run2.unchanged["versions"], 6)
        after = _counts()
        self.assertEqual(after[:5], before[:5])          # no duplicate rows
        self.assertEqual(after[5], before[5] + 1)        # each run is recorded

    def test_changed_version_content_is_rejected_without_partial_import(self):
        import_dataset(str(DATASET))
        before = _counts()
        first_hash = ResourceVersion.objects.get(resource__resource_key="TW-DEMO-LIVING-001").content_hash

        def mutate(d):
            d["resources"][0]["version"]["summary_plain"] = "被改寫的摘要（測試）"
        with self.assertRaises(ImportRejected):
            import_dataset(_write_variant(mutate))
        self.assertEqual(_counts(), before)
        self.assertEqual(ResourceVersion.objects.get(resource__resource_key="TW-DEMO-LIVING-001").content_hash, first_hash)

    def test_new_version_label_adds_history_without_overwriting(self):
        import_dataset(str(DATASET))

        def mutate(d):
            v = d["resources"][0]["version"]
            v["version_label"] = "2027"
            v["effective_from"], v["effective_to"] = "2027-01-01", "2027-12-31"
        import_dataset(_write_variant(mutate))
        labels = list(ResourceVersion.objects.filter(resource__resource_key="TW-DEMO-LIVING-001").order_by("id").values_list("version_label", flat=True))
        self.assertEqual(labels, ["2026", "2027"])

    def test_non_synthetic_flag_is_rejected_and_nothing_written(self):
        def mutate(d):
            d["is_synthetic"] = False
        with self.assertRaises(ImportRejected):
            import_dataset(_write_variant(mutate))
        self.assertEqual(_counts(), (0, 0, 0, 0, 0, 0))

    def test_external_source_url_is_rejected(self):
        def mutate(d):
            d["sources"][0]["url_or_ref"] = "https://example.com/real-looking"
        with self.assertRaises(ImportRejected):
            import_dataset(_write_variant(mutate))
        self.assertEqual(_counts(), (0, 0, 0, 0, 0, 0))

    def test_mid_file_failure_rolls_back_everything(self):
        def mutate(d):
            d["resources"][-1]["version"]["effective_unknown"] = True   # inconsistent with effective_to set
        with self.assertRaises(ImportRejected):
            import_dataset(_write_variant(mutate))
        self.assertEqual(_counts(), (0, 0, 0, 0, 0, 0))

    def test_database_rejects_non_synthetic_row(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Resource.objects.create(resource_key="TW-REAL-X", canonical_name="x", level="LOCAL", categories=["OTHER"], risk_tier="LOW", is_synthetic=False)

    def test_database_rejects_inconsistent_effective_unknown(self):
        import_dataset(str(DATASET))
        res = Resource.objects.get(resource_key="TW-DEMO-LIVING-001")
        with self.assertRaises(IntegrityError), transaction.atomic():
            ResourceVersion.objects.create(resource=res, version_label="bad", status="PUBLISHED", verification_level="V2", regions=["DEMO"],
                                           effective_to=date(2026, 12, 31), effective_unknown=True, application_window={"type": "ROLLING"},
                                           summary_plain="x", how_to_apply={}, content_hash="0" * 64)


class CatalogViewTests(TestCase):
    def setUp(self):
        import_dataset(str(DATASET))

    def get(self, url):
        return self.client.get(url, HTTP_HOST="127.0.0.1")

    def test_list_shows_five_and_hides_expired(self):
        r = self.get(f"/?as_of={AS_OF}")
        self.assertEqual(r.status_code, 200)
        body = r.content.decode()
        for key in LISTED:
            self.assertIn(key, body)
        self.assertNotIn("TW-DEMO-RENT-006", body)
        self.assertIn("共 5 項", body)
        self.assertIn("合成資料", body)

    def test_status_query_cannot_bypass_visibility(self):
        body = self.get(f"/?status=EXPIRED&as_of={AS_OF}").content.decode()
        self.assertNotIn("TW-DEMO-RENT-006", body)
        self.assertIn("共 5 項", body)

    def test_food_box_shows_unknown_period_needs_manual_check(self):
        body = self.get(f"/?as_of={AS_OF}").content.decode()
        self.assertIn("期限未知", body)
        detail = self.get(f"/resources/TW-DEMO-FOOD-005/?as_of={AS_OF}").content.decode()
        self.assertIn("截止日未知", detail)
        self.assertIn("人工確認", detail)
        self.assertIn("名額已滿", detail)

    def test_expired_resource_direct_link_is_history(self):
        r = self.get(f"/resources/TW-DEMO-RENT-006/?as_of={AS_OF}")
        self.assertEqual(r.status_code, 200)
        body = r.content.decode()
        self.assertIn("歷史版本", body)
        self.assertIn("已過期", body)
        self.assertIn("不在公開列表", body)

    def test_region_filters(self):
        a = self.get(f"/?region=DEMO-A&as_of={AS_OF}").content.decode()
        self.assertIn("TW-DEMO-EDU-003", a)
        self.assertIn("共 5 項", a)
        b = self.get(f"/?region=DEMO-B&as_of={AS_OF}").content.decode()
        self.assertNotIn("TW-DEMO-EDU-003", b)
        self.assertIn("共 4 項", b)
        county = self.get(f"/?region=DEMO&as_of={AS_OF}").content.decode()
        self.assertIn("共 5 項", county)

    def test_category_filter_and_empty_state(self):
        food = self.get(f"/?category=FOOD_GOODS&as_of={AS_OF}").content.decode()
        self.assertIn("TW-DEMO-FOOD-005", food)
        self.assertIn("共 1 項", food)
        empty = self.get(f"/?region=DEMO-B&category=EDUCATION&as_of={AS_OF}")
        self.assertEqual(empty.status_code, 200)
        self.assertIn("尚無已查核資源", empty.content.decode())
        self.assertIn("1957", empty.content.decode())

    def test_unknown_region_or_category_gives_empty_state_not_500(self):
        for url in ["/?region=NOWHERE", "/?category=NOPE", "/?region=DEMO-Z&category=LIVING"]:
            r = self.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertIn("查無此", r.content.decode())

    def test_missing_resource_is_404_page(self):
        r = self.get("/resources/TW-DEMO-NOPE-999/")
        self.assertEqual(r.status_code, 404)
        self.assertIn("找不到", r.content.decode())

    def test_internal_and_suspended_statuses(self):
        res = Resource.objects.create(resource_key="TW-DEMO-DRAFT-007", canonical_name="【合成】草稿", level="LOCAL", categories=["OTHER"], risk_tier="LOW")
        common = dict(verification_level="V1", regions=["DEMO"], effective_from=date(2026, 1, 1), effective_to=date(2026, 12, 31),
                      effective_unknown=False, application_window={"type": "ROLLING"}, summary_plain="草稿", how_to_apply={"channels": []}, content_hash="1" * 64)
        ResourceVersion.objects.create(resource=res, version_label="d", status="DRAFT", **common)
        self.assertNotIn("DRAFT-007", self.get(f"/?as_of={AS_OF}").content.decode())
        self.assertEqual(self.get("/resources/TW-DEMO-DRAFT-007/").status_code, 404)
        res2 = Resource.objects.create(resource_key="TW-DEMO-SUSP-008", canonical_name="【合成】暫停", level="LOCAL", categories=["OTHER"], risk_tier="LOW")
        ResourceVersion.objects.create(resource=res2, version_label="s", status="SUSPENDED", **common)
        self.assertNotIn("SUSP-008", self.get(f"/?as_of={AS_OF}").content.decode())
        r = self.get("/resources/TW-DEMO-SUSP-008/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("暫停推薦", r.content.decode())

    def test_not_yet_effective_is_listed_with_date_note(self):
        body = self.get("/?as_of=2026-07-01").content.decode()
        self.assertIn("2026-08-01 起適用", body)
        self.assertIn("TW-DEMO-EDU-003", body)

    def test_public_api_matches_list(self):
        r = self.get(f"/api/public/resources?as_of={AS_OF}")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["is_synthetic"])
        self.assertEqual(data["count"], 5)
        keys = [x["resource_key"] for x in data["results"]]
        self.assertEqual(keys, LISTED)
        food = next(x for x in data["results"] if x["resource_key"] == "TW-DEMO-FOOD-005")
        self.assertTrue(food["effective_unknown"])
        self.assertIn("期限未知", food["badges"])
        self.assertEqual(self.get("/api/public/resources?region=NOWHERE").json()["count"], 0)

    def test_first_screen_under_300kb(self):
        for url in [f"/?as_of={AS_OF}", f"/resources/TW-DEMO-FOOD-005/?as_of={AS_OF}"]:
            self.assertLess(len(self.get(url).content), 300 * 1024, url)

    def test_database_failure_shows_safe_page(self):
        self.client.raise_request_exception = False
        with mock.patch("catalog.views._region_index", side_effect=OperationalError("connection refused to /var/tmp/stp_d1a_pg/sock:54329 user stp_d1a")):
            r = self.get("/")
        self.assertEqual(r.status_code, 500)
        body = r.content.decode()
        self.assertIn("資料暫時無法載入", body)
        for leak in ["Traceback", "OperationalError", "stp_d1a", "54329", "connection refused", "/var/tmp"]:
            self.assertNotIn(leak, body)


class VisibilityUnitTests(TestCase):
    def setUp(self):
        import_dataset(str(DATASET))

    def _v(self, key):
        return Resource.objects.get(resource_key=key).current_version

    def test_rules(self):
        self.assertTrue(catalog_visibility(self._v("TW-DEMO-LIVING-001"), date(2026, 10, 13)).listed)
        food = catalog_visibility(self._v("TW-DEMO-FOOD-005"), date(2026, 10, 13))
        self.assertTrue(food.listed)
        self.assertIn("期限未知", food.badges)
        rent = catalog_visibility(self._v("TW-DEMO-RENT-006"), date(2026, 10, 13))
        self.assertFalse(rent.listed)
        self.assertEqual(rent.detail, "HISTORY")
        edu = catalog_visibility(self._v("TW-DEMO-EDU-003"), date(2026, 7, 1))
        self.assertTrue(edu.listed)
        self.assertTrue(any("起適用" in b for b in edu.badges))
        ended = catalog_visibility(self._v("TW-DEMO-LIVING-001"), date(2027, 3, 1))
        self.assertTrue(ended.listed)
        self.assertIn("期間已結束", ended.badges)
