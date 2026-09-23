"""2일마다 새 프로그램 목록(data/current.json)을 만들고 이전 목록은 data/archive/에 남긴다.

사용법:
  python scripts/update.py           # 마지막 목록이 2일 이상 지났을 때만 갱신
  python scripts/update.py --force   # 바로 갱신
"""
import html
import json
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ARCHIVE = DATA / "archive"
CURRENT = DATA / "current.json"
STATE = DATA / "state.json"
INTERVAL_DAYS = 2
KST = timezone(timedelta(hours=9))

HEADERS = {"User-Agent": "OnAirEnglish/1.0 (English-learning web app; GitHub Actions)"}
VOA = "https://learningenglish.voanews.com"

# VOA Learning English RSS 피드 (2025년 봄 이후 새 글이 없어서 과거 글을 돌려 가며 사용)
VOA_TEXT_FEEDS = {
    "AS IT IS": "zkm-ql-vomx-tpej-rqi",
    "SCIENCE & TECHNOLOGY": "zmg_pl-vomx-tpeymtm",
    "HEALTH & LIFESTYLE": "zmmpql-vomx-tpey-_q",
    "ARTS & CULTURE": "zpyp_l-vomx-tpe_rym",
    "WORDS AND THEIR STORIES": "zmypyl-vomx-tpeyry_",
    "ASK A TEACHER": "zti_qvl-vomx-tpekgvqr",
    "AMERICAN STORIES": "zyg__l-vomx-tpetmty",
    "U.S. HISTORY": "zj_pvl-vomx-tpebb_v",
    "EDUCATION TIPS": "z_gjqyl-vomx-tpevmrov",
    "ALL ABOUT AMERICA": "zbmroml-vomx-tpeqboo_",
    "AMERICA'S PRESIDENTS": "zjypq_l-vomx-tpebryqy",
    "EDUCATION": "ztmp_l-vomx-tpek-__",
}
VOA_VIDEO_FEEDS = {
    "ENGLISH IN A MINUTE": "zjk-rl-vomx-tpebpqqo",
    "EVERYDAY GRAMMAR": "z_riqtl-vomx-tpevtmqr",
    "HOW TO PRONOUNCE": "zpivqol-vomx-tpe_guqi",
    "VOA60: WATCH & LEARN": "zyk-il-vomx-tpetpqqm",
}
NASA_SERIES = ["NASA Minute", "What's Up", "ScienceCasts", "NASA Science Live"]


def get(url, **kw):
    r = requests.get(url, headers=HEADERS, timeout=40, **kw)
    r.raise_for_status()
    return r


def clean(fragment):
    text = html.unescape(re.sub(r"<[^>]+>", "", fragment))
    return re.sub(r"\s+", " ", text).strip()


def rss_links(feed_id):
    xml = get(f"{VOA}/api/{feed_id}").text
    items = re.findall(r"<item>(.*?)</item>", xml, re.S)
    return [re.search(r"<link>(.*?)</link>", it).group(1).strip() for it in items]


def mark_gloss(paragraphs, words):
    """각 단어의 첫 등장 위치를 {word}로 감싼다. 찾지 못한 단어는 gloss에서 뺀다."""
    found = {}
    for word, meaning in words.items():
        pat = re.compile(r"(?<![\w{])(" + re.escape(word) + r")(?![\w}])", re.I)
        for i, p in enumerate(paragraphs):
            m = pat.search(p)
            if m:
                paragraphs[i] = p[: m.start()] + "{" + m.group(1) + "}" + p[m.end():]
                found[m.group(1).lower()] = meaning
                break
    return paragraphs, found


# ---------- VOA ----------
def voa_article(url):
    page = get(url).text
    title = clean(re.search(r"<title>(.*?)</title>", page, re.S).group(1))
    title = re.sub(r"\s*[|-]\s*VOA Learning English\s*$", "", title).strip()
    media = sorted(set(re.findall(r"https://[^\"\s&]+?\.(?:mp3|mp4)", page)))
    date = re.search(r'"datePublished":"(\d{4}-\d{2}-\d{2})', page)
    start = max(page.find('class="wsw"'), 0)
    wits = page.find("Words in This Story", start)
    body = page[start: wits if wits > 0 else len(page)] if start else ""
    paragraphs = []
    for raw in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S):
        t = clean(raw)
        if not t or "No media source" in t or set(t) <= set("_-— "):
            continue
        paragraphs.append(t)
    gloss = {}
    if wits > 0:
        block = page[wits: page.find("</div>", wits)]
        for raw in re.findall(r"<p[^>]*>(.*?)</p>", block, re.S):
            m = re.match(r"\s*<strong>(.*?)</strong>(.*)", raw, re.S)
            if not m:
                continue
            word = clean(m.group(1))
            meaning = clean(m.group(2))
            meaning = re.sub(r"^[\s\-–—:]*(\(?\s*(n|v|adj|adv|phrase|idiom|noun|verb|expression|phrasal verb)\.?\s*\)?\.?\s*)?", "", meaning, flags=re.I)
            if word and meaning and len(word) < 40:
                gloss[word] = meaning[:220]
    return {
        "url": url, "title": title, "paragraphs": paragraphs, "gloss": gloss,
        "mp3": pick_mp3(media), "mp4": pick_mp4(media),
        "date": date.group(1) if date else "",
    }


def pick_mp3(media):
    mp3 = [m for m in media if m.endswith(".mp3")]
    hq = [m for m in mp3 if m.endswith("_hq.mp3")]
    return (hq or mp3 or [None])[0]


def pick_mp4(media):
    mp4 = [m for m in media if m.endswith(".mp4")]
    for suffix in ("_480p.mp4", "_720p.mp4"):
        hit = [m for m in mp4 if m.endswith(suffix)]
        if hit:
            return hit[0]
    base = [m for m in mp4 if not re.search(r"_(\d+p|fullhd|hq)\.mp4$", m)]
    return (base or mp4 or [None])[0]


def voa_text(show, feed, used):
    for url in rss_links(feed):
        key = "voa:" + url
        if key in used:
            continue
        a = voa_article(url)
        if not a or len(a["paragraphs"]) < 4:
            used.add(key)
            continue
        paragraphs = a["paragraphs"][:14]
        paragraphs, gloss = mark_gloss(paragraphs, a["gloss"])
        used.add(key)
        return {
            "type": "text", "show": show, "title": a["title"], "paragraphs": paragraphs, "gloss": gloss,
            "source": url, "sourceName": "VOA Learning English",
            "credit": f"Voice of America — VOA Learning English, {a['date']} · Public Domain",
        }
    return None


def voa_media(show, feed, kind, used):
    for url in rss_links(feed):
        key = "voa:" + url
        if key in used:
            continue
        a = voa_article(url)
        used.add(key)
        src = a and (a["mp4"] if kind == "video" else a["mp3"])
        if not src:
            continue
        return {
            "type": "video", "media": kind, "show": show, "title": a["title"], "src": src,
            "source": url, "sourceName": "VOA Learning English",
            "credit": f"Voice of America — VOA Learning English {kind}, {a['date']} · Public Domain",
        }
    return None


# ---------- The Conversation ----------
def conversation(used):
    feed = get("https://theconversation.com/global/articles.atom").text
    for entry in re.findall(r"<entry>(.*?)</entry>", feed, re.S):
        link = re.search(r'<link[^>]*rel="alternate"[^>]*href="([^"]+)"', entry) or re.search(r'<link[^>]*href="([^"]+)"', entry)
        url = link.group(1)
        key = "tc:" + url
        if key in used:
            continue
        used.add(key)
        content = re.search(r"<content[^>]*>(.*?)</content>", entry, re.S)
        if not content:
            continue
        body = html.unescape(content.group(1))
        paragraphs = [clean(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S)]
        paragraphs = [p for p in paragraphs if p]
        if len(paragraphs) < 4:
            continue
        title = clean(re.search(r"<title[^>]*>(.*?)</title>", entry, re.S).group(1))
        author = clean(re.search(r"<name>(.*?)</name>", entry, re.S).group(1)) if "<name>" in entry else "The Conversation"
        return {
            "type": "text", "show": "THE CONVERSATION", "title": title, "paragraphs": paragraphs, "gloss": {},
            "source": url, "sourceName": "The Conversation",
            "credit": f"{author} — republished from The Conversation under CC BY-ND 4.0",
        }
    return None


# ---------- NASA ----------
def nasa(used):
    year = datetime.now(KST).year
    items = []
    for q in NASA_SERIES:
        try:
            res = get("https://images-api.nasa.gov/search",
                      params={"q": q, "media_type": "video", "year_start": str(year - 1)}).json()
            items += res["collection"]["items"]
        except Exception:
            pass
    items.sort(key=lambda i: i["data"][0].get("date_created", ""), reverse=True)
    for it in items:
        d = it["data"][0]
        key = "nasa:" + d["nasa_id"]
        if key in used:
            continue
        used.add(key)
        files = [x["href"] for x in get(f"https://images-api.nasa.gov/asset/{d['nasa_id']}").json()["collection"]["items"]]
        mp4 = next((f for tag in ("~medium.mp4", "~mobile.mp4", "~small.mp4", "~orig.mp4") for f in files if f.endswith(tag)), None)
        if not mp4:
            continue
        return {
            "type": "video", "media": "video", "show": "NASA", "title": d["title"].strip(),
            "src": mp4.replace("http://", "https://"),
            "source": f"https://images.nasa.gov/details/{d['nasa_id']}", "sourceName": "NASA Image and Video Library",
            "credit": f"NASA{(' / ' + d['center']) if d.get('center') else ''} — {d.get('date_created', '')[:10]} · Public Domain",
        }
    return None


# ---------- LibriVox ----------
def librivox(used):
    for _ in range(8):
        try:
            books = get("https://librivox.org/api/feed/audiobooks",
                        params={"format": "json", "limit": 5, "offset": random.randint(0, 18000), "extended": 1}).json().get("books", [])
        except Exception:
            continue
        for b in books:
            if b.get("language") != "English":
                continue
            for s in b.get("sections", []):
                url = (s.get("listen_url") or "").replace("http://", "https://")
                key = "lv:" + url
                if not url or key in used or not (180 <= int(s.get("playtime") or 0) <= 900):
                    continue
                used.add(key)
                authors = ", ".join(f"{a['first_name']} {a['last_name']}".strip() for a in b.get("authors", [])) or "Unknown"
                return {
                    "type": "video", "media": "audio", "show": "LIBRIVOX AUDIOBOOK",
                    "title": f"{clean(b['title'])}: {clean(s.get('title') or 'Section ' + str(s.get('section_number')))}",
                    "src": url, "source": b.get("url_librivox") or b.get("url_iarchive"),
                    "sourceName": "LibriVox",
                    "credit": f"{authors} — LibriVox volunteer recording · Public Domain",
                }
    return None


# ---------- Wikimedia Commons: Spoken Wikipedia ----------
def spoken_wikipedia(used):
    api = "https://commons.wikimedia.org/w/api.php"
    params = {"action": "query", "format": "json", "generator": "categorymembers",
              "gcmtitle": "Category:Spoken English Wikipedia", "gcmtype": "file", "gcmlimit": 50,
              "gcmsort": "timestamp", "gcmdir": "desc",
              "prop": "videoinfo", "viprop": "url|derivatives|extmetadata|size"}
    pages = list(get(api, params=params).json().get("query", {}).get("pages", {}).values())
    random.shuffle(pages)
    for p in pages:
        key = "cm:" + p["title"]
        info = (p.get("videoinfo") or [{}])[0]
        dur = float(info.get("duration") or 0)
        if key in used or not (60 <= dur <= 1200):
            continue
        mp3 = next((d["src"] for d in info.get("derivatives", []) if d.get("type", "").startswith("audio/mpeg")), None)
        if not mp3:
            continue
        used.add(key)
        meta = info.get("extmetadata", {})
        name = re.sub(r"^File:(En[-_ ])?", "", p["title"])
        name = re.sub(r"(-article)?\.(ogg|oga|flac|wav|mp3)$", "", name, flags=re.I).replace("_", " ")
        artist = clean(meta.get("Artist", {}).get("value", "")) or "Wikipedia volunteer"
        lic = clean(meta.get("LicenseShortName", {}).get("value", "")) or "CC BY-SA"
        return {
            "type": "video", "media": "audio", "show": "SPOKEN WIKIPEDIA", "title": name,
            "src": mp3, "source": info.get("descriptionurl"), "sourceName": "Wikimedia Commons",
            "credit": f"Read by {artist} — Spoken English Wikipedia · {lic}",
        }
    return None


# ---------- 조립 ----------
def build(used, rng):
    programs = []
    text_shows = list(VOA_TEXT_FEEDS.items())
    rng.shuffle(text_shows)
    for show, feed in text_shows:
        if len(programs) == 3:
            break
        try:
            p = voa_text(show, feed, used)
            if p:
                programs.append(p)
        except Exception as e:
            print("VOA text failed:", show, e)

    for fn in (conversation,):
        try:
            p = fn(used)
            if p:
                programs.append(p)
        except Exception as e:
            print("Conversation failed:", e)

    listening = []
    for show, feed in reversed(text_shows):
        try:
            p = voa_media(show, feed, "audio", used)
            if p:
                listening.append(p)
                break
        except Exception as e:
            print("VOA audio failed:", show, e)
    video_shows = list(VOA_VIDEO_FEEDS.items())
    rng.shuffle(video_shows)
    for show, feed in video_shows:
        try:
            p = voa_media(show, feed, "video", used)
            if p:
                listening.append(p)
                break
        except Exception as e:
            print("VOA video failed:", show, e)
    for fn in (nasa, librivox, spoken_wikipedia):
        try:
            p = fn(used)
            if p:
                listening.append(p)
        except Exception as e:
            print(fn.__name__, "failed:", e)

    programs += listening
    n = len(programs)
    for i, p in enumerate(programs):
        p["id"] = i + 1
        p["available"] = True
        p["tune"] = f"{round(8 + 84 * i / max(1, n - 1))}%"
    return programs


def load(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main():
    force = "--force" in sys.argv
    now = datetime.now(KST)
    today = now.strftime("%Y-%m-%d")
    current = load(CURRENT, None)
    if current and not force:
        last = datetime.strptime(current["date"], "%Y-%m-%d").date()
        if (now.date() - last).days < INTERVAL_DAYS:
            print(f"skip: last edition {current['date']}, next on {last + timedelta(days=INTERVAL_DAYS)}")
            return
    state = load(STATE, {"used": []})
    used = set(state["used"])
    programs = build(used, random.Random(today))
    if len(programs) < 6:
        sys.exit(f"too few programs ({len(programs)}); keeping previous edition")

    index = load(ARCHIVE / "index.json", {"editions": []})
    ids = {e["id"] for e in index["editions"]}
    eid, k = today, 2
    while eid in ids:
        eid, k = f"{today}-{k}", k + 1
    edition = {"id": eid, "date": today, "generated": now.isoformat(timespec="seconds"), "programs": programs}

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    save(ARCHIVE / f"{eid}.json", edition)
    index["editions"].insert(0, {"id": eid, "date": today, "titles": [p["title"] for p in programs]})
    save(ARCHIVE / "index.json", index)
    save(CURRENT, edition)
    save(STATE, {"used": sorted(used)})
    print(f"new edition {eid}: {len(programs)} programs")
    for p in programs:
        print(f"  {p['id']}. [{p.get('media', 'text')}] {p['show']} — {p['title']}")


if __name__ == "__main__":
    main()
