#!/usr/bin/env python3
"""Generate simulated raw intake files for 10 Forvilla market events.

Real vendor lists arrive from market organizers in inconsistent shapes. This script
reproduces that mess deterministically (mixed date/phone/Instagram formats, free-text
categories, stray whitespace, duplicate rows, missing contacts) so the cleaning and
validation steps can be demonstrated end to end. Replace data/raw/ with real files
when they're available — the rest of the pipeline is unchanged.
"""
import csv
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

# (event_id, name, iso_date, start, end, venue, city, state)
EVENTS = [
    ("EVT-001", "Summer Makers Market", "2026-07-11", "10:00 AM", "4:00 PM",
     "Georgetown Waterfront Park", "Washington", "DC"),
    ("EVT-002", "Handmade at the Harbor", "2026-07-18", "11:00 AM", "6:00 PM",
     "National Harbor Plaza", "Oxon Hill", "MD"),
    ("EVT-003", "Village Craft Fair", "2026-07-26", "10:00 AM", "5:00 PM",
     "Old Town Market Square", "Alexandria", "VA"),
    ("EVT-004", "Moonlight Artisan Night Market", "2026-08-07", "5:00 PM", "10:00 PM",
     "The Wharf, District Pier", "Washington", "DC"),
    ("EVT-005", "Riverside Makers Bazaar", "2026-08-15", "10:00 AM", "4:00 PM",
     "Yards Park", "Washington", "DC"),
    ("EVT-006", "Late Summer Craft Collective", "2026-08-23", "11:00 AM", "5:00 PM",
     "Silver Spring Civic Plaza", "Silver Spring", "MD"),
    ("EVT-007", "Harvest Handmade Market", "2026-09-05", "10:00 AM", "6:00 PM",
     "Reston Town Center Pavilion", "Reston", "VA"),
    ("EVT-008", "Makers in the Park", "2026-09-13", "12:00 PM", "5:00 PM",
     "Meridian Hill Park", "Washington", "DC"),
    ("EVT-009", "Autumn Artisan Fair", "2026-09-19", "10:00 AM", "5:00 PM",
     "Bethesda Row Plaza", "Bethesda", "MD"),
    ("EVT-010", "Fall Village Market", "2026-09-27", "10:00 AM", "4:00 PM",
     "Eastern Market Plaza", "Washington", "DC"),
]

# name: (clean_category, products, ig_handle, email, phone10)
VENDORS = {
    "Willow & Wick Candle Co.": ("Candles & Home Fragrance", "Soy candles, wax melts, room sprays",
                                 "willowwickcandles", "hello@willowwick.com", "2025550143"),
    "Terra Luna Ceramics": ("Pottery & Ceramics", "Hand-thrown mugs, planters, serving bowls",
                            "terralunaceramics", "studio@terraluna.com", "2025550171"),
    "The Gilded Thread": ("Textiles & Fiber Arts", "Hand-embroidered linens, tea towels",
                          "thegildedthread", "orders@gildedthread.com", "3015550122"),
    "Hazel + Pine Woodworks": ("Woodworking", "Cutting boards, serving trays, coasters",
                               "hazelpinewood", "shop@hazelpine.com", "7035550188"),
    "Marigold Paper Studio": ("Stationery & Paper Goods", "Letterpress cards, notebooks, gift wrap",
                              "marigoldpaper", "hi@marigoldpaper.com", "2025550109"),
    "Copper Fox Jewelry": ("Jewelry", "Hammered copper earrings, brass cuffs",
                           "copperfoxjewelry", "hello@copperfox.shop", "5715550137"),
    "Bloom & Bramble Botanicals": ("Bath & Body", "Herbal soaps, bath soaks, balms",
                                   "bloomandbramble", "care@bloombramble.com", "3015550165"),
    "Sweet Alchemy Bakes": ("Baked Goods", "French macarons, shortbread, brownies",
                            "sweetalchemybakes", "orders@sweetalchemy.com", "2025550152"),
    "Stone & Sage Pottery": ("Pottery & Ceramics", "Stoneware dinnerware, vases",
                             "stoneandsagepottery", "kiln@stonesage.com", "7035550119"),
    "Lark & Loom Weaving": ("Textiles & Fiber Arts", "Woven wall hangings, table runners",
                            "larkandloom", "weave@larkloom.com", "2025550196"),
    "Ember Glassworks": ("Glass Art", "Blown-glass ornaments, stained glass suncatchers",
                         "emberglassworks", "studio@emberglass.com", "3015550174"),
    "Prairie Honey Co.": ("Food & Pantry", "Raw wildflower honey, honeycomb, beeswax",
                          "prairiehoneyco", "buzz@prairiehoney.com", "5405550131"),
    "Cedar & Salt Soap Co.": ("Bath & Body", "Cold-process soaps, shower steamers",
                              "cedarandsalt", "hello@cedarsalt.com", "7035550142"),
    "Inkwell Prints": ("Art & Prints", "Linocut prints, screen-printed posters",
                       "inkwellprintsdc", "press@inkwellprints.com", "2025550118"),
    "Juniper Hill Farm": ("Food & Pantry", "Small-batch jams, pickles, hot sauces",
                          "juniperhillfarm", "farm@juniperhill.com", "5405550126"),
    "The Velvet Cactus": ("Plants & Florals", "Succulent arrangements, hand-painted pots",
                          "thevelvetcactus", "grow@velvetcactus.com", "3015550183"),
    "Golden Hour Macrame": ("Textiles & Fiber Arts", "Macrame plant hangers, wall art",
                            "goldenhourmacrame", "knots@goldenhour.art", "2025550161"),
    "Tin Roof Leather": ("Leather Goods", "Hand-stitched wallets, belts, key fobs",
                         "tinroofleather", "shop@tinroofleather.com", "7035550157"),
    "Wildflower Press": ("Art & Prints", "Pressed-flower frames, botanical prints",
                         "wildflowerpressart", "bloom@wildflowerpress.art", "3015550149"),
    "Moon Phase Metals": ("Jewelry", "Sterling silver rings, moon-phase pendants",
                          "moonphasemetals", "luna@moonphasemetals.com", "2025550134"),
    "Birch Bark Baskets": ("Home Goods", "Woven baskets, storage trays",
                           "birchbarkbaskets", "weave@birchbark.com", "5405550178"),
    "Saffron Sky Spices": ("Food & Pantry", "Hand-blended spice mixes, infused salts",
                           "saffronskyspices", "blend@saffronsky.com", "2025550187"),
    "Little Fox Knits": ("Textiles & Fiber Arts", "Chunky knit beanies, baby blankets",
                         "littlefoxknits", "yarn@littlefoxknits.com", "3015550113"),
    "Clay & Co. Studio": ("Pottery & Ceramics", "Speckled mugs, ring dishes, planters",
                          "clayandcostudio", "hello@clayandco.studio", "7035550164"),
    "The Paper Lantern": ("Stationery & Paper Goods", "Origami mobiles, paper garlands, cards",
                          "thepaperlanterndc", "fold@paperlantern.com", "2025550128"),
    "Rosemary Row Soaps": ("Bath & Body", "Garden-herb soaps, lotion bars",
                           "rosemaryrowsoaps", "suds@rosemaryrow.com", "5715550146"),
    "Harbor Light Candles": ("Candles & Home Fragrance", "Coastal soy candles, reed diffusers",
                             "harborlightcandles", "glow@harborlight.co", "3015550192"),
    "Fern & Feather Illustration": ("Art & Prints", "Watercolor wildlife prints, greeting cards",
                                    "fernandfeatherart", "art@fernfeather.com", "2025550175"),
    "Oakheart Cutting Boards": ("Woodworking", "End-grain cutting boards, cheese boards",
                                "oakheartboards", "wood@oakheart.shop", "5405550153"),
    "Silver Thistle Studio": ("Jewelry", "Botanical-cast silver earrings, necklaces",
                              "silverthistlestudio", "cast@silverthistle.com", "7035550129"),
    "Cocoa & Crumb": ("Baked Goods", "Artisan cookies, hand-dipped chocolates",
                      "cocoaandcrumb", "treats@cocoacrumb.com", "2025550166"),
    "Painted Sky Pottery": ("Pottery & Ceramics", "Glazed landscape mugs, wall tiles",
                            "paintedskypottery", "glaze@paintedsky.art", "3015550138"),
    "Thread & Thistle Embroidery": ("Textiles & Fiber Arts", "Embroidery hoop art, patches",
                                    "threadandthistle", "stitch@threadthistle.com", "5715550172"),
    "Amber Grove Apothecary": ("Bath & Body", "Botanical facial oils, herbal salves",
                               "ambergroveapothecary", "herbs@ambergrove.com", "2025550193"),
    "Pinecone & Petal Wreaths": ("Plants & Florals", "Dried-flower wreaths, seasonal swags",
                                 "pineconeandpetal", "wreaths@pineconepetal.com", "7035550181"),
}

NAMES = list(VENDORS)
# 8 vendors per event, overlapping so vendor calendars span multiple markets
ASSIGNMENTS = {
    "EVT-001": [0, 1, 3, 5, 7, 11, 13, 19],
    "EVT-002": [26, 10, 4, 6, 8, 12, 30, 34],
    "EVT-003": [2, 5, 9, 14, 16, 21, 23, 28],
    "EVT-004": [0, 13, 17, 20, 24, 27, 29, 31],
    "EVT-005": [1, 6, 10, 15, 18, 22, 25, 33],
    "EVT-006": [3, 7, 11, 16, 19, 26, 30, 32],
    "EVT-007": [2, 8, 12, 14, 21, 24, 28, 34],
    "EVT-008": [4, 9, 15, 17, 23, 27, 31, 5],
    "EVT-009": [0, 6, 13, 18, 20, 25, 29, 33],
    "EVT-010": [1, 10, 22, 26, 32, 34, 12, 16],
}

DATE_STYLES = ["%B %d, %Y", "%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y", "%b %d, %Y"]
PHONE_STYLES = [
    lambda d: d,
    lambda d: f"{d[:3]}-{d[3:6]}-{d[6:]}",
    lambda d: f"({d[:3]}) {d[3:6]} {d[6:]}",
    lambda d: f"{d[:3]}.{d[3:6]}.{d[6:]}",
]
IG_STYLES = [
    lambda h: f"@{h}",
    lambda h: h,
    lambda h: f"https://www.instagram.com/{h}/",
    lambda h: f"instagram.com/{h}",
    lambda h: f"@{h.upper()}",
]
CATEGORY_ALIASES = {
    "Candles & Home Fragrance": ["candles", "CANDLES", "home fragrance", "candle maker"],
    "Pottery & Ceramics": ["pottery", "Ceramics", "CERAMICS/POTTERY", "ceramicist"],
    "Textiles & Fiber Arts": ["fiber arts", "Textiles", "weaving/textiles", "FIBER"],
    "Woodworking": ["wood working", "Woodwork", "WOODCRAFT"],
    "Stationery & Paper Goods": ["stationery", "paper goods", "Paper"],
    "Jewelry": ["jewellery", "JEWELRY", "jewelry maker"],
    "Bath & Body": ["bath and body", "soaps & skincare", "SKINCARE"],
    "Baked Goods": ["bakery", "baked goods", "BAKER"],
    "Food & Pantry": ["food", "pantry goods", "FOOD/PANTRY", "specialty food"],
    "Glass Art": ["glass", "glasswork"],
    "Art & Prints": ["prints", "artist/prints", "ART"],
    "Leather Goods": ["leather", "leatherwork"],
    "Plants & Florals": ["plants", "florals", "PLANTS/FLOWERS"],
    "Home Goods": ["home goods", "homewares"],
}
NAME_STYLES = [str, str.upper, str.lower, str.title, lambda s: f"  {s} "]


def mess_date(iso, i):
    from datetime import date
    y, m, d = map(int, iso.split("-"))
    return date(y, m, d).strftime(DATE_STYLES[i % len(DATE_STYLES)])


def mess_time(t, i):
    if i % 3 == 0:
        return t
    h, rest = t.split(":")
    ampm = rest.split()[1].lower()
    if i % 3 == 1:
        return f"{h}{ampm}"          # "10am"
    return f"{h}:{rest.split()[0].split(':')[0] if ':' in rest else '00'} {ampm.upper()}"


def main():
    RAW.mkdir(parents=True, exist_ok=True)

    # events.csv — inconsistent dates, times, header casing left alone but values messy
    with open(RAW / "events.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "event_name", "date", "hours", "venue", "city", "state"])
        for i, (eid, name, iso, start, end, venue, city, state) in enumerate(EVENTS):
            hours = f"{mess_time(start, i)} - {mess_time(end, i + 1)}" if i % 2 else f"{start} to {end}"
            w.writerow([eid, name if i % 3 else name.upper(), mess_date(iso, i),
                        hours, venue, city.upper() if i % 4 == 0 else city, state])

    row_n = 0
    for eid, name, iso, *_ in EVENTS:
        slug = name.lower().replace(" ", "-").replace(",", "")
        rows = []
        for booth_i, vi in enumerate(ASSIGNMENTS[eid]):
            vname = NAMES[vi]
            cat, products, ig, email, phone = VENDORS[vname]
            aliases = CATEGORY_ALIASES[cat]
            booth = f"{chr(65 + booth_i // 4)}{booth_i % 4 + 1}"
            row = [
                NAME_STYLES[row_n % len(NAME_STYLES)](vname),
                aliases[row_n % len(aliases)],
                products if row_n % 2 else products.lower(),
                email.upper() if row_n % 5 == 0 else f" {email}" if row_n % 7 == 0 else email,
                "" if row_n % 11 == 3 else PHONE_STYLES[row_n % len(PHONE_STYLES)](phone),
                "" if row_n % 13 == 5 else IG_STYLES[row_n % len(IG_STYLES)](ig),
                booth if row_n % 3 else f"Booth {booth.lower()}",
            ]
            rows.append(row)
            row_n += 1
        # inject duplicate rows in two files to test dedupe
        if eid in ("EVT-002", "EVT-007"):
            rows.append(list(rows[2]))
        with open(RAW / f"{eid}_{slug}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["vendor name", "category", "products", "email", "phone",
                        "instagram", "booth"])
            w.writerows(rows)

    print(f"Wrote events.csv + {len(EVENTS)} raw vendor files to {RAW}")


if __name__ == "__main__":
    main()
