#!/usr/bin/env python3
"""Capture 360px screenshots, horizontal-scroll and keyboard evidence from the running loopback server.

Usage: python scripts/capture_evidence.py [base_url] [out_dir]
Requires playwright (requirements-test.txt). Uses STP_CHROMIUM if set (path to a chrome binary),
otherwise playwright's default browser.
"""
import json
import os
import sys
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "evidence")
AS_OF = os.environ.get("STP_AS_OF", "2026-10-13")
PAGES = [
    ("01_list", f"/?as_of={AS_OF}"),
    ("02_list_filter_demo_a", f"/?region=DEMO-A&as_of={AS_OF}"),
    ("03_list_empty_state", f"/?region=DEMO-B&category=EDUCATION&as_of={AS_OF}"),
    ("04_detail_food_unknown_period", f"/resources/TW-DEMO-FOOD-005/?as_of={AS_OF}"),
    ("05_detail_rent_expired_history", f"/resources/TW-DEMO-RENT-006/?as_of={AS_OF}"),
    ("06_not_found", "/resources/TW-DEMO-NOPE-999/"),
    ("07_unknown_region", "/?region=NOWHERE"),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    report = {"captured_at": datetime.now(timezone.utc).isoformat(), "base_url": BASE, "viewport": {"width": 360, "height": 740},
              "synthetic_only": True, "pages": []}
    with sync_playwright() as p:
        kwargs = {}
        if os.environ.get("STP_CHROMIUM"):
            kwargs["executable_path"] = os.environ["STP_CHROMIUM"]
        browser = p.chromium.launch(**kwargs)
        report["browser"] = browser.version
        ctx = browser.new_context(viewport={"width": 360, "height": 740}, device_scale_factor=2, is_mobile=True, has_touch=True)
        page = ctx.new_page()
        for name, path in PAGES:
            resp = page.goto(BASE + path, wait_until="load")
            page.screenshot(path=os.path.join(OUT, f"{name}_360.png"), full_page=True)
            metrics = page.evaluate("() => ({scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth, bodyScrollWidth: document.body.scrollWidth})")
            entry = {"name": name, "path": path, "status": resp.status if resp else None,
                     "content_length_bytes": len(resp.body()) if resp else None, "title": page.title(),
                     "scrollWidth": metrics["scrollWidth"], "innerWidth": metrics["innerWidth"],
                     "no_horizontal_scroll": metrics["scrollWidth"] <= metrics["innerWidth"] and metrics["bodyScrollWidth"] <= metrics["innerWidth"]}
            if name == "01_list":
                # keyboard walk: Tab through the page and record focus order
                focus = []
                for _ in range(12):
                    page.keyboard.press("Tab")
                    focus.append(page.evaluate("() => {const e=document.activeElement; return (e.tagName||'')+(e.id?'#'+e.id:'')+' '+(e.textContent||e.value||'').trim().slice(0,30)}"))
                entry["tab_focus_order"] = focus
                # keyboard-only filter: focus region select, choose DEMO-B via keyboard, submit with Enter
                page.focus("#region")
                page.select_option("#region", "DEMO-B")
                page.focus("button[type=submit]")
                with page.expect_navigation():
                    page.keyboard.press("Enter")
                entry["keyboard_filter_result_url"] = page.url
                entry["keyboard_filter_result_text"] = page.locator("p.meta[role=status]").first.inner_text()
                page.screenshot(path=os.path.join(OUT, "01b_list_keyboard_filtered_demo_b_360.png"), full_page=True)
                # keyboard open first detail link
                page.goto(BASE + path, wait_until="load")
                page.focus("ul.cards a")
                with page.expect_navigation():
                    page.keyboard.press("Enter")
                entry["keyboard_open_detail_url"] = page.url
            report["pages"].append(entry)
        browser.close()
    with open(os.path.join(OUT, "ui_evidence.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    bad = [e["name"] for e in report["pages"] if not e["no_horizontal_scroll"]]
    print("pages:", len(report["pages"]), "horizontal_scroll_failures:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
