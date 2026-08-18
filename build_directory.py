"""
build_directory.py
-------------------
Turns raw scraped data (SoundCloud track search, Fiverr gig search, Google
Places / Maps crawler -- all in the shape produced by common Apify actors)
into a single curated directory.json for the HipHopLord site.

FOLDER LAYOUT EXPECTED (same names Apify/your scrapes already used):
    Producers/            -> raw SoundCloud track-search JSON files
    Sound Engineers/       -> raw Fiverr gig-search JSON files
    Visuals & Design/      -> raw Fiverr gig-search JSON files
    studios_usa/           -> raw Google Places crawler JSON files

Each folder may contain any number of .json files, each holding a JSON
array of raw items straight out of the scraper -- nothing needs to be
cleaned by hand first.

WHY THIS VERSION IS DIFFERENT FROM A SIMPLE "COPY EVERYTHING OVER" SCRIPT
  - SoundCloud search results are individual TRACKS, not producer profiles,
    and a lot of them are not actually beats for sale (label reissue
    accounts, an artist's own released songs, duplicate uploads). This
    script groups tracks by uploader and only keeps uploaders whose
    catalog actually looks like beat/instrumental content, then shows
    one representative track per producer instead of a spammy track list.
  - Fiverr search results mix in loosely related gigs (a "cinematic game
    music" gig showing up under a hip hop search, for example). This
    script filters by genre tag + title keywords before anything is
    published.
  - Google Places results include a few non-studio categories (record
    stores, business centers) that slipped into the "recording studio"
    search. Those are dropped.
  - Every category is deduplicated (by seller ID, place ID, or track URL)
    so re-running the same search twice doesn't create repeat cards.

Run it with:
    python build_directory.py
It writes directory.json next to this script.
"""

import json
import os
import re
import urllib.parse
from collections import defaultdict

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

FIVERR_AFFILIATE_ID = "45990"  # replace with your real Fiverr affiliate/bta ID

FOLDERS = {
    "producers": ["Producers"],
    "engineers": ["Sound Engineers"],
    "visuals": ["Visuals & Design", "(Visuals & Design"],  # tolerate the stray "(" typo
    "studios": ["studios_usa"],
}

HIP_HOP_GENRES = {"hip_hop", "rap", "trap", "drill", "lofi"}
GENRE_PRIORITY = ["trap", "drill", "rap", "hip_hop", "r_b", "lofi", "edm", "pop", "rock"]
ENGINEER_KEYWORDS = re.compile(r"\bmix|\bmaster|\btune|\bvocal", re.I)
BEAT_SIGNAL = re.compile(
    r"type beat|instrumental|prod\.?\s*by|beatmaker|free beat|beat ?tape|riddim|"
    r"boom ?bap|\bbeat\b",
    re.I,
)
MAX_REASONABLE_FIVERR_PRICE = 400  # filters out obvious outlier/mispriced gigs

# SoundCloud uploaders that pass the automated BEAT_SIGNAL check (title/tag/
# description keywords, or a "beatmaker"-style username) but turned out on
# manual review to NOT actually be producers selling beats -- false positives
# the regex can't catch on its own. Reviewed by hand against their full track
# list before exclusion; reasons kept here for future re-review:
#   - "Emad Saad Hip Hop": rapper/emcee releasing his own vocal songs
#     ("Heavyweight Lyricist", features, verses) -- matched only because
#     "boom bap" is used as his genre/style tag, not because he sells beats.
#   - "Dgunzbeatz": mixing & mastering engineer ("M&M BY DGUNZ" credited on
#     other artists' finished vocal songs) -- matched via a couple of
#     "instrumental"-tagged tracks and one "prod by" credit, but the bulk of
#     the catalog is mix/master work, not original instrumentals for sale.
#   - "Lance O Smith": every track carries the same copy-pasted "Instrumental
#     hiphop..." boilerplate description (a SoundCloud discovery/SEO tactic),
#     but the actual titles ("Bad Bunny", "My Boo", "Track 1"..."Track 9")
#     read as a DJ/remix repost account, not original productions.
#   - "MagroTheHipHopArtist": rapper/emcee (rap-battle cypher entries,
#     features, a Mac Miller tribute); one track's title credits a *different*
#     person as producer ("Produced by @Dangertheproducer"), which is what
#     tripped the filter.
EXCLUDED_PRODUCER_USERNAMES = {
    "Emad Saad Hip Hop",
    "Dgunzbeatz",
    "Lance O Smith",
    "MagroTheHipHopArtist",
}

# Minimal ISO 3166-1 alpha-2 -> country name map, covering the codes that show
# up in Fiverr/SoundCloud data. Falls back to the raw code for anything else.
COUNTRY_NAMES = {
    "US": "United States", "GB": "United Kingdom", "CA": "Canada", "AU": "Australia",
    "DE": "Germany", "FR": "France", "IT": "Italy", "ES": "Spain", "PT": "Portugal",
    "NL": "Netherlands", "BE": "Belgium", "PL": "Poland", "RO": "Romania",
    "BG": "Bulgaria", "GR": "Greece", "RS": "Serbia", "SI": "Slovenia",
    "CZ": "Czechia", "LT": "Lithuania", "EE": "Estonia", "UA": "Ukraine",
    "LK": "Sri Lanka", "PK": "Pakistan", "IN": "India", "BD": "Bangladesh",
    "PH": "Philippines", "ID": "Indonesia", "TH": "Thailand", "NG": "Nigeria",
    "KE": "Kenya", "ZA": "South Africa", "MA": "Morocco", "ET": "Ethiopia",
    "AR": "Argentina", "BR": "Brazil", "CL": "Chile", "BO": "Bolivia",
    "PE": "Peru", "CO": "Colombia", "MX": "Mexico", "DO": "Dominican Republic",
    "AZ": "Azerbaijan", "TJ": "Tajikistan",
}


def country_name(code):
    if not code:
        return ""
    return COUNTRY_NAMES.get(code.strip().upper(), code)


def parse_soundcloud_tags(tag_list):
    """SoundCloud tag_list mixes quoted multi-word tags with bare single
    words, e.g.  '"Mobb Deep" "Hip Hop" Remix Rap'. A plain .split() breaks
    the quoted phrases apart -- this keeps them intact."""
    if not tag_list:
        return []
    tokens = re.findall(r'"([^"]+)"|(\S+)', tag_list)
    tags = [a or b for a, b in tokens]
    return [t.strip().lower() for t in tags if t.strip()]


def sorted_by_genre_priority(genres):
    genres = list(genres)
    genres.sort(key=lambda g: GENRE_PRIORITY.index(g) if g in GENRE_PRIORITY else 99)
    return [g.replace("_", " ") for g in genres]


# ---------------------------------------------------------------------------
# GENERIC HELPERS
# ---------------------------------------------------------------------------

def load_json_files(folder_names, base_dir):
    items = []
    for name in folder_names:
        path = os.path.join(base_dir, name)
        if not os.path.isdir(path):
            continue
        for filename in sorted(os.listdir(path)):
            if not filename.endswith(".json"):
                continue
            try:
                with open(os.path.join(path, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as error:
                print(f"  (skipped {filename}: {error})")
                continue
            if isinstance(data, list):
                items.extend(data)
    return items


def make_fiverr_affiliate_link(raw_url):
    """Build a Fiverr affiliate deep link to a specific gig page.

    IMPORTANT: Fiverr's go.fiverr.com/visit/ redirector only honors the
    param name "landingPage" (camelCase), NOT "landing_page" (snake_case) --
    and it expects the target URL to be percent-encoded TWICE. Confirmed by
    comparing against a real link generated from the Fiverr affiliate
    dashboard's own "LP URL" tool:

        ...&landingPage=https%253A%252F%252Fwww.fiverr.com%252F<user>%252F<gig>

    Using "landing_page" (single-encoded, as this function did before) is
    silently ignored by Fiverr and falls back to the generic homepage --
    that was the root cause of every Engineers/Visuals card resolving to
    the same non-specific Fiverr URL.
    """
    if not raw_url or "fiverr.com" not in raw_url:
        return raw_url or ""
    clean_url = raw_url.split("?")[0]
    encoded_once = urllib.parse.quote(clean_url, safe="")
    encoded_twice = urllib.parse.quote(encoded_once, safe="")
    return (
        "https://go.fiverr.com/visit/"
        f"?bta={FIVERR_AFFILIATE_ID}&brand=fiverrmarketplace&landingPage={encoded_twice}"
    )


def make_soundcloud_embed(track_url):
    if not track_url:
        return ""
    encoded = urllib.parse.quote(track_url, safe="")
    return (
        "https://w.soundcloud.com/player/?url=" + encoded +
        "&color=%23e2a83f&auto_play=false&hide_related=true&show_comments=false"
        "&show_user=true&show_reposts=false&visual=false"
    )


def title_case_words(value):
    return value.strip() if value else ""


def clean_producer_name(username):
    """SoundCloud usernames are often 'Name | extra tagline' or
    'Name (extra description)' -- keep just the clean name for display."""
    if not username:
        return "Unknown Artist"
    name = re.split(r"\s*[|(]", username)[0].strip()
    return name or username.strip()


# ---------------------------------------------------------------------------
# PRODUCERS  (SoundCloud track search -> one card per producer)
# ---------------------------------------------------------------------------

def build_producers(base_dir):
    raw_tracks = load_json_files(FOLDERS["producers"], base_dir)
    by_user = defaultdict(list)
    for track in raw_tracks:
        user = track.get("user") or {}
        username = user.get("username") or "Unknown"
        by_user[username].append(track)

    entries = []
    for username, tracks in by_user.items():
        if username in EXCLUDED_PRODUCER_USERNAMES:
            continue

        def has_signal(t):
            haystack = " ".join([
                t.get("title") or "", t.get("tag_list") or "", t.get("description") or "",
            ])
            return bool(BEAT_SIGNAL.search(haystack))

        signal_tracks = [t for t in tracks if has_signal(t)]
        signal_ratio = len(signal_tracks) / len(tracks) if tracks else 0
        username_signals = bool(BEAT_SIGNAL.search(username))

        # Keep this uploader only if their catalog reads like actual beat/
        # instrumental content -- either most of their tracks show beat
        # signals, or the account name itself makes it obvious (e.g. a
        # username containing "Beatmaker" or "Type Beat").
        if signal_ratio < 0.3 and not username_signals:
            continue

        pool = signal_tracks or tracks
        best = max(pool, key=lambda t: t.get("likes_count") or 0)

        genre = best.get("genre") or "Hip Hop"
        clean_name = clean_producer_name(username)
        tags = parse_soundcloud_tags(best.get("tag_list"))[:4] or [genre.lower()]

        user = best.get("user") or {}
        location = ", ".join(filter(None, [user.get("city"), country_name(user.get("country_code"))]))

        entries.append({
            "id": f"prod-{len(entries) + 1:03d}",
            "category": "producers",
            "categoryLabel": "Producers & Beatmakers",
            "title": title_case_words(best.get("title")) or "Hip Hop Instrumental",
            "provider_name": clean_name,
            "location": location,
            "price": "Contact for licensing",
            "description": (best.get("description") or "").strip()[:220] or
                            f"Original {genre.lower()} production from {clean_name}, sampled from their SoundCloud catalog.",
            "tags": tags,
            "link": best.get("permalink_url", ""),
            "linkLabel": "Listen on SoundCloud",
            "embed_url": make_soundcloud_embed(best.get("permalink_url", "")),
            "image": best.get("artwork_url") or "",
            "likes": best.get("likes_count") or 0,
            "featured": (best.get("likes_count") or 0) > 50,
            "sample": False,
        })

    return entries


# ---------------------------------------------------------------------------
# ENGINEERS + VISUALS  (Fiverr gig search)
# ---------------------------------------------------------------------------

def build_fiverr_category(base_dir, folder_key, category, label, id_prefix,
                           require_hip_hop_genre, require_engineer_keywords,
                           genre_field="genre"):
    raw_gigs = load_json_files(FOLDERS[folder_key], base_dir)
    by_seller = {}

    for gig in raw_gigs:
        title = (gig.get("title") or "").strip()
        if not title:
            continue

        price = gig.get("priceFrom")
        if price is not None and price > MAX_REASONABLE_FIVERR_PRICE:
            continue

        genres = set((gig.get("attributes") or {}).get(genre_field) or [])
        if require_hip_hop_genre and not (genres & HIP_HOP_GENRES):
            continue
        if require_engineer_keywords and not ENGINEER_KEYWORDS.search(title):
            continue

        seller_id = gig.get("sellerId") or gig.get("sellerName")
        score = (gig.get("rating") or 0) * (gig.get("reviewsCount") or 0)

        # Keep only the best-scoring gig per seller, so one popular seller
        # with many gigs doesn't crowd out everyone else.
        existing = by_seller.get(seller_id)
        if existing is None or score > existing["_score"]:
            gig["_score"] = score
            by_seller[seller_id] = gig

    ranked = sorted(by_seller.values(), key=lambda g: g["_score"], reverse=True)

    entries = []
    for gig in ranked:
        attributes = gig.get("attributes") or {}
        genres = set(attributes.get(genre_field) or [])
        design_styles = attributes.get("design_style") or []

        # Cover art gigs are more usefully tagged by visual style than by
        # musical genre (every gig in this file targets hip hop already).
        if design_styles:
            tags = [s.replace("_", " ") for s in design_styles][:3]
        else:
            tags = sorted_by_genre_priority(genres & HIP_HOP_GENRES or genres)[:4]
        tags = tags or ["hip hop"]

        price = gig.get("priceFrom")
        rating = gig.get("rating")
        reviews = gig.get("reviewsCount") or 0
        seller_level = {
            "top_rated_seller": "Fiverr Top Rated Seller",
            "level_two_seller": "Fiverr Level 2 Seller",
            "level_one_seller": "Fiverr Level 1 Seller",
        }.get(gig.get("sellerLevel"), "Fiverr Seller")

        description = seller_level
        if reviews:
            description += f" · {reviews} reviews"
        if rating:
            description += f" · {rating}★"

        entries.append({
            "id": f"{id_prefix}-{len(entries) + 1:03d}",
            "category": category,
            "categoryLabel": label,
            "title": title_case_words(gig.get("title")),
            "provider_name": gig.get("sellerDisplayName") or gig.get("sellerName") or "",
            "location": country_name(gig.get("sellerCountry")),
            "price": f"From ${price:g}" if price is not None else "",
            "description": description,
            "tags": tags,
            "link": make_fiverr_affiliate_link(gig.get("gigUrl", "")),
            "linkLabel": "View Gig on Fiverr",
            "image": (gig.get("images") or [None])[0] or gig.get("sellerImage") or "",
            "rating": rating,
            "reviewsCount": reviews,
            "featured": (rating or 0) >= 4.9 and reviews >= 500,
            "sample": False,
        })

    return entries


# ---------------------------------------------------------------------------
# STUDIOS  (Google Places crawler)
# ---------------------------------------------------------------------------

def build_studios(base_dir):
    raw_places = load_json_files(FOLDERS["studios"], base_dir)
    seen_place_ids = set()
    kept = []

    for place in raw_places:
        if place.get("permanentlyClosed") or place.get("temporarilyClosed"):
            continue
        if place.get("categoryName") != "Recording studio":
            continue

        place_id = place.get("placeId") or place.get("title")
        if place_id in seen_place_ids:
            continue
        seen_place_ids.add(place_id)
        kept.append(place)

    kept.sort(key=lambda p: (p.get("city") or "", -(p.get("totalScore") or 0)))

    entries = []
    for place in kept:
        rating = place.get("totalScore")
        reviews = place.get("reviewsCount") or 0
        city = place.get("city") or ""
        state = place.get("state") or ""

        entries.append({
            "id": f"std-{len(entries) + 1:03d}",
            "category": "studios",
            "categoryLabel": "Recording Studios & Spaces",
            "title": title_case_words(place.get("title")),
            "provider_name": "",
            "location": ", ".join(filter(None, [city, state])),
            "address": place.get("address") or "",
            "phone": place.get("phone") or "",
            "price": "Contact for rates",
            "description": (place.get("description") or "").strip() or
                            f"Recording studio in {city or 'the US'}" + (f", rated {rating}★ from {reviews} reviews." if rating else "."),
            "tags": [t.lower() for t in (place.get("categories") or [])][:4] or ["recording studio"],
            "link": place.get("website") or f"https://www.google.com/maps/place/?q=place_id:{place.get('placeId','')}",
            "linkLabel": "Visit Website" if place.get("website") else "View on Google Maps",
            "image": place.get("imageUrl") or "",
            "rating": rating,
            "reviewsCount": reviews,
            "featured": (rating or 0) >= 4.8 and reviews >= 100,
            "sample": False,
        })

    return entries


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    print("Building producers...")
    producers = build_producers(base_dir)
    print(f"  -> {len(producers)} curated producer profiles")

    print("Building sound engineers...")
    engineers = build_fiverr_category(
        base_dir, "engineers", "engineers", "Mixing & Mastering Engineers", "eng",
        require_hip_hop_genre=True, require_engineer_keywords=True,
    )
    print(f"  -> {len(engineers)} curated engineer listings")

    print("Building visual / cover art designers...")
    visuals = build_fiverr_category(
        base_dir, "visuals", "visuals", "Cover Art & Visual Designers", "vis",
        require_hip_hop_genre=False, require_engineer_keywords=False,
        genre_field="musical_genre",
    )
    print(f"  -> {len(visuals)} curated designer listings")

    print("Building recording studios...")
    studios = build_studios(base_dir)
    print(f"  -> {len(studios)} curated studio listings")

    master_data = producers + engineers + visuals + studios

    output_path = os.path.join(base_dir, "directory.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(master_data, f, ensure_ascii=False, indent=2)

    print()
    print(f"Done. Wrote {len(master_data)} total listings to {output_path}")


if __name__ == "__main__":
    main()
