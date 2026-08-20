#!/usr/bin/env python3
"""
Generates one static, fully server-rendered HTML page per directory.json
listing (439 pages) under /listings/<id>.html.

Why: the main index.html renders all cards client-side via a fetch() of
directory.json, which is fine for the browsing UX but means search engines
that don't execute JavaScript (or that execute it slowly/inconsistently)
never see the actual listing content, and there is no unique, indexable URL
per listing to rank for its own long-tail queries ("mix engineer for hip
hop atlanta", a specific producer's name, etc.). This script fixes that:
each listing gets its own plain-HTML page with the full description,
curator note, stats, badges, and a real <title>/meta description/canonical/
JSON-LD -- all still built from directory.json, no manual duplication of
data.

Usage:
    python3 generate_listing_pages.py

Re-run this any time directory.json changes (after build_directory.py).
It fully regenerates the listings/ folder and sitemap.xml.
"""
import html as html_lib
import json
import os
import re

BASE_URL = "https://hiphoplord.com"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LISTINGS_DIR = os.path.join(BASE_DIR, "listings")

# Short, consistent role keyword for each category. Used to make sure every
# single listing page's <title> and meta description explicitly names what
# the page is about ("hip hop producer", "mixing & mastering engineer"...)
# instead of relying only on raw source data (a messy SoundCloud track name,
# a lowercase Fiverr gig blurb, or a bare studio name) which often never
# mentions "hip hop" or the role at all. Keeps keyword usage identical and
# predictable across all 439 pages -- the exact kind of consistency search
# engines and AI crawlers look for when deciding what a page is "about".
CATEGORY_KEYWORDS = {
    "producers": "Hip Hop Producer",
    "engineers": "Mixing & Mastering Engineer",
    "visuals": "Cover Art Designer",
    "studios": "Recording Studio",
}


def esc(value):
    if value is None:
        return ""
    return html_lib.escape(str(value), quote=True)


def load_shared_style():
    """Pull the <style>...</style> block straight out of index.html so the
    listing pages always stay visually in sync with the main site without
    hand-duplicating CSS."""
    with open(os.path.join(BASE_DIR, "index.html"), encoding="utf-8") as f:
        page = f.read()
    m = re.search(r"<style>(.*?)</style>", page, re.S)
    return m.group(1)


NAV_HTML = """
<nav class="sticky top-0 z-50 backdrop-blur-md bg-black/60 border-b border-white/10">
  <div class="max-w-6xl mx-auto px-5 py-4 flex items-center justify-between">
    <a href="../index.html" class="display text-lg tracking-tight" aria-label="HipHopLord">HIPHOP<span class="gold-text">L</span><svg class="logo-o gold-text" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="9.3" fill="none" stroke="currentColor" stroke-width="2.6"/><circle cx="12" cy="12" r="3" fill="currentColor"/></svg><span class="gold-text">RD</span></a>
    <div class="hidden md:flex items-center gap-7 text-sm text-zinc-300">
      <a href="../index.html#directory" class="hover:text-white transition">Directory</a>
      <a href="../index.html#cities" class="hover:text-white transition">Cities</a>
      <a href="../about.html" class="hover:text-white transition">About</a>
      <a href="../contact.html" class="hover:text-white transition">Contact</a>
    </div>
    <a href="../index.html#submit" class="mono text-xs px-4 py-2 rounded-full border border-[--gold] gold-text hover:bg-[--gold] hover:text-black transition">+ List Your Service</a>
  </div>
</nav>
"""

FOOTER_HTML = """
<footer class="border-t border-white/10 py-10 px-5">
  <div class="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
    <p class="text-xs text-zinc-500">&copy; 2026 HipHopLord Directory. All rights reserved.</p>
    <div class="flex flex-wrap gap-5 text-xs text-zinc-500">
      <a href="../guides/" class="hover:text-zinc-300 transition">Guides</a>
      <a href="../about.html" class="hover:text-zinc-300 transition">About</a>
      <a href="../contact.html" class="hover:text-zinc-300 transition">Contact</a>
      <a href="../privacy-policy.html" class="hover:text-zinc-300 transition">Privacy Policy</a>
      <a href="../terms.html" class="hover:text-zinc-300 transition">Terms of Service</a>
      <a href="../affiliate-disclosure.html" class="hover:text-zinc-300 transition">Affiliate Disclosure</a>
    </div>
  </div>
</footer>
"""


def initial_avatar_html(item, size_classes="w-20 h-20"):
    initial = (item.get("provider_name") or item.get("title") or "?").strip()[:1].upper() or "?"
    if item.get("image"):
        alt = f"{item.get('title','')}{' — ' + item['provider_name'] if item.get('provider_name') else ''} | {item.get('categoryLabel','HipHopLord')}"
        return (f'<img src="{esc(item["image"])}" alt="{esc(alt)}" width="80" height="80" loading="lazy"'
                f' class="{size_classes} rounded-2xl object-cover border border-white/10 flex-shrink-0"'
                f' onerror="this.replaceWith(Object.assign(document.createElement(\'div\'),'
                f'{{className:\'{size_classes} rounded-2xl bg-gradient-to-br from-purple-900 to-zinc-800 border border-white/10 flex items-center justify-center flex-shrink-0\','
                f'innerHTML:\'<span class=&quot;mono text-2xl gold-text font-bold&quot;>{esc(initial)}</span>\'}}))">')
    return (f'<div class="{size_classes} rounded-2xl bg-gradient-to-br from-purple-900 to-zinc-800 border border-white/10 '
            f'flex items-center justify-center flex-shrink-0">'
            f'<span class="mono text-2xl gold-text font-bold">{esc(initial)}</span></div>')


def rating_block(item):
    if not item.get("rating"):
        return ""
    reviews = f' <span class="text-zinc-500">({item["reviewsCount"]} reviews)</span>' if item.get("reviewsCount") else ""
    return f'<p class="mono text-sm text-amber-300/90 mt-3">★ {esc(item["rating"])}{reviews}</p>'


def likes_block(item):
    if not item.get("likes"):
        return ""
    return f'<p class="mono text-sm text-zinc-500 mt-1">♥ {esc(item["likes"])} likes on SoundCloud</p>'


def address_block(item):
    if not item.get("address"):
        return ""
    phone = f" &middot; {esc(item['phone'])}" if item.get("phone") else ""
    return f'<p class="text-zinc-400 text-sm mt-3 leading-relaxed">{esc(item["address"])}{phone}</p>'


def extra_stats_block(item):
    stats = item.get("extraStats") or []
    if not stats:
        return ""
    return (f'<p class="text-zinc-500 text-xs mt-3 leading-relaxed">'
            f'{" &middot; ".join(esc(s) for s in stats)}</p>')


def badges_block(item):
    badges = item.get("badges") or []
    if not badges:
        return ""
    pills = "".join(
        f'<span class="mono text-[11px] px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-300 '
        f'border border-emerald-500/20">{esc(b)}</span>'
        for b in badges
    )
    return f'<div class="flex flex-wrap gap-2 mt-3">{pills}</div>'


def embed_block(item):
    if not item.get("embed_url"):
        return ""
    return (f'<iframe class="w-full mt-5 rounded-xl" width="100%" height="120" loading="lazy" scrolling="no" '
            f'frameborder="no" src="{esc(item["embed_url"])}"></iframe>')


def curator_note_block(item):
    if not item.get("curatorNote"):
        return ""
    return (f'<div class="mt-5 pl-4 border-l-2 border-[--gold]/40 bg-white/[0.02] rounded-r-lg py-3 pr-4">'
            f'<span class="mono text-[10.5px] uppercase tracking-widest gold-text">Curator\'s Note</span>'
            f'<p class="text-zinc-300 text-sm mt-1.5 leading-relaxed italic">{esc(item["curatorNote"])}</p>'
            f'</div>')


def badge_widget_block(item):
    """Studios only: an optional, self-serve embeddable HTML badge a real
    studio owner can grab for their own website or social page if they ever
    find their listing. Deliberately framed as a free, no-strings-attached
    courtesy rather than tied to any paid upgrade or reciprocal deal --
    trading a backlink for something of value is explicitly called out in
    Google's Link Schemes guidance. Voluntary, unprompted embeds from real
    industry sites are a legitimate way to build backlinks; keeping the
    offer optional and non-transactional is what keeps it on the right side
    of that line."""
    if item.get("category") != "studios":
        return ""
    canonical = f"{BASE_URL}/listings/{item['id']}.html"
    title = item.get("title", "")
    alt_text = f"Featured on HipHopLord — {title}"
    snippet = (f'<a href="{canonical}" target="_blank" rel="noopener">'
               f'<img src="{BASE_URL}/badge.svg" alt="{esc(alt_text)}" width="180" height="48" '
               f'style="display:block;border:0;" /></a>')
    return (
        '<div class="card rounded-2xl p-7 md:p-9">'
        '<span class="mono text-[10.5px] uppercase tracking-widest text-zinc-500">Is This Your Studio?</span>'
        '<p class="text-zinc-400 text-sm mt-2 leading-relaxed">Feel free to grab this badge for your own '
        'website or social page — no cost, no obligation, just a way to show off your listing.</p>'
        '<div class="mt-3 bg-black/40 border border-white/10 rounded-xl p-4">'
        f'<img src="{BASE_URL}/badge.svg" alt="{esc(alt_text)}" width="180" height="48" '
        'style="display:block;margin-bottom:12px;" />'
        '<textarea readonly onclick="this.select()" class="w-full text-[11px] font-mono bg-black/60 '
        f'text-zinc-400 p-3 rounded-lg border border-white/10 resize-none" rows="3">{esc(snippet)}</textarea>'
        '</div></div>'
    )


def tags_block(item):
    tags = item.get("tags") or []
    if not tags:
        return ""
    pills = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags)
    return f'<div class="flex flex-wrap gap-2 mt-5">{pills}</div>'


def faq_block(item):
    faq = item.get("faq") or []
    if not faq:
        return ""
    rows = []
    for i, qa in enumerate(faq):
        rows.append(f"""
        <div class="border-b border-white/10 py-4 last:border-b-0">
          <h3 class="text-white text-sm font-semibold leading-snug">{esc(qa.get('question',''))}</h3>
          <p class="text-zinc-400 text-sm mt-2 leading-relaxed">{esc(qa.get('answer',''))}</p>
        </div>""")
    return f"""
    <section class="max-w-3xl mx-auto px-5 pb-6">
      <div class="card rounded-2xl p-7 md:p-9">
        <h2 class="display text-xl mb-2">Frequently Asked Questions</h2>
        <p class="text-zinc-500 text-xs mb-4">About {esc(item.get('title',''))}</p>
        <div>{''.join(rows)}</div>
      </div>
    </section>"""


def faq_json_ld(item):
    faq = item.get("faq") or []
    if not faq:
        return ""
    block = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": qa.get("question", ""),
                "acceptedAnswer": {"@type": "Answer", "text": qa.get("answer", "")},
            }
            for qa in faq
        ],
    }
    return f'<script type="application/ld+json">{json.dumps(block, ensure_ascii=False)}</script>'


def json_ld_for(item):
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": item.get("categoryLabel", ""),
             "item": f"{BASE_URL}/index.html#directory"},
            {"@type": "ListItem", "position": 3, "name": item.get("title", "")},
        ],
    }
    blocks = [breadcrumb]

    if item.get("category") == "studios":
        biz = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": item.get("title", ""),
            "url": item.get("link", ""),
        }
        if item.get("address"):
            biz["address"] = item["address"]
        if item.get("phone"):
            biz["telephone"] = item["phone"]
        if item.get("rating") and item.get("reviewsCount"):
            biz["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": item["rating"],
                "reviewCount": item["reviewsCount"],
            }
        blocks.append(biz)
    else:
        service = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": item.get("title", ""),
            "serviceType": item.get("categoryLabel", ""),
            "provider": {"@type": "Person", "name": item.get("provider_name") or item.get("title", "")},
            "url": item.get("link", ""),
        }
        if item.get("rating") and item.get("reviewsCount"):
            service["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": item["rating"],
                "reviewCount": item["reviewsCount"],
            }
        blocks.append(service)

    return "\n".join(
        f'<script type="application/ld+json">{json.dumps(b, ensure_ascii=False)}</script>' for b in blocks
    )


def related_listings_html(item, related):
    if not related:
        return ""
    cards = []
    for r in related:
        cards.append(f"""
        <a href="{esc(r['id'])}.html" class="card rounded-xl p-4 flex items-start gap-3 no-underline">
          {initial_avatar_html(r, size_classes="w-11 h-11")}
          <div class="min-w-0">
            <h3 class="text-white text-sm font-semibold leading-snug truncate">{esc(r.get('title',''))}</h3>
            <p class="text-zinc-500 text-xs mt-1 truncate">{esc(r.get('provider_name') or r.get('location') or '')}</p>
          </div>
        </a>""")
    return f"""
    <section class="max-w-3xl mx-auto px-5 pb-20">
      <div class="vinyl-divider mb-8"></div>
      <h2 class="display text-xl mb-5">More in {esc(item.get('categoryLabel',''))}</h2>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">{''.join(cards)}</div>
    </section>"""


def render_page(item, related, style_block):
    # A handful of raw SoundCloud track titles contain a literal "|" (e.g.
    # 'Rick Ross Type Beat - "Luxurious" [2024] | Rich Trap Type Beat'). Left
    # as-is that reads to search engines like several titles concatenated
    # together in one <title> tag. Swap it for an en dash so our own "|"
    # separators (role keyword, provider, brand) stay the only ones.
    title = (item.get("title", "") or "").replace("|", "–")
    provider = item.get("provider_name", "")
    category = item.get("category", "")
    category_label = item.get("categoryLabel", "")
    role_keyword = CATEGORY_KEYWORDS.get(category, "")
    location = item.get("location", "")

    # Title: lead with the role keyword so every page's <title> names what
    # it is about even when the raw title/provider text doesn't (messy
    # SoundCloud track names for producers, lowercase Fiverr gig blurbs for
    # engineers/visuals). Studios get their real city/state appended instead
    # of a role prefix, since "Recording Studio" is already implied by the
    # business name and the location is the stronger, more searched keyword
    # for that category (298 of 439 pages are studios).
    if category == "studios":
        page_title = f"{title} — {role_keyword} in {location} | HipHopLord" if location \
            else f"{title} — {role_keyword} | HipHopLord"
    elif provider:
        page_title = f"{role_keyword}: {title} — {provider} | HipHopLord"
    else:
        page_title = f"{role_keyword}: {title} | HipHopLord"

    description_src = item.get("curatorNote") or item.get("description") or page_title
    # Most auto-generated curator notes never say "hip hop" at all (they're
    # built purely from real stats), so on their own they under-signal what
    # the page is actually about. Prepend a short, honest keyword lead-in --
    # the underlying curator note text itself is untouched.
    # Studio curator notes already state the city/state themselves (e.g.
    # "...5 Google reviews in Denver, Colorado."), so skip repeating it here
    # to avoid an awkward duplicate location mention in the same sentence.
    kw_lead_in = f"{role_keyword} for hip hop artists" + (f" in {location}" if category != "studios" and location else "") + " — "
    meta_description = (kw_lead_in + description_src)[:300]
    canonical = f"{BASE_URL}/listings/{item['id']}.html"

    featured_badge = ('<span class="mono text-[11px] gold-text tracking-widest mb-2 block">★ FEATURED LISTING</span>'
                       if item.get("featured") else "")

    subtitle_parts = [p for p in [provider, item.get("location")] if p]
    subtitle = (f'<p class="text-zinc-400 text-sm mt-2">{esc(" · ".join(subtitle_parts))}</p>'
                if subtitle_parts else "")

    price_html = f'<span class="text-lg font-semibold text-zinc-100">{esc(item.get("price",""))}</span>' if item.get("price") else ""
    # Only engineers/visuals are actual paid Fiverr affiliate links -- Google's
    # own guidance is to mark those rel="sponsored". Producer (SoundCloud) and
    # studio (direct business site) links are not paid placements, so they
    # stay plain rel="noopener" like any other outbound link.
    is_affiliate = item.get("category") in ("engineers", "visuals")
    rel_attr = "noopener sponsored" if is_affiliate else "noopener"
    cta = (f'<a href="{esc(item.get("link",""))}" target="_blank" rel="{rel_attr}" '
           f'class="mono text-sm px-5 py-3 rounded-full bg-[--gold] text-black font-semibold '
           f'hover:bg-[--gold-soft] transition">{esc(item.get("linkLabel","View"))} →</a>')
    affiliate_note = ('<p class="text-[10px] text-zinc-600 mt-2 text-right w-full">Affiliate link — '
                       '<a href="../affiliate-disclosure.html" class="underline hover:text-zinc-400">disclosure</a></p>') if is_affiliate else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-31TNRD57MQ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-31TNRD57MQ');
</script>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{esc(page_title)}</title>
<meta name="description" content="{esc(meta_description)}" />
<link rel="canonical" href="{canonical}" />
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22><circle cx=%2212%22 cy=%2212%22 r=%2211%22 fill=%22%230a0a0b%22/><circle cx=%2212%22 cy=%2212%22 r=%229.3%22 fill=%22none%22 stroke=%22%23e2a83f%22 stroke-width=%222.6%22/><circle cx=%2212%22 cy=%2212%22 r=%223%22 fill=%22%23e2a83f%22/></svg>" />

<meta property="og:type" content="profile" />
<meta property="og:site_name" content="HipHopLord" />
<meta property="og:title" content="{esc(page_title)}" />
<meta property="og:description" content="{esc(meta_description)}" />
<meta property="og:url" content="{canonical}" />
{f'<meta property="og:image" content="{esc(item["image"])}" />' if item.get("image") else ''}
<meta name="twitter:card" content="summary" />
<meta name="twitter:title" content="{esc(page_title)}" />
<meta name="twitter:description" content="{esc(meta_description)}" />

{json_ld_for(item)}
{faq_json_ld(item)}

<script src="https://cdn.tailwindcss.com"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>{style_block}</style>
</head>
<body class="min-h-screen">
<div class="noise"></div>
{NAV_HTML}

<main class="max-w-3xl mx-auto px-5 pt-12 pb-6">
  <nav class="mono text-[11px] text-zinc-500 mb-8" aria-label="Breadcrumb">
    <a href="../index.html" class="hover:text-zinc-300 transition">Home</a>
    <span class="mx-1.5">/</span>
    <a href="../index.html#directory" class="hover:text-zinc-300 transition">{esc(category_label)}</a>
    <span class="mx-1.5">/</span>
    <span class="text-zinc-400">{esc(title)}</span>
  </nav>

  <div class="card rounded-2xl p-7 md:p-9 {'featured' if item.get('featured') else ''}">
    <div class="flex items-start gap-4">
      {initial_avatar_html(item)}
      <div class="min-w-0">
        <span class="mono text-[11px] uppercase tracking-widest text-zinc-500">{esc(category_label)}</span>
        {featured_badge}
        <h1 class="display text-2xl md:text-3xl leading-tight mt-1">{esc(title)}</h1>
        {subtitle}
      </div>
    </div>

    {rating_block(item)}
    {likes_block(item)}
    {address_block(item)}

    <p class="text-zinc-300 text-base mt-5 leading-relaxed">{esc(item.get("description",""))}</p>

    {curator_note_block(item)}
    {extra_stats_block(item)}
    {badges_block(item)}
    {embed_block(item)}
    {tags_block(item)}

    <div class="flex items-center justify-between mt-8 pt-6 border-t border-white/10 flex-wrap gap-4">
      {price_html}
      {cta}
      {affiliate_note}
    </div>
  </div>

  <p class="mt-6">
    <a href="../index.html#directory" class="mono text-xs text-zinc-500 hover:text-zinc-300 transition">&larr; Back to full directory</a>
  </p>
</main>

{faq_block(item)}

{related_listings_html(item, related)}

{f'<section class="max-w-3xl mx-auto px-5 pb-12">{badge_widget_block(item)}</section>' if item.get("category") == "studios" else ""}

{FOOTER_HTML}
</body>
</html>"""


def build_related_map(entries):
    """For each category, map id -> next 3 ids in that category's own order
    (cyclic), so every listing gets real internal links to other real
    listings in the same category -- deterministic, no randomness needed."""
    by_category = {}
    for e in entries:
        by_category.setdefault(e["category"], []).append(e)

    related_map = {}
    for cat, items in by_category.items():
        n = len(items)
        for i, item in enumerate(items):
            picks = [items[(i + 1 + k) % n] for k in range(min(3, n - 1))]
            related_map[item["id"]] = picks
    return related_map


def generate_sitemap(entries, guide_slugs=None):
    static_pages = [
        ("https://hiphoplord.com/", "weekly", "1.0"),
        ("https://hiphoplord.com/about.html", "monthly", "0.5"),
        ("https://hiphoplord.com/contact.html", "monthly", "0.4"),
        ("https://hiphoplord.com/privacy-policy.html", "yearly", "0.2"),
        ("https://hiphoplord.com/terms.html", "yearly", "0.2"),
        ("https://hiphoplord.com/affiliate-disclosure.html", "yearly", "0.2"),
    ]
    if guide_slugs:
        static_pages.append((f"{BASE_URL}/guides/", "monthly", "0.6"))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, freq, prio in static_pages:
        lines.append(f"  <url>\n    <loc>{loc}</loc>\n    <changefreq>{freq}</changefreq>\n    <priority>{prio}</priority>\n  </url>")
    for e in entries:
        prio = "0.7" if e.get("featured") else "0.5"
        lines.append(
            f"  <url>\n    <loc>{BASE_URL}/listings/{e['id']}.html</loc>\n"
            f"    <changefreq>monthly</changefreq>\n    <priority>{prio}</priority>\n  </url>"
        )
    for slug in (guide_slugs or []):
        lines.append(
            f"  <url>\n    <loc>{BASE_URL}/guides/{slug}.html</loc>\n"
            f"    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>"
        )
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main():
    with open(os.path.join(BASE_DIR, "directory.json"), encoding="utf-8") as f:
        entries = json.load(f)

    style_block = load_shared_style()
    related_map = build_related_map(entries)

    os.makedirs(LISTINGS_DIR, exist_ok=True)
    # Clear stale pages from previous runs (e.g. a removed listing id)
    # before writing the current set, so no dead/orphaned page lingers.
    for fname in os.listdir(LISTINGS_DIR):
        if fname.endswith(".html"):
            os.remove(os.path.join(LISTINGS_DIR, fname))

    for entry in entries:
        page_html = render_page(entry, related_map.get(entry["id"], []), style_block)
        out_path = os.path.join(LISTINGS_DIR, f"{entry['id']}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page_html)

    sitemap_xml = generate_sitemap(entries)
    with open(os.path.join(BASE_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

    print(f"Generated {len(entries)} listing pages in {LISTINGS_DIR}")
    print(f"Wrote sitemap.xml with {len(entries) + 5} URLs")


if __name__ == "__main__":
    main()
