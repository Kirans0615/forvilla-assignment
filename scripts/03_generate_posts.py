#!/usr/bin/env python3
"""Convert cleaned vendor data into social media posts in Forvilla's voice.

For each of the 10 events, generates from data/clean/:
- instagram_announcement.md  (7 days before the event)
- vendor_spotlight.md        (3 days before)
- facebook_event_post.md     (1 day before)
plus social/content_calendar.csv scheduling all 30 posts.

Voice reference (docs/research-brief.md): warm, community-first, "villagers" /
"the village", celebrates the maker's story, invitational.
"""
import csv
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CLEAN, SOCIAL = BASE / "data" / "clean", BASE / "social"

CATEGORY_EMOJI = {
    "Jewelry": "💍", "Pottery & Ceramics": "🏺", "Candles & Home Fragrance": "🕯️",
    "Bath & Body": "🧼", "Textiles & Fiber Arts": "🧶", "Woodworking": "🪵",
    "Art & Prints": "🎨", "Stationery & Paper Goods": "✉️", "Baked Goods": "🧁",
    "Food & Pantry": "🍯", "Glass Art": "🫙", "Leather Goods": "👜",
    "Plants & Florals": "🌿", "Home Goods": "🧺",
}
BASE_TAGS = "#Forvilla #ForTheVillage #ShopSmall #HandmadeMarket #SupportLocalArtisans"


def pretty_date(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return d.strftime("%A, %B %-d")


def city_tag(city):
    return "#" + city.replace(" ", "")


def instagram_announcement(ev, vendors):
    lineup = "\n".join(
        f"{CATEGORY_EMOJI[v['category']]} {v['vendor_name']}"
        + (f" ({v['instagram']})" if v["instagram"] else "")
        + f" — {v['category']}"
        for v in vendors)
    return f"""# Instagram — Event Announcement · {ev['event_id']}

**Post 7 days before event ({schedule_date(ev, 7)})**

---

🏘️ Villagers, mark your calendars!

**{ev['event_name']}** is coming to {ev['venue']} on {pretty_date(ev['event_date'])},
{ev['start_time']}–{ev['end_time']} · {ev['city']}, {ev['state']} 📍

Meet {len(vendors)} incredible local makers:

{lineup}

Open the Forvilla app to browse every booth on the live event map, peek at each
artisan's signature pieces, and plan your visit. Come out for the village! 💛

{BASE_TAGS} #MadeIn{ev['state']} {city_tag(ev['city'])} {"#" + ev['event_name'].replace(" ", "")}
"""


def vendor_spotlight(ev, vendors):
    # rotate the spotlight so different vendors get featured across the season
    v = vendors[int(ev["event_id"][-3:]) % len(vendors)]
    products = [p.strip() for p in v["products"].split(",")]
    handle = f" {v['instagram']}" if v["instagram"] else ""
    return f"""# Instagram — Vendor Spotlight · {ev['event_id']}

**Post 3 days before event ({schedule_date(ev, 3)})**

---

✨ VENDOR SPOTLIGHT ✨

Say hello to **{v['vendor_name']}**{handle} — the hands behind
{products[0].lower()}, {products[1].lower()}, and more {CATEGORY_EMOJI[v['category']]}

You'll find them at booth **{v['booth']}** at {ev['event_name']} this
{pretty_date(ev['event_date']).split(',')[0]} at {ev['venue']}.

Tap their hub in the Forvilla app to read their story, see what's new for this
market, and leave them a thank-you note after you visit. Every purchase keeps a
local maker making 💛

{BASE_TAGS} #{v['category'].replace(' & ', 'And').replace(' ', '')} {city_tag(ev['city'])}
"""


def facebook_post(ev, vendors):
    by_cat = defaultdict(list)
    for v in vendors:
        by_cat[v["category"]].append(v["vendor_name"])
    cats = "\n".join(
        f"• {CATEGORY_EMOJI[c]} {c}: {', '.join(names)}"
        for c, names in sorted(by_cat.items()))
    return f"""# Facebook — Event Post · {ev['event_id']}

**Post 1 day before event ({schedule_date(ev, 1)})**

---

Tomorrow, the village comes together! 🏘️

Join us for **{ev['event_name']}** at {ev['venue']}, {ev['city']}, {ev['state']}
🗓️ {pretty_date(ev['event_date'])} · {ev['start_time']}–{ev['end_time']}

Here's who's setting up their booths:

{cats}

Every item at this market is made by hand by a local artisan — and every artisan
has a story. Download the Forvilla app to explore the live event map, find your
favorite vendors' booths, and play the market stamp game while you shop.

Free to attend. Bring a friend, meet your makers, and come out for the village! 💛

{BASE_TAGS.replace('#', '#')}
"""


def schedule_date(ev, days_before):
    d = datetime.strptime(ev["event_date"], "%Y-%m-%d") - timedelta(days=days_before)
    return d.strftime("%Y-%m-%d")


def main():
    with open(CLEAN / "events.csv", newline="") as f:
        events = {e["event_id"]: e for e in csv.DictReader(f)}
    with open(CLEAN / "all_vendors_master.csv", newline="") as f:
        vendors = defaultdict(list)
        for r in csv.DictReader(f):
            vendors[r["event_id"]].append(r)

    calendar = []
    for eid, ev in sorted(events.items()):
        out = SOCIAL / eid
        out.mkdir(parents=True, exist_ok=True)
        posts = [
            ("instagram_announcement.md", "Instagram", 7, instagram_announcement),
            ("vendor_spotlight.md", "Instagram", 3, vendor_spotlight),
            ("facebook_event_post.md", "Facebook", 1, facebook_post),
        ]
        for fname, platform, days, fn in posts:
            (out / fname).write_text(fn(ev, vendors[eid]))
            calendar.append({
                "post_date": schedule_date(ev, days),
                "platform": platform,
                "post_type": fname.replace(".md", "").replace("_", " "),
                "event_id": eid,
                "event_name": ev["event_name"],
                "event_date": ev["event_date"],
                "file": f"social/{eid}/{fname}",
            })

    calendar.sort(key=lambda r: r["post_date"])
    with open(SOCIAL / "content_calendar.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(calendar[0]))
        w.writeheader()
        w.writerows(calendar)

    print(f"Wrote {len(calendar)} posts for {len(events)} events -> {SOCIAL}")


if __name__ == "__main__":
    main()
