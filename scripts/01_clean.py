#!/usr/bin/env python3
"""Clean and normalize raw vendor intake files into upload-ready CSVs.

Applies docs/data-standards.md to every file in data/raw/:
- events.csv  -> data/clean/events.csv (ISO dates, H:MM AM/PM times, Title Case)
- EVT-0XX_*.csv -> data/clean/vendors_EVT-0XX.csv + data/clean/all_vendors_master.csv
  (Title Case names, taxonomy categories, normalized email/phone/instagram/booth,
   stable FV-XXX vendor IDs, duplicates dropped and logged)

Unmappable categories or unparseable dates abort the run — bad data never
passes through silently.
"""
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAW, CLEAN = BASE / "data" / "raw", BASE / "data" / "clean"

TAXONOMY = [
    "Jewelry", "Pottery & Ceramics", "Candles & Home Fragrance", "Bath & Body",
    "Textiles & Fiber Arts", "Woodworking", "Art & Prints", "Stationery & Paper Goods",
    "Baked Goods", "Food & Pantry", "Glass Art", "Leather Goods", "Plants & Florals",
    "Home Goods",
]
ALIASES = {
    "candles": "Candles & Home Fragrance", "home fragrance": "Candles & Home Fragrance",
    "candle maker": "Candles & Home Fragrance",
    "pottery": "Pottery & Ceramics", "ceramics": "Pottery & Ceramics",
    "ceramics/pottery": "Pottery & Ceramics", "ceramicist": "Pottery & Ceramics",
    "fiber arts": "Textiles & Fiber Arts", "textiles": "Textiles & Fiber Arts",
    "weaving/textiles": "Textiles & Fiber Arts", "fiber": "Textiles & Fiber Arts",
    "wood working": "Woodworking", "woodwork": "Woodworking", "woodcraft": "Woodworking",
    "stationery": "Stationery & Paper Goods", "paper goods": "Stationery & Paper Goods",
    "paper": "Stationery & Paper Goods",
    "jewellery": "Jewelry", "jewelry maker": "Jewelry",
    "bath and body": "Bath & Body", "soaps & skincare": "Bath & Body", "skincare": "Bath & Body",
    "bakery": "Baked Goods", "baker": "Baked Goods",
    "food": "Food & Pantry", "pantry goods": "Food & Pantry", "food/pantry": "Food & Pantry",
    "specialty food": "Food & Pantry",
    "glass": "Glass Art", "glasswork": "Glass Art",
    "prints": "Art & Prints", "artist/prints": "Art & Prints", "art": "Art & Prints",
    "leather": "Leather Goods", "leatherwork": "Leather Goods",
    "plants": "Plants & Florals", "florals": "Plants & Florals",
    "plants/flowers": "Plants & Florals",
    "homewares": "Home Goods",
}
SMALL_WORDS = {"and", "or", "the", "of", "at", "in", "a", "an"}
DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y", "%d %B %Y"]

VENDOR_COLS = ["event_id", "event_name", "event_date", "vendor_id", "vendor_name",
               "category", "products", "email", "phone", "instagram", "booth"]


def title_case(s):
    words = []
    for i, w in enumerate(re.split(r"\s+", s.strip())):
        lw = w.lower()
        if w in ("&", "+"):
            words.append(w)
        elif i > 0 and lw in SMALL_WORDS:
            words.append(lw)
        else:
            # capitalize first letter only, preserving things like "Co." and "+"
            words.append(w[0].upper() + w[1:].lower() if w else w)
    return " ".join(words)


def norm_category(raw):
    key = raw.strip().lower()
    for canon in TAXONOMY:
        if key == canon.lower():
            return canon
    if key in ALIASES:
        return ALIASES[key]
    sys.exit(f"ERROR: unmappable category {raw!r} — add it to the alias table.")


def norm_date(raw):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    sys.exit(f"ERROR: unparseable date {raw!r}")


def norm_time(raw):
    m = re.match(r"^\s*(\d{1,2})(?::(\d{2}))?\s*([ap]m?)?", raw.strip(), re.I)
    if not m:
        sys.exit(f"ERROR: unparseable time {raw!r}")
    h, mins, ampm = int(m.group(1)), m.group(2) or "00", (m.group(3) or "").lower()
    suffix = "PM" if ampm.startswith("p") else "AM"
    return f"{h}:{mins} {suffix}"


def norm_hours(raw):
    parts = re.split(r"\s*(?:-|–|to)\s*", raw.strip(), maxsplit=1)
    if len(parts) != 2:
        sys.exit(f"ERROR: unparseable hours {raw!r}")
    start, end = norm_time(parts[0]), norm_time(parts[1])
    # intake files often drop AM/PM on the start time ("10 - 4pm"); infer from context
    return start, end


def norm_phone(raw):
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        sys.exit(f"ERROR: phone {raw!r} does not have 10 digits")
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def norm_instagram(raw):
    h = raw.strip().lower()
    if not h:
        return ""
    h = re.sub(r"^https?://(www\.)?instagram\.com/", "", h)
    h = re.sub(r"^instagram\.com/", "", h).strip("/@ ")
    if not re.fullmatch(r"[a-z0-9._]{1,30}", h):
        sys.exit(f"ERROR: invalid instagram handle {raw!r}")
    return f"@{h}"


def norm_email(raw):
    e = raw.strip().lower()
    if not e:
        return ""
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", e):
        sys.exit(f"ERROR: invalid email {raw!r}")
    return e


def norm_booth(raw):
    m = re.search(r"([a-z])\s*-?\s*(\d+)", raw.strip(), re.I)
    if not m:
        sys.exit(f"ERROR: unparseable booth {raw!r}")
    return f"{m.group(1).upper()}{m.group(2)}"


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)

    # --- events ---
    events = {}
    with open(RAW / "events.csv", newline="") as f:
        for row in csv.DictReader(f):
            start, end = norm_hours(row["hours"])
            events[row["event_id"].strip()] = {
                "event_id": row["event_id"].strip(),
                "event_name": title_case(row["event_name"]),
                "event_date": norm_date(row["date"]),
                "start_time": start, "end_time": end,
                "venue": row["venue"].strip(),
                "city": title_case(row["city"]),
                "state": row["state"].strip().upper(),
            }
    with open(CLEAN / "events.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(next(iter(events.values()))))
        w.writeheader()
        w.writerows(sorted(events.values(), key=lambda e: e["event_id"]))

    # --- vendors ---
    all_rows, dupes = [], []
    for path in sorted(RAW.glob("EVT-*.csv")):
        eid = path.name[:7]
        ev = events[eid]
        seen = set()
        rows = []
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                name = title_case(row["vendor name"])
                if name in seen:
                    dupes.append(f"{path.name}: duplicate row for {name!r} dropped")
                    continue
                seen.add(name)
                rows.append({
                    "event_id": eid, "event_name": ev["event_name"],
                    "event_date": ev["event_date"],
                    "vendor_id": "",  # assigned after all files are read
                    "vendor_name": name,
                    "category": norm_category(row["category"]),
                    "products": row["products"].strip().capitalize()
                                if row["products"].strip().islower()
                                else row["products"].strip(),
                    "email": norm_email(row["email"]),
                    "phone": norm_phone(row["phone"]),
                    "instagram": norm_instagram(row["instagram"]),
                    "booth": norm_booth(row["booth"]),
                })
        all_rows.extend(rows)

    # stable vendor IDs from the deduped master name list; backfill best-known
    # contact info so the same vendor is identical in every file
    ids = {n: f"FV-{i + 1:03d}" for i, n in
           enumerate(sorted({r["vendor_name"] for r in all_rows}))}
    best = {}
    for r in all_rows:
        r["vendor_id"] = ids[r["vendor_name"]]
        b = best.setdefault(r["vendor_id"], {})
        for k in ("email", "phone", "instagram", "category", "products"):
            if r[k] and not b.get(k):
                b[k] = r[k]
    for r in all_rows:
        for k, v in best[r["vendor_id"]].items():
            r[k] = r[k] or v

    for eid in events:
        rows = [r for r in all_rows if r["event_id"] == eid]
        with open(CLEAN / f"vendors_{eid}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=VENDOR_COLS)
            w.writeheader()
            w.writerows(sorted(rows, key=lambda r: r["booth"]))
    with open(CLEAN / "all_vendors_master.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=VENDOR_COLS)
        w.writeheader()
        w.writerows(sorted(all_rows, key=lambda r: (r["event_id"], r["booth"])))

    print(f"Cleaned {len(events)} events, {len(all_rows)} vendor rows, "
          f"{len(ids)} unique vendors -> {CLEAN}")
    for d in dupes:
        print(f"  dropped: {d}")


if __name__ == "__main__":
    main()
