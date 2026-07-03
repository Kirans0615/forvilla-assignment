# Data Quality Report — Forvilla Vendor Uploads

*Generated 2026-07-03 17:34*

## Result: ✅ PASS

- Events validated: **10**
- Vendor rows validated: **80**
- Unique vendors: **35**
- Errors: **0** · Warnings: **2**

## Checks performed
- Field formats (IDs, ISO dates, times, phone, email, Instagram, booth, state)
- Categories restricted to the 14-value taxonomy
- No duplicate vendor per event; no double-booked booths
- Same vendor ID ⇒ identical name/category/contacts at every event
- Every vendor row references a real event; per-event files match the master
- 10 events present, each with ≥ 5 vendors; no past-dated events

## Errors
- None 🎉

## Warnings (follow-up list)
- all_vendors_master.csv:20: Lark & Loom Weaving missing instagram — follow up with vendor
- all_vendors_master.csv:59: Lark & Loom Weaving missing instagram — follow up with vendor

## Vendors per event

| Event | Vendors |
|---|---|
| EVT-001 | 8 |
| EVT-002 | 8 |
| EVT-003 | 8 |
| EVT-004 | 8 |
| EVT-005 | 8 |
| EVT-006 | 8 |
| EVT-007 | 8 |
| EVT-008 | 8 |
| EVT-009 | 8 |
| EVT-010 | 8 |
