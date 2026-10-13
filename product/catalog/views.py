from datetime import date

from django.http import Http404, JsonResponse
from django.shortcuts import render

from .models import Region, Resource, ResourceVersion
from .visibility import CAPACITY_LABELS, catalog_visibility

CATEGORY_LABELS = {
    "LIVING": "生活／急難救助", "EMERGENCY": "急難救助", "CHILD_YOUTH": "兒少", "EDUCATION": "就學",
    "FOOD_GOODS": "食物／物資", "HOUSING": "居住", "EMPLOYMENT": "就業", "HEALTH": "健康",
    "CARE": "照顧", "LEGAL": "法律", "OTHER": "其他",
}
LEVEL_LABELS = {"CENTRAL": "中央", "LOCAL": "地方", "PRIVATE": "民間"}
CHANNEL_LABELS = {"IN_PERSON": "臨櫃", "MAIL": "郵寄", "ONLINE": "線上", "SCHOOL": "學校", "REFERRAL": "據點轉介", "PHONE": "電話"}
PROXY_LABELS = {"YES": "可委託他人代辦", "NO": "須本人辦理", "CONDITIONAL": "有條件可代辦", "UNKNOWN": "可否代辦未知，需確認"}


def _as_of(request) -> date:
    raw = request.GET.get("as_of")
    if raw:
        try:
            return date.fromisoformat(raw)
        except ValueError:
            pass
    return date.today()


def _region_index():
    return {r.code: r for r in Region.objects.select_related("parent")}


def _matches_region(version_regions, selected: Region, index) -> bool:
    """A version applies to the selected area if any of its regions is the area or one of its ancestors,
    or if the selected area contains one of its regions (county view shows district-only items)."""
    wanted = set(selected.ancestors_and_self())
    for code in version_regions:
        if code in wanted:
            return True
        node = index.get(code)
        if node is not None and selected.code in node.ancestors_and_self():
            return True
    return False


def _listed_items(as_of, region=None, category=None):
    index = _region_index()
    items = []
    for res in Resource.objects.prefetch_related("versions__sources"):
        ver = res.current_version
        if ver is None:
            continue
        vis = catalog_visibility(ver, as_of)
        if not vis.listed:
            continue
        if region is not None and not _matches_region(ver.regions, region, index):
            continue
        if category and category not in res.categories:
            continue
        items.append({"resource": res, "version": ver, "vis": vis,
                      "region_names": [index[c].name if c in index else c for c in ver.regions],
                      "category_labels": [CATEGORY_LABELS.get(c, c) for c in res.categories],
                      "level_label": LEVEL_LABELS.get(res.level, res.level),
                      "capacity_label": CAPACITY_LABELS.get(ver.capacity_status, ver.capacity_status)})
    items.sort(key=lambda i: i["resource"].pk)  # dataset order (import order), stable across runs
    return items


def _filters(request):
    index = _region_index()
    region_code = (request.GET.get("region") or "").strip()
    category = (request.GET.get("category") or "").strip()
    region = index.get(region_code) if region_code else None
    unknown_region = bool(region_code) and region is None
    unknown_category = bool(category) and category not in Resource.CATEGORIES
    return index, region_code, region, unknown_region, category, unknown_category


def resource_list(request):
    as_of = _as_of(request)
    index, region_code, region, unknown_region, category, unknown_category = _filters(request)
    items = [] if (unknown_region or unknown_category) else _listed_items(as_of, region, category or None)
    return render(request, "catalog/list.html", {
        "items": items, "as_of": as_of,
        "regions": sorted(index.values(), key=lambda r: (len(r.ancestors_and_self()), r.code)),
        "categories": [(c, CATEGORY_LABELS[c]) for c in Resource.CATEGORIES],
        "selected_region": region_code, "selected_region_obj": region, "selected_category": category,
        "unknown_region": unknown_region, "unknown_category": unknown_category,
        "category_label": CATEGORY_LABELS.get(category, category),
    })


def resource_detail(request, resource_key):
    as_of = _as_of(request)
    res = Resource.objects.filter(resource_key=resource_key).prefetch_related("versions__sources").first()
    ver = res.current_version if res else None
    if ver is None:
        raise Http404
    vis = catalog_visibility(ver, as_of)
    if vis.detail == "NONE":
        raise Http404
    index = _region_index()
    win = ver.application_window or {}
    return render(request, "catalog/detail.html", {
        "resource": res, "version": ver, "vis": vis, "as_of": as_of,
        "is_history": vis.detail == "HISTORY",
        "region_names": [index[c].name if c in index else c for c in ver.regions],
        "category_labels": [CATEGORY_LABELS.get(c, c) for c in res.categories],
        "level_label": LEVEL_LABELS.get(res.level, res.level),
        "capacity_label": CAPACITY_LABELS.get(ver.capacity_status, ver.capacity_status),
        "channels": [CHANNEL_LABELS.get(c, c) for c in (ver.how_to_apply or {}).get("channels", [])],
        "proxy_label": PROXY_LABELS.get((ver.how_to_apply or {}).get("proxy_allowed", "UNKNOWN"), "需確認"),
        "window_type": win.get("type"), "window_ranges": win.get("ranges", []), "window_months": win.get("months"),
        "sources": ver.sources.all(),
        "excludes": [e.get("resource_key") for e in (ver.stacking_rules or {}).get("excludes", [])],
        "other_versions": ver.resource.versions.exclude(pk=ver.pk).order_by("-id"),
    })


def api_public_resources(request):
    as_of = _as_of(request)
    index, region_code, region, unknown_region, category, unknown_category = _filters(request)
    items = [] if (unknown_region or unknown_category) else _listed_items(as_of, region, category or None)
    return JsonResponse({
        "is_synthetic": True, "as_of": as_of.isoformat(),
        "notice": "目錄展示不等於正式推薦；初篩不等於主管機關核定。全部為合成資料。",
        "count": len(items),
        "results": [{
            "resource_key": i["resource"].resource_key, "canonical_name": i["resource"].canonical_name,
            "level": i["resource"].level, "categories": i["resource"].categories,
            "version_label": i["version"].version_label, "status": i["version"].status,
            "status_label": i["vis"].status_label, "badges": i["vis"].badges, "notes": i["vis"].notes,
            "regions": i["version"].regions,
            "effective_from": i["version"].effective_from.isoformat() if i["version"].effective_from else None,
            "effective_to": i["version"].effective_to.isoformat() if i["version"].effective_to else None,
            "effective_unknown": i["version"].effective_unknown,
            "capacity_status": i["version"].capacity_status,
            "sources": [{"id": s.source_id, "url_or_ref": s.url_or_ref, "retrieved_at": s.retrieved_at.isoformat()} for s in i["version"].sources.all()],
            "last_source_retrieved_at": i["version"].last_source_retrieved_at.isoformat() if i["version"].last_source_retrieved_at else None,
            "is_synthetic": True,
        } for i in items],
    }, json_dumps_params={"ensure_ascii": False})


def page_not_found(request, exception=None):
    return render(request, "catalog/404.html", status=404)


def server_error(request):
    # No database access, no exception details: safe even when the DB is down.
    return render(request, "catalog/500.html", status=500)
