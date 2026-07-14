# -*- coding: utf-8 -*-
"""Beyond the Song — generates /songs/<slug>/ pages: official lyrics + the
scripture each song is built on (full text, World English Bible, public
domain, fetched from bible-api.com and cached) + the Bible story to read
when you're in that prayer/emotion.

Run: python build_songs.py   (rebuilds all pages + sitemap.xml)
Lyrics source: the I-Asked-God-Reels official lyrics store.
"""
import os, json, re, time, urllib.request, urllib.parse

SITE = os.path.dirname(os.path.abspath(__file__))
LYRICS = r"C:\Users\felic\Desktop\I-Asked-God-Reels\Lyrics\official"
CACHE = os.path.join(SITE, "verses_cache.json")
BASE_URL = "https://unlikelydisciples.com"
ALBUM_URL = "https://open.spotify.com/album/1CTKORudh8Wxa9dFV72d2O"
AMAZON_URL = "https://music.amazon.com/albums/B0H8MG1KD4"
APPLE_URL = "https://music.apple.com/us/album/i-asked-god/6790194050"
APPLE_ARTIST = "https://music.apple.com/us/artist/unlikely-disciples/6786909566"
AMEN_ID = "57dtdUFcIehfMEkkb5LBPz"   # Here I Am, Send Me (Amen) — track 21
SPOTIFY = {  # slug -> Spotify track id (pulled from the album embed 7/13)
 "the-room": "5e92YkuVPtkmHjGqNHOBUS", "the-silence": "4z8wRRfwOus0Q180FmYfTA",
 "the-doubt": "6Se7nYdnZHjAydmlA7Eu5r", "the-fear": "3tSs55JT4nCz3sIl9E0knv",
 "the-comparison": "5F13oF23ZexsVDvgt25ruV", "the-shame": "6Uq7VQ1iiJm9yLOQN38rDC",
 "the-lonely": "6eFcG4yz7bI5eLB8F2r3TX", "the-scars": "1Xr3pjl1uZP7bWi1O6C5Uc",
 "the-injustice": "3auo0E5P4xnT6YTjSYmtYe", "the-weary": "0MoKpONArpGLEyrptd1kUZ",
 "the-burden": "3l2cMcf4fQ4hQBQTsktewr", "the-wait": "1tyu6W3urqjLIduj3fXKsY",
 "the-detour": "1xY8l5txlu1TITiGS6o3pE", "the-lie": "3kgp2EH3G0nLqx4rxlqgss",
 "the-provision": "11EoukugfrVpndDW2TsoVT", "the-grudge": "3Y5OQqyydOAhWqs6WRBSwt",
 "the-way": "5AMmR3eBaSS8XBBnBFYHFs", "the-victory": "6jqVKHV16YcQTQfPsrOKLW",
 "here-i-am-send-me": "4YT9rzAp4cg3YLjUcQpPQh", "the-battle": "1hJF5EPr49fzVsUs5ZoUTf",
}

def sp_embed(track_id, title):
    return (f'<iframe style="border-radius:12px" '
            f'src="https://open.spotify.com/embed/track/{track_id}?theme=0" '
            f'width="100%" height="152" frameborder="0" '
            f'allow="clipboard-write; encrypted-media; fullscreen; picture-in-picture" '
            f'loading="lazy" title="Play {title} on Spotify"></iframe>')

#            slug, track#, title, lyrics tag, emotion line
SONGS = [
 dict(slug="the-room", num=1, title="The Room", tag="room",
      emotion="For when you need somewhere to fall apart.",
      verses=["Matthew 6:6", "Psalm 34:18", "Psalm 147:3"],
      story=("The woman who came undone in the room", "Luke 7:36-50",
             "She walked into a room full of people who knew her worst chapter, "
             "knelt at Jesus' feet, and spilled it all — the tears, the perfume, "
             "the past. He didn't flinch. He didn't look away. He called what she "
             "brought Him precious, and He sent her out whole.")),
 dict(slug="the-silence", num=2, title="The Silence", tag="silence",
      emotion="For when heaven feels quiet.",
      verses=["Psalm 13:1-2", "Romans 8:28", "Habakkuk 2:3"],
      story=("The Saturday God went quiet", "Matthew 27:57-66 & 28:1-8",
             "Between the cross and the empty tomb there was a whole day of "
             "silence. It looked like the end. It looked like love had lost. But "
             "that silence was the pause right before the stone rolled off — God "
             "was working the entire time.")),
 dict(slug="the-doubt", num=3, title="The Doubt", tag="doubt",
      emotion="For the questions you're afraid to say out loud.",
      verses=["John 20:27-29", "Revelation 21:3-4"],
      story=("Thomas, the one who needed to see", "John 20:24-29",
             "Thomas didn't get a lecture for his doubt. Jesus walked through a "
             "locked door, held out His scarred hands, and met the question "
             "head-on. Honest doubt brought to Jesus doesn't get you thrown out — "
             "it gets you closer.")),
 dict(slug="the-fear", num=4, title="The Fear", tag="fear",
      emotion="For the three a.m. what-ifs.",
      verses=["1 John 4:18", "1 John 4:4", "Psalm 23:4"],
      story=("The storm that obeyed", "Mark 4:35-41",
             "The disciples were seasoned fishermen, and the storm still "
             "terrified them. Jesus was asleep in the stern — not because He "
             "didn't care, but because He knew who was in the boat. One word "
             "from Him and the sea went still. The same voice is in your boat.")),
 dict(slug="the-comparison", num=5, title="The Comparison", tag="comparison",
      emotion="For when everyone else's life looks perfect.",
      verses=["Psalm 139:14", "Galatians 6:4-5"],
      story=("Peter, John, and the question that wasn't his to ask", "John 21:20-22",
             "Fresh off his restoration, Peter looked over his shoulder at John "
             "and asked, \"Lord, what about him?\" Jesus' answer is the whole cure "
             "for comparison: \"What is that to you? You follow Me.\" Your race "
             "has your name on it.")),
 dict(slug="the-shame", num=6, title="The Shame", tag="shame",
      emotion="For the name you've been answering to in the dark.",
      verses=["Isaiah 1:18", "Romans 8:1", "Psalm 34:5"],
      story=("The woman they dragged into the light", "John 8:2-11",
             "They threw her worst moment into the middle of a crowd and reached "
             "for stones. Jesus knelt, wrote in the dust, and emptied the whole "
             "courtroom without raising His voice. Then the only One with the "
             "right to condemn her chose not to. \"Go, and sin no more\" — spoken "
             "to a lifted head, not a hidden face.")),
 dict(slug="the-lonely", num=7, title="The Lonely", tag="lonely",
      emotion="For when you feel invisible.",
      verses=["Psalm 68:5-6", "Hebrews 13:5"],
      story=("Hagar and the God who sees", "Genesis 16:1-13",
             "Used, dismissed, and running through a desert nobody would cross "
             "for her — Hagar is the first person in the Bible to give God a "
             "name. She called Him El Roi: \"the God who sees me.\" Not the God "
             "who sees the crowd. The God who found one invisible woman by a "
             "spring and knew her whole story.")),
 dict(slug="the-scars", num=8, title="The Scars", tag="scars",
      emotion="For the parts you've been hiding.",
      verses=["Genesis 50:20", "2 Corinthians 12:9", "Revelation 12:11"],
      story=("Joseph, and the wound that fed nations", "Genesis 50:15-21",
             "Betrayed by his brothers, sold, slandered, forgotten in a prison — "
             "and every one of those scars became the road to the throne room "
             "where he saved the very family that broke him. \"You intended to "
             "harm me, but God intended it for good.\" Even the risen Jesus kept "
             "His scars — they're proof, not shame.")),
 dict(slug="the-injustice", num=9, title="The Injustice", tag="injustice",
      emotion="For when the guilty walk away.",
      verses=["Romans 12:19", "Psalm 73:16-17", "Ephesians 6:12"],
      story=("David, Saul, and the sword he didn't swing", "1 Samuel 24:1-12",
             "David had his enemy cornered in a cave — the man hunting him "
             "unjustly, asleep and defenseless. One swing and it would be over. "
             "He cut the robe instead of the throat and said, \"May the LORD "
             "judge between me and you.\" Taking your hands off the scales isn't "
             "weakness. It's trust.")),
 dict(slug="the-weary", num=10, title="The Weary", tag="weary",
      emotion="For when you're running on empty.",
      verses=["Matthew 11:28-30", "Isaiah 40:29-31"],
      story=("Elijah under the broom tree", "1 Kings 19:3-8",
             "Right after his greatest victory, Elijah hit the wall — exhausted, "
             "afraid, asking God to just let it end. God's answer wasn't a "
             "rebuke. It was sleep, fresh bread, and a gentle \"the journey is "
             "too much for you.\" Sometimes the holiest thing you can do is rest "
             "and let Him feed you.")),
 dict(slug="the-burden", num=11, title="The Burden", tag="burden",
      emotion="For the weight you've carried alone.",
      verses=["Psalm 55:22", "1 Peter 5:7", "Philippians 4:6-7"],
      story=("The man carried by four friends", "Mark 2:1-12",
             "He couldn't carry himself — so four friends tore a hole in a roof "
             "to lower him to Jesus. He came down on a mat and walked out "
             "carrying it. The weight you can't lift was never meant to be "
             "lifted alone.")),
 dict(slug="the-wait", num=12, title="The Wait", tag="wait",
      emotion="For the door that hasn't opened.",
      verses=["Habakkuk 2:3", "Psalm 27:14", "Ecclesiastes 3:11"],
      story=("Abraham, Sarah, and the promise that took 25 years", "Genesis 21:1-7",
             "God promised Abraham a son — and then came decades of silence, "
             "wrinkles, and math that didn't work. But the scripture says Sarah "
             "conceived \"at the very time God had promised.\" Not one day early. "
             "Not one day late. The wait wasn't the promise dying; it was the "
             "promise ripening.")),
 dict(slug="the-detour", num=13, title="The Detour", tag="detour",
      emotion="For the road you never would have drawn.",
      verses=["Exodus 13:17-18", "Proverbs 16:9", "Proverbs 3:5-6"],
      story=("The long way out of Egypt", "Exodus 13:17-22",
             "When Pharaoh finally let Israel go, there was a short road to the "
             "Promised Land — and God deliberately didn't take it. Scripture "
             "says He led them the long way around, by a pillar of cloud and "
             "fire, because the short road would have broken them. Some detours "
             "aren't delays. They're protection with a route.")),
 dict(slug="the-lie", num=14, title="The Lie", tag="lie",
      emotion="For what the mirror keeps telling you.",
      verses=["Psalm 139:13-14", "Isaiah 43:1", "Zephaniah 3:17"],
      story=("Gideon, the 'mighty warrior' hiding in a winepress", "Judges 6:11-16",
             "Gideon was threshing wheat in a hole, hiding from his enemies, "
             "when the angel of the LORD called him \"mighty warrior.\" It sounded "
             "like a joke — he was the least of the least, and said so. God "
             "wasn't describing what Gideon saw in the mirror. He was naming who "
             "He'd made. He does the same to you.")),
 dict(slug="the-provision", num=15, title="The Provision", tag="provision",
      emotion="For the kitchen-table math.",
      verses=["Matthew 6:26", "Matthew 6:31-33", "Philippians 4:19"],
      story=("The widow's jar that wouldn't run dry", "1 Kings 17:8-16",
             "A widow down to her last handful of flour was gathering sticks to "
             "cook a final meal for her son when God sent a prophet to her door. "
             "She gave from her not-enough — and the jar never emptied again. "
             "God's math starts where yours runs out.")),
 dict(slug="the-grudge", num=16, title="The Grudge", tag="grudge",
      emotion="For the apology that never came.",
      verses=["Colossians 3:13", "Ephesians 4:32", "Luke 23:34"],
      story=("The servant who was forgiven millions", "Matthew 18:21-35",
             "Jesus told this one when Peter asked how many times he had to "
             "forgive. A servant forgiven a debt he could never repay walked "
             "out and choked a man over pocket change. The point lands hard: "
             "the mercy you were handed first is the mercy you can hand to "
             "them. From the cross, He went first.")),
 dict(slug="the-way", num=17, title="The Way", tag="way",
      emotion="For the one who made it out.",
      verses=["2 Corinthians 1:3-4", "Psalm 40:1-3"],
      story=("The man sent back to his own town", "Mark 5:18-20",
             "The man Jesus freed begged to leave with Him. Jesus said no — "
             "\"Go home to your own people and tell them how much the Lord has "
             "done for you.\" The dark you survived is somebody's map out. "
             "You're not just rescued. You're sent back in.")),
 dict(slug="the-victory", num=18, title="The Victory", tag="victory",
      emotion="For when you need to remember it's already won.",
      verses=["1 Corinthians 15:57", "Colossians 2:15", "Romans 8:37"],
      story=("The empty tomb", "John 19:28-30 & 20:1-18",
             "\"It is finished\" wasn't a sigh of defeat — it was a verdict. And "
             "three days later an empty tomb signed it. Every enemy you're "
             "facing is a beaten one still trying to sell you fear. You don't "
             "fight for victory. You fight from it.")),
 dict(slug="here-i-am-send-me", num=19, title="Here I Am, Send Me", tag="hereiam",
      emotion="For when you feel unqualified.",
      verses=["Isaiah 6:8", "1 Corinthians 1:26-29", "Exodus 4:10-12"],
      story=("Isaiah, the man with unclean lips", "Isaiah 6:1-8",
             "Isaiah's first reaction to seeing God's glory wasn't volunteering "
             "— it was \"woe is me, I'm ruined.\" Then the coal touched his lips, "
             "guilt taken, and the same mouth that said \"I'm unclean\" said "
             "\"here am I — send me.\" God has never once called the equipped. "
             "He equips the called."),
      note="Track 21 closes the album with the (Amen) reprise of this song."),
 dict(slug="the-battle", num=20, title="The Battle", tag="battle",
      emotion="For the fight that isn't yours to win.",
      verses=["2 Chronicles 20:15", "2 Chronicles 20:21-22", "Exodus 14:14"],
      story=("Jehoshaphat's choir that marched in front of the army", "2 Chronicles 20:1-30",
             "Three armies were coming and Judah had no chance. God's battle "
             "plan: \"the battle is not yours, but God's — stand firm and see.\" "
             "So Jehoshaphat put the singers in FRONT of the soldiers, and as "
             "the praise went up, the enemy fell. They never drew a sword. "
             "That's what lifting your hands instead of clenching fists does.")),
]

def fetch_verse(ref, cache):
    if ref in cache: return cache[ref]
    url = "https://bible-api.com/" + urllib.parse.quote(ref) + "?translation=web"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8"))
            txt = re.sub(r"\s+", " ", data["text"]).strip()
            cache[ref] = {"ref": data.get("reference", ref), "text": txt}
            time.sleep(0.4)
            return cache[ref]
        except Exception as e:
            if attempt == 2:
                print(f"  ! verse fetch failed {ref}: {e}")
                cache[ref] = {"ref": ref, "text": ""}
                return cache[ref]
            time.sleep(2)

def load_lyrics(tag):
    path = os.path.join(LYRICS, f"{tag}.txt")
    raw = [ln.rstrip() for ln in open(path, encoding="utf-8", errors="replace")]
    # drop title header line(s) at top
    while raw and not raw[0].strip(): raw.pop(0)
    if raw: raw.pop(0)
    stanzas, cur = [], []
    for ln in raw:
        if ln.strip(): cur.append(re.sub(r'(\w)"(\w)', r'\1 "\2', ln.strip()))
        elif cur: stanzas.append(cur); cur = []
    if cur: stanzas.append(cur)
    return stanzas

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def gateway(ref):
    return ("https://www.biblegateway.com/passage/?search=" +
            urllib.parse.quote(ref) + "&version=WEB")

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Lyrics &amp; Scripture | Unlikely Disciples</title>
<meta name="description" content="{title} by Unlikely Disciples, from the album I Asked God — full lyrics, the scripture the song is built on, and the Bible story to read {emotion_lc}">
<link rel="canonical" href="{base}/songs/{slug}/">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/site.css">
<meta property="og:type" content="music.song">
<meta property="og:site_name" content="Unlikely Disciples">
<meta property="og:title" content="{title} — Unlikely Disciples | Lyrics &amp; Scripture">
<meta property="og:description" content="{emotion} Full lyrics, scripture, and the story behind the song.">
<meta property="og:url" content="{base}/songs/{slug}/">
<meta property="og:image" content="{base}/assets/ud-og-1200x630.jpg">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{jsonld}
</script>
</head>
<body>

<nav aria-label="Site">
  <a href="/"><img src="/assets/apple-touch-icon.png" alt="Unlikely Disciples logo" width="38" height="38"></a>
  <a class="name" href="/">UNLIKELY&nbsp;DISCIPLES</a>
  <span class="links">
    <a href="/#music">Music</a>
    <a href="/songs/">Beyond the Song</a>
    <a href="/#about">About</a>
    <a href="/#follow">Follow</a>
  </span>
</nav>

<header class="song-head">
  <div class="wrap">
    <p class="kicker">I Asked God · Track {num:02d} · Beyond the Song</p>
    <h1>{title}</h1>
    <div class="rule"></div>
    <p class="emotion">{emotion}</p>
  </div>
</header>

<main class="wrap song-grid">
  <section class="lyrics-col">
    <h2>The Lyrics</h2>
    {lyrics_html}
    {note_html}
  </section>

  <aside class="scripture-col">
    <section>
      <h2>The Scripture</h2>
      <p class="lede">The verses this song is built on — sit with them slowly.</p>
      {verses_html}
    </section>
    <section class="story">
      <h2>The Story</h2>
      <p class="story-title">{story_title}</p>
      <p class="story-ref"><a href="{story_link}">Read: {story_ref} →</a></p>
      <p>{story_why}</p>
    </section>
    <section class="listen">
      <h2>Listen</h2>
      {embed_html}
      <p><a class="btn solid" href="https://open.spotify.com/track/{spotify_id}">Open in Spotify</a>
      <a class="btn" href="{apple_url}">Apple Music</a>
      <a class="btn" href="{amazon_url}">Amazon Music</a></p>
    </section>
  </aside>
</main>

<nav class="prevnext wrap" aria-label="Album navigation">
  {prev_html}
  <a class="mid" href="/songs/">All songs</a>
  {next_html}
</nav>

<footer>
  <p class="fname">Unlikely Disciples</p>
  <p>© 2026 Unlikely Disciples · unlikelydisciples.com · Welcome, unlikely disciple.</p>
  <p class="scripture-credit">Scripture quotations are from the World English Bible (public domain).</p>
</footer>

</body>
</html>
"""

def jsonld(s):
    return json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "MusicRecording", "name": s["title"],
             "url": f"{BASE_URL}/songs/{s['slug']}/",
             "sameAs": "https://open.spotify.com/track/" + SPOTIFY[s["slug"]],
             "byArtist": {"@type": "MusicGroup", "name": "Unlikely Disciples",
                          "url": BASE_URL + "/"},
             "inAlbum": {"@type": "MusicAlbum", "name": "I Asked God",
                         "url": ALBUM_URL, "sameAs": [APPLE_URL, AMAZON_URL],
                         "byArtist": {"@type": "MusicGroup", "name": "Unlikely Disciples"}},
             "position": s["num"]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Unlikely Disciples",
                 "item": BASE_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": "I Asked God",
                 "item": BASE_URL + "/#music"},
                {"@type": "ListItem", "position": 3, "name": s["title"]}]}
        ]}, indent=1)

INDEX = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Beyond the Song — Lyrics, Scripture &amp; Stories | Unlikely Disciples</title>
<meta name="description" content="Every song on I Asked God by Unlikely Disciples — full lyrics, the scripture each song is built on, and the Bible story to read when you're in that prayer.">
<link rel="canonical" href="{base}/songs/">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/site.css">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Unlikely Disciples">
<meta property="og:title" content="Beyond the Song — Unlikely Disciples">
<meta property="og:description" content="Lyrics, scripture, and the story behind every song on I Asked God.">
<meta property="og:url" content="{base}/songs/">
<meta property="og:image" content="{base}/assets/ud-og-1200x630.jpg">
<meta name="twitter:card" content="summary_large_image">
</head>
<body>

<nav aria-label="Site">
  <a href="/"><img src="/assets/apple-touch-icon.png" alt="Unlikely Disciples logo" width="38" height="38"></a>
  <a class="name" href="/">UNLIKELY&nbsp;DISCIPLES</a>
  <span class="links">
    <a href="/#music">Music</a>
    <a href="/songs/">Beyond the Song</a>
    <a href="/#about">About</a>
    <a href="/#follow">Follow</a>
  </span>
</nav>

<header class="song-head">
  <div class="wrap">
    <p class="kicker">I Asked God · The Album</p>
    <h1>Beyond the Song</h1>
    <div class="rule"></div>
    <p class="emotion">Every track started as a prayer. Find the one you're praying —
       the lyrics, the scripture it's built on, and the story to sit with.</p>
  </div>
</header>

<main class="wrap">
  <div class="song-cards">
{cards}
  </div>
</main>

<footer>
  <p class="fname">Unlikely Disciples</p>
  <p>© 2026 Unlikely Disciples · unlikelydisciples.com · Welcome, unlikely disciple.</p>
</footer>

</body>
</html>
"""

def build_index():
    cards = []
    for s in SONGS:
        cards.append(
            f'    <a class="song-card" href="/songs/{s["slug"]}/">'
            f'<span class="num">{s["num"]:02d}</span>'
            f'<span class="t">{esc(s["title"])}</span>'
            f'<span class="e">{esc(s["emotion"])}</span></a>')
    with open(os.path.join(SITE, "songs", "index.html"), "w", encoding="utf-8") as f:
        f.write(INDEX.format(base=BASE_URL, cards="\n".join(cards)))
    print("built songs/ index")

def build():
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    for i, s in enumerate(SONGS):
        stanzas = load_lyrics(s["tag"])
        lyr = "\n".join("<p class='stanza'>" +
                        "<br>\n".join(esc(l) for l in st) + "</p>"
                        for st in stanzas)
        verses = []
        for ref in s["verses"]:
            v = fetch_verse(ref, cache)
            body = esc(v["text"]) if v["text"] else \
                   f"<a href='{gateway(ref)}'>Read {esc(ref)} →</a>"
            verses.append(f"<blockquote class='verse'><p>{body}</p>"
                          f"<cite><a href='{gateway(ref)}'>{esc(v['ref'])}</a> (WEB)</cite></blockquote>")
        prev_s = SONGS[i-1] if i > 0 else None
        next_s = SONGS[i+1] if i+1 < len(SONGS) else None
        prev_html = (f"<a class='side' href='/songs/{prev_s['slug']}/'>← {esc(prev_s['title'])}</a>"
                     if prev_s else "<span class='side'></span>")
        next_html = (f"<a class='side' href='/songs/{next_s['slug']}/'>{esc(next_s['title'])} →</a>"
                     if next_s else "<span class='side'></span>")
        note_html = (f"<p class='tracknote'>{esc(s['note'])}</p>" if s.get("note") else "")
        st_title, st_ref, st_why = s["story"]
        embed = sp_embed(SPOTIFY[s["slug"]], esc(s["title"]))
        if s["slug"] == "here-i-am-send-me":
            embed += "\n      <p class='reprise-label'>The (Amen) reprise — track 21:</p>\n      " + \
                     sp_embed(AMEN_ID, "Here I Am, Send Me (Amen)")
        html = PAGE.format(
            embed_html=embed, spotify_id=SPOTIFY[s["slug"]], album_url=ALBUM_URL,
            amazon_url=AMAZON_URL, apple_url=APPLE_URL,
            base=BASE_URL, slug=s["slug"], num=s["num"], title=esc(s["title"]),
            emotion=esc(s["emotion"]), emotion_lc=esc(s["emotion"][0].lower() + s["emotion"][1:]),
            jsonld=jsonld(s), lyrics_html=lyr, verses_html="\n".join(verses),
            note_html=note_html, story_title=esc(st_title), story_ref=esc(st_ref),
            story_link=gateway(st_ref.replace(" & ", "; ")), story_why=esc(st_why),
            prev_html=prev_html, next_html=next_html)
        out = os.path.join(SITE, "songs", s["slug"])
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print(f"built songs/{s['slug']}/  ({len(stanzas)} stanzas, {len(s['verses'])} passages)")
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), indent=0)
    build_index()
    # sitemap
    today = "2026-07-13"
    urls = [f"  <url><loc>{BASE_URL}/</loc><lastmod>{today}</lastmod>"
            "<changefreq>weekly</changefreq><priority>1.0</priority></url>",
            f"  <url><loc>{BASE_URL}/songs/</loc><lastmod>{today}</lastmod>"
            "<priority>0.9</priority></url>"]
    urls += [f"  <url><loc>{BASE_URL}/songs/{s['slug']}/</loc>"
             f"<lastmod>{today}</lastmod><priority>0.8</priority></url>"
             for s in SONGS]
    with open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + "\n".join(urls) + "\n</urlset>\n")
    print(f"sitemap.xml -> {2 + len(SONGS)} urls")

if __name__ == "__main__":
    build()
