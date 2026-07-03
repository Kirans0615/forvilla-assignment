# Forvilla Vendor Data Standards

Every uploaded file must satisfy the rules below. `scripts/01_clean.py` enforces them;
`scripts/02_validate.py` verifies them.

## Files

| File | Contents |
|---|---|
| `data/clean/events.csv` | One row per event (10 events) |
| `data/clean/vendors_EVT-0XX.csv` | One row per vendor **at that event** |
| `data/clean/all_vendors_master.csv` | Union of all event vendor rows |

Encoding UTF-8, comma-separated, header row required, no blank rows.

## Event fields

| Field | Format | Example |
|---|---|---|
| `event_id` | `EVT-` + 3 digits | `EVT-001` |
| `event_name` | Title Case | `Summer Makers Market` |
| `event_date` | ISO `YYYY-MM-DD` | `2026-07-11` |
| `start_time` / `end_time` | `H:MM AM/PM` | `10:00 AM` |
| `venue`, `city` | Title Case | `Georgetown Waterfront Park` |
| `state` | 2-letter USPS | `DC` |

## Vendor fields

| Field | Format | Example |
|---|---|---|
| `vendor_id` | `FV-` + 3 digits, stable across events | `FV-007` |
| `vendor_name` | Title Case (small words lowercased, `&`/`+` kept) | `Willow & Wick Candle Co.` |
| `category` | One value from the taxonomy below | `Candles & Home Fragrance` |
| `products` | Sentence-case, comma-separated list | `Soy candles, wax melts, room sprays` |
| `email` | lowercase, valid `x@y.z`; blank if unknown | `hello@willowwick.com` |
| `phone` | `(XXX) XXX-XXXX`; blank if unknown | `(202) 555-0143` |
| `instagram` | `@handle` (lowercase, no URL); blank if unknown | `@willowwickcandles` |
| `booth` | Letter + number, no prefix words | `A1` |

Missing `email`/`phone`/`instagram` are allowed but are **flagged for follow-up** in the
data quality report. All other fields are required.

## Category taxonomy (controlled vocabulary)

`Jewelry` · `Pottery & Ceramics` · `Candles & Home Fragrance` · `Bath & Body` ·
`Textiles & Fiber Arts` · `Woodworking` · `Art & Prints` · `Stationery & Paper Goods` ·
`Baked Goods` · `Food & Pantry` · `Glass Art` · `Leather Goods` · `Plants & Florals` ·
`Home Goods`

Free-text categories in raw files are mapped via the alias table in `scripts/01_clean.py`
(e.g. `candles`, `home fragrance` → `Candles & Home Fragrance`). Unmappable categories fail
the run loudly rather than passing through silently.

## Integrity rules

1. No duplicate `(event_id, vendor_id)` pairs — duplicates in raw files are dropped and logged.
2. Same vendor ⇒ same `vendor_id`, name, and contact info in every file (IDs assigned from the
   deduped master list).
3. Every vendor row's `event_id` must exist in `events.csv`.
4. Every event has ≥ 5 vendors.
