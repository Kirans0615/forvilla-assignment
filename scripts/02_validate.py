#!/usr/bin/env python3
"""Validate the cleaned files against docs/data-standards.md.

Independent re-check of 01_clean.py's output: field formats, category taxonomy,
duplicate detection, referential integrity, vendor-ID consistency, and completeness.
Writes reports/data_quality_report.md and exits non-zero on any error so this can
gate an upload in CI.
"""
import csv
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CLEAN, REPORTS = BASE / "data" / "clean", BASE / "reports"

TAXONOMY = {
    "Jewelry", "Pottery & Ceramics", "Candles & Home Fragrance", "Bath & Body",
    "Textiles & Fiber Arts", "Woodworking", "Art & Prints", "Stationery & Paper Goods",
    "Baked Goods", "Food & Pantry", "Glass Art", "Leather Goods", "Plants & Florals",
    "Home Goods",
}
PATTERNS = {
    "event_id": r"EVT-\d{3}",
    "vendor_id": r"FV-\d{3}",
    "event_date": r"\d{4}-\d{2}-\d{2}",
    "phone": r"\(\d{3}\) \d{3}-\d{4}",
    "instagram": r"@[a-z0-9._]{1,30}",
    "email": r"[^@\s]+@[^@\s]+\.[a-z]{2,}",
    "booth": r"[A-Z]\d+",
    "start_time": r"\d{1,2}:\d{2} [AP]M",
    "end_time": r"\d{1,2}:\d{2} [AP]M",
    "state": r"[A-Z]{2}",
}
OPTIONAL = {"email", "phone", "instagram"}

errors, warnings = [], []


def check(row, field, where):
    val = row.get(field, "")
    if not val:
        if field in OPTIONAL:
            warnings.append(f"{where}: {row.get('vendor_name', row.get('event_id'))} "
                            f"missing {field} — follow up with vendor")
        else:
            errors.append(f"{where}: missing required field {field}")
        return
    if field in PATTERNS and not re.fullmatch(PATTERNS[field], val):
        errors.append(f"{where}: {field}={val!r} does not match required format")


def main():
    REPORTS.mkdir(exist_ok=True)

    with open(CLEAN / "events.csv", newline="") as f:
        events = list(csv.DictReader(f))
    if len(events) != 10:
        errors.append(f"events.csv: expected 10 events, found {len(events)}")
    event_ids = set()
    for i, e in enumerate(events, 2):
        where = f"events.csv:{i}"
        for field in e:
            check(e, field, where)
        try:
            if datetime.strptime(e["event_date"], "%Y-%m-%d").date() < datetime(2026, 7, 3).date():
                warnings.append(f"{where}: {e['event_id']} date {e['event_date']} is in the past")
        except ValueError:
            pass  # format error already recorded
        event_ids.add(e["event_id"])

    with open(CLEAN / "all_vendors_master.csv", newline="") as f:
        master = list(csv.DictReader(f))

    per_event = defaultdict(list)
    vendor_identity = defaultdict(set)
    for i, r in enumerate(master, 2):
        where = f"all_vendors_master.csv:{i}"
        for field in r:
            if field not in ("event_name", "products", "vendor_name", "category"):
                check(r, field, where)
        if r["category"] not in TAXONOMY:
            errors.append(f"{where}: category {r['category']!r} not in taxonomy")
        if r["event_id"] not in event_ids:
            errors.append(f"{where}: event_id {r['event_id']} not in events.csv")
        per_event[r["event_id"]].append(r)
        vendor_identity[r["vendor_id"]].add(
            (r["vendor_name"], r["category"], r["email"], r["phone"], r["instagram"]))

    for vid, identities in vendor_identity.items():
        if len(identities) > 1:
            errors.append(f"vendor {vid} has inconsistent identity across events: {identities}")

    pair_counts = Counter((r["event_id"], r["vendor_id"]) for r in master)
    for pair, n in pair_counts.items():
        if n > 1:
            errors.append(f"duplicate vendor {pair[1]} at event {pair[0]} ({n} rows)")

    for eid in event_ids:
        rows = per_event.get(eid, [])
        if len(rows) < 5:
            errors.append(f"{eid}: only {len(rows)} vendors (minimum 5)")
        booth_counts = Counter(r["booth"] for r in rows)
        for booth, n in booth_counts.items():
            if n > 1:
                errors.append(f"{eid}: booth {booth} assigned to {n} vendors")
        per_file = CLEAN / f"vendors_{eid}.csv"
        if not per_file.exists():
            errors.append(f"missing per-event file {per_file.name}")
        else:
            with open(per_file, newline="") as f:
                if list(csv.DictReader(f)) != sorted(rows, key=lambda r: r["booth"]):
                    errors.append(f"{per_file.name} does not match master rows for {eid}")

    status = "❌ FAIL" if errors else "✅ PASS"
    lines = [
        "# Data Quality Report — Forvilla Vendor Uploads",
        f"\n*Generated {datetime.now():%Y-%m-%d %H:%M}*",
        f"\n## Result: {status}",
        f"\n- Events validated: **{len(events)}**",
        f"- Vendor rows validated: **{len(master)}**",
        f"- Unique vendors: **{len(vendor_identity)}**",
        f"- Errors: **{len(errors)}** · Warnings: **{len(warnings)}**",
        "\n## Checks performed",
        "- Field formats (IDs, ISO dates, times, phone, email, Instagram, booth, state)",
        "- Categories restricted to the 14-value taxonomy",
        "- No duplicate vendor per event; no double-booked booths",
        "- Same vendor ID ⇒ identical name/category/contacts at every event",
        "- Every vendor row references a real event; per-event files match the master",
        "- 10 events present, each with ≥ 5 vendors; no past-dated events",
        "\n## Errors",
    ]
    lines += [f"- {e}" for e in errors] or ["- None 🎉"]
    lines += ["\n## Warnings (follow-up list)"]
    lines += [f"- {w}" for w in warnings] or ["- None"]
    lines += ["\n## Vendors per event\n", "| Event | Vendors |", "|---|---|"]
    lines += [f"| {eid} | {len(per_event[eid])} |" for eid in sorted(event_ids)]

    report = REPORTS / "data_quality_report.md"
    report.write_text("\n".join(lines) + "\n")
    print(f"{status} — {len(errors)} errors, {len(warnings)} warnings -> {report}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
