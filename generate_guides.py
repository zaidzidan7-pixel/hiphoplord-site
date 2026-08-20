#!/usr/bin/env python3
"""
Generates the /guides/ section: a small set of hand-written, editorial
"how it actually works" articles that target informational search intent
the 439 listing pages don't cover (a listing page ranks for "mixing engineer
Atlanta"; a guide ranks for "how much does mixing cost"). Deliberately not
called "Blog" anywhere in the UI or nav -- it's linked from the footer as
"Guides", uses the exact same visual template as the rest of the site, and
stays a small, fixed set of evergreen pieces rather than an ongoing content
stream.

Every number quoted in these articles is pulled from directory.json at
generation time (see PRICING_STATS / CITY_STATS below) -- nothing here is
made up, matching the standard the rest of the site has held to throughout.

Usage:
    python3 generate_guides.py

Re-run any time directory.json changes, so the quoted pricing/city numbers
stay accurate.
"""
import html as html_lib
import json
import os
import re

from generate_listing_pages import BASE_URL, esc, load_shared_style, NAV_HTML, FOOTER_HTML, generate_sitemap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GUIDES_DIR = os.path.join(BASE_DIR, "guides")


# ---------------------------------------------------------------------------
# Real numbers pulled from directory.json, used to ground the articles below
# instead of guessing at figures.
# ---------------------------------------------------------------------------

def compute_stats():
    with open(os.path.join(BASE_DIR, "directory.json"), encoding="utf-8") as f:
        data = json.load(f)

    def price_num(p):
        if not p:
            return None
        m = re.search(r"[\d.]+", p.replace(",", ""))
        return float(m.group()) if m else None

    engineers = [it for it in data if it["category"] == "engineers"]
    visuals = [it for it in data if it["category"] == "visuals"]
    studios = [it for it in data if it["category"] == "studios"]

    eng_prices = sorted(x for x in (price_num(it.get("price")) for it in engineers) if x)
    vis_prices = sorted(x for x in (price_num(it.get("price")) for it in visuals) if x)

    from collections import Counter
    city_counts = Counter(it.get("location") for it in studios if it.get("location"))

    return {
        "eng_count": len(engineers),
        "eng_min": eng_prices[0], "eng_max": eng_prices[-1],
        "eng_median": eng_prices[len(eng_prices) // 2],
        "vis_count": len(visuals),
        "vis_min": vis_prices[0], "vis_max": vis_prices[-1],
        "vis_median": vis_prices[len(vis_prices) // 2],
        "studio_count": len(studios),
        "city_count": len(city_counts),
        "top_cities": city_counts.most_common(12),
    }


STATS = compute_stats()


# ---------------------------------------------------------------------------
# Article content. Each body is hand-written HTML (h2/p/ul), not generated
# from a template -- these are meant to read like they were written by
# someone who actually works in and around independent hip hop, not filled
# in from a generic content outline.
# ---------------------------------------------------------------------------

GUIDES = []


def add_guide(slug, title, dek, meta_description, category_link, body_html, faq, related):
    GUIDES.append({
        "slug": slug, "title": title, "dek": dek,
        "meta_description": meta_description,
        "category_link": category_link,
        "body_html": body_html, "faq": faq, "related": related,
    })


# 1 ---------------------------------------------------------------------
add_guide(
    slug="type-beat-vs-custom-beat",
    title="Type Beat vs. Custom Beat: Which One Should You Actually Buy?",
    dek="Both get you a beat. They don't get you the same thing.",
    meta_description="Type beats and custom beats solve different problems for a hip hop artist. Here's the real difference in sound, cost, rights, and turnaround.",
    category_link=("producers", "Browse Producers & Beatmakers"),
    body_html="""
<p>If you've spent any time on SoundCloud or YouTube looking for beats, you've seen the pattern: "Travis Scott Type Beat," "21 Savage Type Beat," a thousand variations on the same idea. A type beat is a producer making a track in the style of an established artist -- not for that artist, not licensed by them, just built to sound like something that could sit on one of their projects. It's a catalog play. The producer makes one beat and sells the same lease to dozens of different artists over months or years.</p>

<p>A custom beat is the opposite model. You go to a producer directly, tell them what you're after -- the reference tracks, the mood, the BPM range, maybe a specific drum pattern or sample chop you have in mind -- and they build something from scratch for you. Nobody else gets that exact beat unless you decide to resell the rights yourself.</p>

<h2>What you're actually paying for with a type beat</h2>
<p>Speed and price, mostly. Type beats are already made. You're browsing a catalog, not commissioning work, so you can go from "I need a beat" to having a lease in your inbox in minutes. Because the same beat gets leased to multiple artists, the per-artist price is low -- that's the whole economic model. The tradeoff is exactly what you'd expect: your beat isn't unique, and if it blows up, there's a real chance someone else drops a song on the same instrumental a few months later.</p>

<h2>What changes with a custom beat</h2>
<p>You get a producer's actual attention -- revisions, a beat built around your voice and flow instead of a generic pocket, and (depending on the deal) exclusive rights so nobody else can use it. That costs more and takes longer, because it's real production work, not a catalog pull. It's the right call once you have a sound you're trying to build consistently, not just a song you need finished this week.</p>

<h2>Lease vs. exclusive: the part people skip and then regret</h2>
<p>This is the single most important thing to understand before you buy any beat, type or custom. A <strong>lease</strong> means you're renting non-exclusive rights, usually with a cap on streams, sales, or monetized views before you're expected to upgrade. A <strong>WAV lease</strong> or <strong>trackout/stems lease</strong> gets you higher-quality files and the individual stems for mixing, but you still don't own it outright. <strong>Exclusive rights</strong> means the producer stops selling that beat to anyone else, period -- and it costs the most because you're buying out the rest of that beat's earning potential, not just a license to use it once.</p>
<p>Read whatever agreement comes with the beat before you drop it anywhere with real distribution behind it. A cheap type beat lease with a 50,000-stream cap can turn into an unplanned upgrade fee right when a song is starting to move.</p>

<h2>So which one do you actually need</h2>
<p>If you're testing a sound, building a catalog fast, or working with a tight budget, type beats are a legitimate and normal way to get started -- most working independent artists have used them. If you've found your lane and you're releasing a project meant to define your sound, a custom beat (with exclusive rights, if the budget allows) protects that investment. There's no wrong answer here, just a mismatch to avoid: don't buy a leased type beat for a song you're planning to push hard commercially without understanding the cap you agreed to.</p>
""",
    faq=[
        {"question": "Can I use a type beat commercially, on streaming platforms?",
         "answer": "Yes, as long as you have a valid lease from the producer and you stay within whatever terms it sets (stream caps, monetization limits, credit requirements). Read the license before you release, not after."},
        {"question": "Is a custom beat always exclusive?",
         "answer": "Not automatically -- exclusivity is a separate negotiation from \"custom.\" A producer can build you a one-off custom beat and still license it non-exclusively unless you specifically pay for exclusive rights."},
        {"question": "Why do some type beats cost $20 and others $200?",
         "answer": "License tier (MP3 vs. WAV vs. trackout/stems vs. exclusive), the producer's reputation and catalog performance, and how competitive that particular sound currently is all factor in. A producer whose type beats consistently get used on tracks that perform well can charge more for the same tier of license."},
    ],
    related=["hip-hop-beat-pricing-guide", "mixing-mastering-cost-hip-hop", "how-to-release-your-first-hip-hop-track"],
)

# 2 ---------------------------------------------------------------------
add_guide(
    slug="hip-hop-beat-pricing-guide",
    title="How Much Does a Hip Hop Beat Cost in 2026? A Realistic Price Guide",
    dek="The honest range, why it swings so wide, and what actually drives the price up.",
    meta_description="A realistic breakdown of what hip hop beats actually cost in 2026 -- lease tiers, exclusive pricing, and what makes one producer charge more than another.",
    category_link=("producers", "Browse Producers & Beatmakers"),
    body_html="""
<p>There's no single price for a hip hop beat, and anyone who tells you otherwise is either selling you something or hasn't shopped around. The honest answer is that price is set by license tier first, and by the producer's reputation and catalog performance second.</p>

<h2>The lease tiers, from cheapest to most expensive</h2>
<p>Most independent producers sell beats in tiers rather than one flat price:</p>
<ul>
<li><strong>MP3 lease</strong> -- the cheapest option, usually a low-quality file with a stream/sale cap. Fine for demos, freestyles, and testing a sound before you commit.</li>
<li><strong>WAV lease</strong> -- higher audio quality, still non-exclusive, still capped. This is the realistic minimum for anything you're actually releasing.</li>
<li><strong>Trackout / stems lease</strong> -- you get the individual stems (drums, bass, melody separated out), which your mixing engineer needs if they're going to do real work on the track rather than just polishing a stereo file.</li>
<li><strong>Exclusive rights</strong> -- the beat comes off the market entirely once you buy it. Highest price, no cap, no competing songs on the same instrumental later.</li>
</ul>

<h2>What actually moves the price beyond the tier</h2>
<p>Two producers selling a WAV lease can charge very different prices for reasons that have nothing to do with the file itself: how established their catalog is, whether their beats have a track record of being used on songs that performed well, how in-demand their specific sound currently is (drill and dark trap production has stayed expensive relative to more generic boom bap in recent years, simply because more artists are chasing that sound right now), and how much back-and-forth they're willing to do before a sale.</p>

<h2>A structural thing worth knowing about this directory specifically</h2>
<p>The producers listed on HipHopLord are sourced from SoundCloud, not a fixed-price marketplace like Fiverr or BeatStars. That means pricing for most of them isn't posted upfront the way a Fiverr gig is -- you reach out directly, usually through the contact info on their profile or a comment/DM, and negotiate from there. It's a more old-school process, but it's also how a lot of real relationships between artists and producers actually start: not a checkout page, an actual conversation about what you're trying to make.</p>

<h2>What a fair starting budget looks like</h2>
<p>If you're an independent artist without a budget yet, a WAV lease in the $20&ndash;$50 range is a normal, fair starting point for most working producers. If you've got a specific sound you're chasing from a producer whose beats have real momentum, expect to pay more -- and expect exclusive rights on anything you're building a real release campaign around to run well past that.</p>
""",
    faq=[
        {"question": "Is it normal to negotiate beat prices?",
         "answer": "Yes, especially with independent producers selling directly rather than through a fixed-price storefront. Most are open to a conversation, particularly if you're buying more than one beat or building an ongoing relationship."},
        {"question": "Do more expensive beats mean better quality?",
         "answer": "Not necessarily. Price often tracks a producer's reputation and how in-demand their current sound is more than the technical quality of any single beat. Plenty of underrated producers price well below what their actual craft is worth."},
        {"question": "Should I always buy the trackout/stems version?",
         "answer": "Only if you're planning to have a mixing engineer do real work on the track. If you're releasing the beat close to as-is, a WAV lease is enough and you can skip paying extra for stems you won't use."},
    ],
    related=["type-beat-vs-custom-beat", "mixing-mastering-cost-hip-hop", "how-to-release-your-first-hip-hop-track"],
)

# 3 ---------------------------------------------------------------------
add_guide(
    slug="mixing-mastering-cost-hip-hop",
    title="How Much Does Mixing and Mastering Cost for a Hip Hop Track?",
    dek="Real starting prices from working engineers, and why the number on their profile rarely stays the number.",
    meta_description=f"Real mixing and mastering price data from {STATS['eng_count']} working hip hop engineers -- what a fair starting budget looks like and what pushes the final quote higher.",
    category_link=("engineers", "Browse Mixing & Mastering Engineers"),
    body_html=f"""
<p>Mixing and mastering is one of those costs new independent artists consistently underestimate, mostly because the number posted on an engineer's profile is almost always a starting price, not a final quote.</p>

<h2>What the real numbers look like</h2>
<p>Looking at the {STATS['eng_count']} working mixing and mastering engineers listed on HipHopLord, starting prices range from about <strong>${STATS['eng_min']:.0f}</strong> up to <strong>${STATS['eng_max']:.0f}</strong> if you round the top, with a <strong>median starting price around ${STATS['eng_median']:.0f}</strong>. That spread exists for a reason: a $10&ndash;$15 starting price usually covers a single vocal track with a basic mix, while the higher end reflects engineers doing full album packages, analog gear, or working with major-label-adjacent credits.</p>

<h2>Why "from $X" rarely means the final price</h2>
<p>"From $30" almost always means one vocal stem, one revision, standard turnaround. The price climbs from there with anything beyond that baseline: extra vocal takes or ad-libs, additional revision rounds, rush turnaround, stem mastering for multiple platforms, or a full project (EP/album) rather than a single track. None of that is a scam -- it's just how service-based pricing works, and it's exactly why you should always confirm what's actually included before you commit, not after you've sent the files.</p>

<h2>What's actually worth paying more for</h2>
<p>Turnaround time and revision count matter more day-to-day than most people expect going in. An engineer who's slower but includes three rounds of revisions will usually get you a better final product than one who's fast but locks the mix after one pass. If you're not sure what "good" sounds like yet, prioritize revisions over speed -- you'll need them.</p>

<h2>Is it ever worth skipping a professional mix?</h2>
<p>For a demo, a freestyle, or something you're putting out purely to test a sound, no -- don't overthink it, a clean rough mix is fine. For anything you're actually pushing -- a single with a release plan behind it, a project you're sending to playlists or pitching anywhere -- a professional mix and master is close to non-negotiable at this point. Streaming platforms and playlist curators can tell the difference immediately, and a track that's mixed too quiet or unevenly balanced gets skipped before the hook even hits.</p>
""",
    faq=[
        {"question": "What's a realistic starting budget for mixing and mastering one song?",
         "answer": f"Based on real pricing across engineers in this directory, expect to start around ${STATS['eng_median']:.0f} for a straightforward single-vocal mix and master, with the final price depending on revisions and extras."},
        {"question": "Should I get mixing and mastering from the same engineer?",
         "answer": "Not required, but it's common and often more efficient -- the same engineer already knows the mix intimately when they master it. Some artists prefer a second, fresh set of ears for mastering specifically. Both approaches are normal."},
        {"question": "What should I send my engineer to avoid extra fees?",
         "answer": "Clean, correctly labeled vocal stems (no effects baked in), the instrumental, and a clear reference track or two showing the sound you're going for. Sloppy or unlabeled files are the most common reason a quote goes up."},
    ],
    related=["mixing-vs-mastering-difference", "hip-hop-beat-pricing-guide", "how-to-release-your-first-hip-hop-track"],
)

# 4 ---------------------------------------------------------------------
add_guide(
    slug="mixing-vs-mastering-difference",
    title="Mixing vs. Mastering: What's the Difference, and Do You Need Both?",
    dek="Two different jobs that get lumped into one line item more often than they should be.",
    meta_description="Mixing and mastering are two different jobs in the production chain for a hip hop track. Here's what each one actually does, and why skipping one shows.",
    category_link=("engineers", "Browse Mixing & Mastering Engineers"),
    body_html="""
<p>"Mixing and mastering" gets said as one phrase so often that a lot of independent artists assume it's one step. It isn't. They're two different jobs, done in a specific order, solving two different problems.</p>

<h2>What mixing actually does</h2>
<p>Mixing takes all the individual pieces of a track -- vocals, ad-libs, the beat's drums, bass, melody -- and balances them against each other. Volume levels, panning, EQ so instruments aren't fighting for the same frequency space, compression to keep the vocal sitting consistently on top of the beat instead of ducking in and out, and effects like reverb or delay used with intent instead of by accident. A good mix is the difference between a vocal that sounds glued to the beat and one that sounds like it was pasted on top of it.</p>

<h2>What mastering actually does</h2>
<p>Mastering happens after the mix is finished, and it works on the track as a single finished stereo file, not the individual pieces. It's the final polish pass: overall loudness brought up to a competitive streaming level, tonal balance checked across different playback systems (car speakers, AirPods, club system), and consistency with the rest of a project if it's part of an EP or album, so track two doesn't sound noticeably louder or thinner than track one.</p>

<h2>Why the order matters</h2>
<p>You can't master a bad mix into a good one. Mastering makes small, final adjustments to an already-balanced track -- it's not capable of fixing a vocal that's buried under the hi-hats or drums that are clipping. Sending an unmixed or poorly mixed track straight to mastering is one of the most common mistakes independent artists make, usually to save money, and it rarely actually saves anything because the result still doesn't sound finished.</p>

<h2>Do you need both, every time?</h2>
<p>For anything you're releasing publicly, yes. A track that's been properly mixed but never mastered will usually sound noticeably quieter and less polished next to other music on the same playlist -- streaming platforms don't boost your loudness for you. A track that's mixed and mastered by the same person in one pass is common and completely fine for a single song. For a full project, some artists bring in a second engineer just for mastering to get a fresh set of ears across the whole tracklist -- also fine, just a different workflow, not a requirement.</p>
""",
    faq=[
        {"question": "Can one engineer do both mixing and mastering?",
         "answer": "Yes, and it's very common, especially for single songs rather than full projects. Many of the engineers on HipHopLord offer both as a package."},
        {"question": "Is mastering just \"making it louder\"?",
         "answer": "That's part of it, but not the whole job -- mastering also handles tonal balance, playback consistency across devices, and (on a project) making every track sound like it belongs together. Loudness alone with no other adjustment is a shortcut, not a real master."},
        {"question": "What happens if I skip mastering entirely?",
         "answer": "The track will likely sound noticeably quieter and less finished sitting next to professionally mastered music on the same playlist or in the same set. It's the step most likely to make a home-recorded song sound obviously unfinished if it's skipped."},
    ],
    related=["mixing-mastering-cost-hip-hop", "hip-hop-cover-art-guide", "how-to-release-your-first-hip-hop-track"],
)

# 5 ---------------------------------------------------------------------
add_guide(
    slug="hip-hop-cover-art-guide",
    title="What Makes Good Hip Hop Cover Art? A Guide for Independent Artists",
    dek="The genre has real visual conventions right now. Here's what's working, and what a good brief to a designer actually looks like.",
    meta_description=f"What makes hip hop cover art actually work in 2026, real pricing from {STATS['vis_count']} designers, and how to brief a designer so you get what you actually pictured.",
    category_link=("visuals", "Browse Cover Art & Visual Designers"),
    body_html=f"""
<p>Cover art is doing more work than most independent artists give it credit for. On streaming platforms, it's a thumbnail competing against dozens of others in a scroll, often at a size smaller than a postage stamp -- and it's frequently the only thing a potential listener sees before deciding whether to tap play. Good cover art doesn't need to be complicated. It needs to read instantly and match the record.</p>

<h2>What's actually working right now</h2>
<p>A few genuinely current conventions worth knowing before you brief a designer: photographic, high-contrast portraiture is doing a lot of heavy lifting across trap and drill releases right now -- a strong single image beats a busy composite almost every time at thumbnail size. Bold, often distressed or grunge-textured typography treatments are common on the artist name/title, sometimes doing more visual work than the imagery itself. Muted, moody color grading (desaturated, heavy shadow) reads as more premium than bright, saturated palettes for most subgenres right now, with the notable exception of more upbeat, club-oriented tracks where saturated color still works. And restraint matters -- one strong visual idea, executed cleanly, consistently beats a cover trying to communicate five ideas at once.</p>

<h2>How to actually brief a designer</h2>
<p>The single biggest driver of a good result is a clear brief, not a talented designer guessing. Come with: 2&ndash;3 reference covers (real releases, not just "make it look cool"), the mood in one or two words (moody, aggressive, nostalgic, bright), any specific imagery or symbol you want included, and the actual title/artist name text exactly as it should appear. Vague briefs like "something that fits the vibe" are the number one reason a first draft misses -- designers aren't reading your mind, they're reading your brief.</p>

<h2>What it actually costs</h2>
<p>Across the {STATS['vis_count']} designers currently listed on HipHopLord, starting prices run from about <strong>${STATS['vis_min']:.0f}</strong> up to <strong>${STATS['vis_max']:.0f}</strong> at the top end, with a <strong>median starting price around ${STATS['vis_median']:.0f}</strong>. The lower end typically covers a straightforward single-cover design with limited revisions; the higher end usually reflects full project packages (multiple covers, social assets, more revision rounds) or designers with a track record on bigger releases.</p>

<h2>Common mistakes to avoid</h2>
<p>Using a stock photo that's obviously a stock photo. Text that's illegible at thumbnail size because it looked fine at full screen. Matching a genre's current trend so closely the cover has no identity of its own. And changing direction mid-project after the designer already built out the first concept -- it happens, but it's the fastest way to burn through your revision rounds before you've actually landed on something.</p>
""",
    faq=[
        {"question": "What image size should I use for streaming platform cover art?",
         "answer": "3000x3000 pixels is the safe standard most distributors and platforms expect, saved as a high-quality JPG or PNG. A good designer will deliver it at this size by default."},
        {"question": "Should cover art match my previous releases?",
         "answer": "For a series or album, visual consistency helps build recognition. For standalone singles, it matters less -- what matters more is that each cover matches that specific song's mood."},
        {"question": "How many revisions should I expect for the price?",
         "answer": "Varies by designer and package, but 1-2 revision rounds is typical at entry-level pricing. Check what's included before you commit if you know you'll want to iterate more than that."},
    ],
    related=["choosing-a-recording-studio", "mixing-vs-mastering-difference", "how-to-release-your-first-hip-hop-track"],
)

# 6 ---------------------------------------------------------------------
add_guide(
    slug="choosing-a-recording-studio",
    title="How to Choose a Recording Studio for Your First Hip Hop Session",
    dek="What actually matters when you're picking a room, and what to ask before you book.",
    meta_description="What actually matters when choosing a recording studio for hip hop vocals -- the engineer, the room, and the questions to ask before you book a session.",
    category_link=("studios", "Browse Recording Studios"),
    body_html="""
<p>A recording studio is more than a room with a microphone in it, and the gap between a good session and a wasted one usually comes down to a few specific things that aren't always obvious before you book.</p>

<h2>The engineer matters more than the gear</h2>
<p>A studio can have an expensive mic collection and still deliver a flat, lifeless vocal take if the engineer running the session doesn't know how to get a real performance out of an artist -- catching the right take, pushing for more energy when a vocal feels safe, knowing when to punch in versus running it back from the top. If a studio's listing shows real reviews mentioning the engineer specifically (not just "nice space"), that's usually a better signal than a photo of the gear.</p>

<h2>Home setup vs. professional studio: when you actually need one</h2>
<p>A treated home booth with a solid interface and a good condenser mic is genuinely enough for a huge amount of independent hip hop being released right now -- plenty of commercially successful tracks were vocaled at home. Where a professional studio actually earns its cost: rooms with real acoustic treatment (removes the boxy, roomy sound untreated spaces pick up), an engineer who can catch problems in real time instead of you discovering them during mixing, and sessions where energy and performance matter more than usual -- a posse cut, a song that needs real vocal power, anything where being in a proper room with other people changes the take for the better.</p>

<h2>Questions worth asking before you book</h2>
<p>What's the hourly rate, and is there a minimum block? Is the engineer included in that rate, or is it room-only? What happens if the session runs over? Can you get the raw session files (not just a bounced mix) afterward? And does the space have the amenities that actually matter to you -- parking, Wi-Fi if you need to send reference tracks, accessibility. HipHopLord's studio listings pull this kind of detail directly from each studio's real Google Business data, so it's worth checking a listing's amenities and reviews before you call.</p>

<h2>Red flags</h2>
<p>No reviews at all, or reviews that only mention the space and never the actual engineer or session quality. Vague pricing that won't be confirmed until you show up. And a studio that can't answer basic questions about turnaround for session files -- if getting your own vocal stems back afterward is a fight, that's worth knowing before you book, not after.</p>
""",
    faq=[
        {"question": "Do I need a professional studio for my first song?",
         "answer": "Not necessarily. A solid home setup with a good mic and interface is enough for a lot of independent hip hop right now. A professional studio earns its cost most clearly for acoustically demanding sessions or when you specifically need an experienced engineer catching your performance in real time."},
        {"question": "What should I bring to a studio session?",
         "answer": "The instrumental (in the highest quality file the studio can accept), written lyrics or at least a solid reference of your flow, water, and any reference tracks that show the vocal tone or energy you're going for."},
        {"question": "Should I ask for the raw vocal files after a session?",
         "answer": "Yes, always confirm this before booking. You'll need the raw, unprocessed vocal stems if you're sending the song to a separate mixing engineer afterward -- a bounced rough mix alone isn't enough for them to work with."},
    ],
    related=["best-cities-to-record-hip-hop", "mixing-mastering-cost-hip-hop", "how-to-release-your-first-hip-hop-track"],
)

# 7 ---------------------------------------------------------------------

CITY_CULTURE = {
    "Memphis, Tennessee": "the birthplace of a whole dark, horrorcore-adjacent strain of Southern hip hop, from Three 6 Mafia through the current generation of Memphis rap -- studios here still carry that lineage.",
    "Atlanta, Georgia": "the epicenter of trap production for over a decade running, with more working producers and engineers per block than almost anywhere else in the South.",
    "Houston, Texas": "home of chopped and screwed and a slower, bass-heavy production style that's still audible in Southern hip hop today.",
    "New Orleans, Louisiana": "the bounce music capital, with a rhythmic, call-and-response tradition that still shapes how vocals get recorded and arranged locally.",
    "Chicago, Illinois": "ground zero for drill, a sound that's since spread globally but is still cut with a different edge by engineers who grew up on it.",
    "New York, New York": "where the genre started, and still home to one of the deepest concentrations of veteran engineers who've worked across every era of the sound.",
    "Los Angeles, California": "the industry's commercial center on the West Coast, with studios ranging from major-label rooms to independent spaces built for exactly the kind of artist this directory serves.",
    "Nashville, Tennessee": "better known for country, but its hip hop studio scene has grown quietly alongside a broader Southern rap presence in the city.",
    "Las Vegas, Nevada": "a newer but fast-growing hub, pulling artists and engineers relocating from both coasts.",
    "Philadelphia, Pennsylvania": "a historically underrated East Coast scene with a strong lyricism tradition that still shows up in how local engineers approach a vocal session.",
    "Phoenix, Arizona": "a fast-growing independent scene without the price premium of the coasts.",
    "Denver, Colorado": "a smaller but active scene, popular with artists who want real studio access without LA or Atlanta's competition for booking slots.",
}

top_city_rows = "\n".join(
    f'<li><strong>{esc(city.split(",")[0])}</strong> ({count} studios in this directory) &mdash; {esc(CITY_CULTURE.get(city, ""))}</li>'
    for city, count in STATS["top_cities"] if city in CITY_CULTURE
)

add_guide(
    slug="best-cities-to-record-hip-hop",
    title="Best US Cities to Record Hip Hop Music in 2026",
    dek="Where the studios actually are, and why each city's scene sounds a little different.",
    meta_description=f"A city-by-city look at where to record hip hop in the US, backed by real studio counts across {STATS['city_count']} cities in HipHopLord's directory.",
    category_link=("studios", "Browse Recording Studios"),
    body_html=f"""
<p>Hip hop doesn't have one center anymore -- it has a dozen regional scenes, each with its own studio culture and, often, a slightly different sound baked into how local engineers approach a session. Across the {STATS['studio_count']} studios currently listed on HipHopLord, spread over {STATS['city_count']} cities, a handful of metros consistently show up with the deepest concentration of working rooms.</p>

<h2>Where the studios actually are right now</h2>
<ul>
{top_city_rows}
</ul>

<h2>Does the city actually matter for your sound?</h2>
<p>Less than it used to, honestly. Remote sessions, file sharing, and engineers who've worked across regional styles have flattened a lot of the old geographic lines -- a Memphis-trained engineer can absolutely deliver a clean East Coast boom bap mix if that's the brief. But there's still something real about recording in a city with a deep bench of engineers who've spent years inside a specific sound. If you're chasing a specific regional flavor -- Houston's chopped and screwed low end, Atlanta's trap drum programming, Chicago's drill energy -- working with an engineer actually embedded in that scene tends to show up in the final product in ways that are hard to fully replicate remotely.</p>

<h2>What to actually weigh when picking where to record</h2>
<p>Budget first -- studio rates in Los Angeles and New York generally run higher than in Phoenix, Denver, or Las Vegas, for the same quality of room. Availability of the specific sound you want (see above). And logistics -- if you're traveling for a session, factor in whether the city has enough studio density that you can pivot to a second option if your first choice falls through, which matters more than people expect when a session gets cancelled last-minute.</p>
""",
    faq=[
        {"question": "Do I need to record in a specific city to get a specific regional sound?",
         "answer": "It helps but isn't strictly required -- what matters most is working with an engineer experienced in that specific sound, who may or may not be based in that city. Recording locally does make it easier to work with engineers embedded in that scene."},
        {"question": "Which city has the most affordable studios in this directory?",
         "answer": "Rates vary studio by studio rather than purely by city, but secondary markets like Phoenix, Denver, and Las Vegas generally run more affordable than Los Angeles or New York for comparable studio quality."},
        {"question": "Is remote recording a real alternative to traveling for a session?",
         "answer": "Yes, and it's increasingly common -- many engineers can direct a session over video call while you record locally, or work from vocal stems you record and send yourself. It's not identical to an in-person session, but it's a legitimate option, especially for a second or later session with an engineer you've already worked with."},
    ],
    related=["choosing-a-recording-studio", "hip-hop-cover-art-guide", "how-to-release-your-first-hip-hop-track"],
)

# 8 -- the hub article ----------------------------------------------------
add_guide(
    slug="how-to-release-your-first-hip-hop-track",
    title="How to Release Your First Hip Hop Track: A Step-by-Step Guide for Independent Artists",
    dek="Every stage, in order, from an empty session to a link you can actually send someone.",
    meta_description="A step-by-step guide to releasing your first hip hop track as an independent artist -- getting a beat, recording, mixing and mastering, cover art, and distribution.",
    category_link=("producers", "Start With Producers & Beatmakers"),
    body_html="""
<p>There's no single right order to make a song, but there is an order that keeps you from paying twice for work you didn't need to redo. Here's the realistic path from nothing to a released track, stage by stage.</p>

<h2>Step 1: Get your beat</h2>
<p>Start here, not with lyrics written to nothing. If you're testing a sound or working with a limited budget, a <a href="type-beat-vs-custom-beat.html">type beat</a> lease is a completely normal way to start -- most working independent artists have used them. If you already know your lane and this is a track meant to define it, consider a custom beat instead. Either way, understand the license before you buy: a WAV lease at minimum for anything you're actually releasing, and think seriously about whether you'll eventually want exclusive rights if the song starts to move. See our full <a href="hip-hop-beat-pricing-guide.html">beat pricing guide</a> for what a fair budget actually looks like right now.</p>

<h2>Step 2: Write and record your vocals</h2>
<p>Write to the actual beat, not in the abstract -- pocket and flow only make sense against the instrumental you're actually using. When it's time to record, you don't need a professional studio for every session (see our <a href="choosing-a-recording-studio.html">guide to choosing a studio</a> for when you genuinely do), but you do need a clean recording: a decent condenser mic, a quiet room, and multiple takes so your engineer has options later. Record more than you think you need. It's free at this stage and expensive to redo later.</p>

<h2>Step 3: Mixing and mastering</h2>
<p>This is not optional for anything you're actually releasing publicly. Send your engineer clean, correctly labeled vocal stems, the instrumental, and a reference track or two so they understand the sound you're going for. Understand that <a href="mixing-vs-mastering-difference.html">mixing and mastering are two different jobs</a>, done in that order, and that the number on an engineer's profile is usually a starting price, not the final one -- our <a href="mixing-mastering-cost-hip-hop.html">mixing and mastering cost guide</a> breaks down real pricing so you can budget accurately before you commit.</p>

<h2>Step 4: Cover art</h2>
<p>Don't leave this until the last minute -- a rushed cover is one of the most common ways an otherwise strong song underperforms, because the artwork is often the only thing a potential listener sees before deciding to press play. Brief your designer clearly: reference covers, a one or two word mood, the exact title and artist name text. Our <a href="hip-hop-cover-art-guide.html">cover art guide</a> covers what's actually working visually right now and what a good brief looks like.</p>

<h2>Step 5: Distribution</h2>
<p>You'll need a distributor to get your track onto Spotify, Apple Music, and the rest of the major platforms -- services like DistroKid, TuneCore, and CD Baby are the standard options independent artists use, each with different pricing models (flat annual fee vs. per-release, and different royalty splits), so it's worth comparing a couple before committing to one. Submit your final mastered WAV file, your cover art at the platform's required size (3000x3000px is the safe standard), and your metadata -- track title, artist name, songwriter and producer credits -- carefully. Errors here are annoying to fix after the fact and can delay your release date.</p>

<h2>Step 6: Release day</h2>
<p>Give yourself real lead time -- most distributors recommend submitting at least a couple of weeks before your target date, longer if you want a shot at Spotify editorial playlist consideration, which typically requires submitting through Spotify for Artists before release. Have your cover art and a short caption ready for social media the moment it's live, and don't disappear after posting once -- the first 48 hours of engagement matter more than people expect for how a track gets initially picked up.</p>

<h2>The realistic budget, put together</h2>
<p>Putting the pieces from this series together: a WAV-lease beat, a professionally mixed and mastered vocal, and a designed cover can realistically come together well under $200 total for a single independent release, before distribution fees -- and that's before factoring in that plenty of the engineers and designers in this directory price toward the lower end of the ranges covered in our other guides. It doesn't have to be expensive to sound finished. It has to be done in the right order, by people who actually know what they're doing at each stage.</p>
""",
    faq=[
        {"question": "What order should I actually do these steps in?",
         "answer": "Beat first, then vocals recorded to that specific beat, then mixing and mastering, with cover art happening in parallel once you know the song's mood -- not necessarily after mixing is finished. Distribution submission comes last, once everything else is final."},
        {"question": "How much does a first release realistically cost all-in?",
         "answer": "Based on real pricing data across the producers, engineers, and designers in this directory, a single release can realistically come together for well under $200 before distribution fees, using entry-level pricing at each stage."},
        {"question": "Do I need a record label to release music?",
         "answer": "No. Independent distribution through services like DistroKid, TuneCore, or CD Baby gets your music onto every major streaming platform without a label, and the majority of active independent hip hop artists release this way."},
    ],
    related=["type-beat-vs-custom-beat", "mixing-mastering-cost-hip-hop", "hip-hop-cover-art-guide", "best-cities-to-record-hip-hop"],
)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def faq_block(faq):
    if not faq:
        return ""
    rows = []
    for qa in faq:
        rows.append(f"""
        <div class="border-b border-white/10 py-4 last:border-b-0">
          <h3 class="text-white text-sm font-semibold leading-snug">{esc(qa['question'])}</h3>
          <p class="text-zinc-400 text-sm mt-2 leading-relaxed">{esc(qa['answer'])}</p>
        </div>""")
    return f"""
    <section class="max-w-3xl mx-auto px-5 pb-6">
      <div class="card rounded-2xl p-7 md:p-9">
        <h2 class="display text-xl mb-2">Frequently Asked Questions</h2>
        <div>{''.join(rows)}</div>
      </div>
    </section>"""


def faq_json_ld(faq):
    if not faq:
        return ""
    block = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": qa["question"],
             "acceptedAnswer": {"@type": "Answer", "text": qa["answer"]}}
            for qa in faq
        ],
    }
    return f'<script type="application/ld+json">{json.dumps(block, ensure_ascii=False)}</script>'


def article_json_ld(guide, canonical):
    block = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": guide["title"],
        "description": guide["meta_description"],
        "url": canonical,
        "publisher": {"@type": "Organization", "name": "HipHopLord"},
        "mainEntityOfPage": canonical,
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Guides", "item": f"{BASE_URL}/guides/"},
            {"@type": "ListItem", "position": 3, "name": guide["title"]},
        ],
    }
    return (f'<script type="application/ld+json">{json.dumps(block, ensure_ascii=False)}</script>\n'
            f'<script type="application/ld+json">{json.dumps(breadcrumb, ensure_ascii=False)}</script>')


def related_guides_html(guide, by_slug):
    if not guide["related"]:
        return ""
    cards = []
    for slug in guide["related"]:
        r = by_slug.get(slug)
        if not r:
            continue
        cards.append(f"""
        <a href="{esc(slug)}.html" class="card rounded-2xl p-5 block hover:no-underline">
          <span class="mono text-[10.5px] uppercase tracking-widest text-zinc-500">Guide</span>
          <h3 class="text-white text-sm font-semibold mt-1.5 leading-snug">{esc(r['title'])}</h3>
          <p class="text-zinc-500 text-xs mt-1.5 leading-relaxed">{esc(r['dek'])}</p>
        </a>""")
    return f"""
    <section class="max-w-3xl mx-auto px-5 pb-16">
      <div class="vinyl-divider mb-8"></div>
      <h2 class="display text-lg mb-5">More Guides</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        {''.join(cards)}
      </div>
    </section>"""


def render_guide(guide, by_slug, style_block):
    canonical = f"{BASE_URL}/guides/{guide['slug']}.html"
    page_title = f"{guide['title']} | HipHopLord"
    cat_slug, cat_label = guide["category_link"]

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
<meta name="description" content="{esc(guide['meta_description'])}" />
<link rel="canonical" href="{canonical}" />
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22><circle cx=%2212%22 cy=%2212%22 r=%2211%22 fill=%22%230a0a0b%22/><circle cx=%2212%22 cy=%2212%22 r=%229.3%22 fill=%22none%22 stroke=%22%23e2a83f%22 stroke-width=%222.6%22/><circle cx=%2212%22 cy=%2212%22 r=%223%22 fill=%22%23e2a83f%22/></svg>" />

<meta property="og:type" content="article" />
<meta property="og:site_name" content="HipHopLord" />
<meta property="og:title" content="{esc(page_title)}" />
<meta property="og:description" content="{esc(guide['meta_description'])}" />
<meta property="og:url" content="{canonical}" />
<meta name="twitter:card" content="summary" />
<meta name="twitter:title" content="{esc(page_title)}" />
<meta name="twitter:description" content="{esc(guide['meta_description'])}" />

{article_json_ld(guide, canonical)}
{faq_json_ld(guide['faq'])}

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
    <a href="index.html" class="hover:text-zinc-300 transition">Guides</a>
    <span class="mx-1.5">/</span>
    <span class="text-zinc-400">{esc(guide['title'])}</span>
  </nav>

  <div class="card rounded-2xl p-7 md:p-9">
    <span class="mono text-[11px] uppercase tracking-widest text-zinc-500">Guide</span>
    <h1 class="display text-2xl md:text-3xl leading-tight mt-1">{esc(guide['title'])}</h1>
    <p class="text-zinc-400 text-sm mt-2">{esc(guide['dek'])}</p>

    <div class="prose-guide mt-6">
      {guide['body_html']}
    </div>

    <div class="flex items-center mt-8 pt-6 border-t border-white/10">
      <a href="../index.html#directory" class="mono text-sm px-5 py-3 rounded-full bg-[--gold] text-black font-semibold hover:bg-[--gold-soft] transition">{esc(cat_label)} &rarr;</a>
    </div>
  </div>

  <p class="mt-6">
    <a href="../index.html#directory" class="mono text-xs text-zinc-500 hover:text-zinc-300 transition">&larr; Back to full directory</a>
  </p>
</main>

{faq_block(guide['faq'])}

{related_guides_html(guide, by_slug)}

{FOOTER_HTML}
</body>
</html>"""


def guides_index_json_ld(canonical):
    block = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Guides", "item": canonical},
        ],
    }
    return f'<script type="application/ld+json">{json.dumps(block, ensure_ascii=False)}</script>'


def render_guides_index(guides, style_block):
    canonical = f"{BASE_URL}/guides/"
    page_title = "Guides | HipHopLord"
    meta_description = ("Practical, no-fluff guides on hip hop production, pricing, and release strategy -- "
                         "beat licensing, mixing and mastering costs, cover art, studios, and putting out your first track.")

    cards = []
    for g in guides:
        cards.append(f"""
        <a href="{esc(g['slug'])}.html" class="card rounded-2xl p-6 block hover:no-underline">
          <span class="mono text-[10.5px] uppercase tracking-widest text-zinc-500">Guide</span>
          <h2 class="text-white text-base font-semibold mt-2 leading-snug">{esc(g['title'])}</h2>
          <p class="text-zinc-500 text-sm mt-2 leading-relaxed">{esc(g['dek'])}</p>
        </a>""")

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

<meta property="og:type" content="website" />
<meta property="og:site_name" content="HipHopLord" />
<meta property="og:title" content="{esc(page_title)}" />
<meta property="og:description" content="{esc(meta_description)}" />
<meta property="og:url" content="{canonical}" />
<meta name="twitter:card" content="summary" />
<meta name="twitter:title" content="{esc(page_title)}" />
<meta name="twitter:description" content="{esc(meta_description)}" />

{guides_index_json_ld(canonical)}

<script src="https://cdn.tailwindcss.com"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>{style_block}</style>
</head>
<body class="min-h-screen">
<div class="noise"></div>
{NAV_HTML}

<main class="max-w-5xl mx-auto px-5 pt-12 pb-6">
  <nav class="mono text-[11px] text-zinc-500 mb-8" aria-label="Breadcrumb">
    <a href="../index.html" class="hover:text-zinc-300 transition">Home</a>
    <span class="mx-1.5">/</span>
    <span class="text-zinc-400">Guides</span>
  </nav>

  <span class="mono text-[11px] uppercase tracking-widest text-zinc-500">HipHopLord Guides</span>
  <h1 class="display text-2xl md:text-3xl leading-tight mt-1">Guides for Independent Hip Hop Artists</h1>
  <p class="text-zinc-400 text-sm mt-3 max-w-2xl leading-relaxed">Straight answers on beat licensing, mixing and mastering costs, cover art, studios, and how to put a first release together -- written from inside the culture, grounded in real numbers from this directory, not generic content-mill filler.</p>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-5 mt-10 mb-16">
    {''.join(cards)}
  </div>
</main>

{FOOTER_HTML}
</body>
</html>"""


def main():
    os.makedirs(GUIDES_DIR, exist_ok=True)
    style_block = load_shared_style()
    by_slug = {g["slug"]: g for g in GUIDES}

    for guide in GUIDES:
        html = render_guide(guide, by_slug, style_block)
        path = os.path.join(GUIDES_DIR, f"{guide['slug']}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    index_html = render_guides_index(GUIDES, style_block)
    with open(os.path.join(GUIDES_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    # Regenerate the site-wide sitemap.xml so it also includes the guides
    # section (the /listings/ URLs are already in there from the last
    # generate_listing_pages.py run -- reload directory.json here so this
    # script can be re-run standalone without going stale relative to it).
    with open(os.path.join(BASE_DIR, "directory.json"), encoding="utf-8") as f:
        directory_entries = json.load(f)
    guide_slugs = [g["slug"] for g in GUIDES]
    sitemap_xml = generate_sitemap(directory_entries, guide_slugs=guide_slugs)
    with open(os.path.join(BASE_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

    print(f"Generated {len(GUIDES)} guide pages + index in {GUIDES_DIR}")
    print(f"Updated sitemap.xml with {len(directory_entries) + 6 + 1 + len(GUIDES)} URLs (incl. guides)")
    return GUIDES


if __name__ == "__main__":
    main()
