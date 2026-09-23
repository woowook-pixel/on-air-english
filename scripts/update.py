"""2일마다 새 프로그램 목록(data/current.json)을 만들고 이전 목록은 data/archive/에 남긴다.

- 뉴스 듣기: BBC·NPR 팟캐스트의 최신 편 (원래 서버의 파일을 그대로 재생)
- 헤드라인: BBC·NPR RSS의 제목·요약·썸네일 (본문은 원문 사이트에서 읽음)

사용법:
  python scripts/update.py           # 마지막 목록이 2일 이상 지났을 때만 갱신
  python scripts/update.py --force   # 바로 갱신
"""
import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
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

# (보여줄 이름, 출처, RSS 주소)
PODCASTS = [
    ("BBC GLOBAL NEWS PODCAST", "BBC", "https://podcasts.files.bbci.co.uk/p02nq0gn.rss"),
    ("NPR NEWS NOW", "NPR", "https://feeds.npr.org/500005/podcast.xml"),
    ("NPR UP FIRST", "NPR", "https://feeds.npr.org/510318/podcast.xml"),
    ("BBC 6 MINUTE ENGLISH", "BBC", "https://podcasts.files.bbci.co.uk/p02pc9tn.rss"),
    ("NPR SHORT WAVE", "NPR", "https://feeds.npr.org/510351/podcast.xml"),
]
# (보여줄 이름, 출처, RSS 주소, 가져올 개수)
HEADLINES = [
    ("BBC WORLD", "BBC News", "https://feeds.bbci.co.uk/news/world/rss.xml", 2),
    ("BBC SCIENCE", "BBC News", "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", 1),
    ("BBC TECHNOLOGY", "BBC News", "https://feeds.bbci.co.uk/news/technology/rss.xml", 1),
    ("NPR NEWS", "NPR", "https://feeds.npr.org/1001/rss.xml", 1),
    ("NPR WORLD", "NPR", "https://feeds.npr.org/1004/rss.xml", 1),
]


def get(url, **kw):
    r = requests.get(url, headers=HEADERS, timeout=40, **kw)
    r.raise_for_status()
    return r


def clean(fragment):
    text = html.unescape(re.sub(r"<[^>]+>", "", fragment or ""))
    return re.sub(r"\s+", " ", text).strip()


def tag(xml, name):
    m = re.search(rf"<{name}(?:\s[^>]*)?>(.*?)</{name}>", xml, re.S)
    return m.group(1).replace("<![CDATA[", "").replace("]]>", "").strip() if m else ""


def attr(xml, name, attribute):
    m = re.search(rf'<{name}\b[^>]*\b{attribute}="([^"]+)"', xml)
    return html.unescape(m.group(1)) if m else ""


def feed(url):
    xml = get(url).text
    channel = xml.split("<item>")[0]
    return channel, re.findall(r"<item>(.*?)</item>", xml, re.S)


def iso_date(value):
    try:
        return parsedate_to_datetime(value).astimezone(KST).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""


def seconds(value):
    parts = [int(x) for x in re.findall(r"\d+", value or "")]
    if not parts:
        return None
    total = 0
    for x in parts[-3:]:
        total = total * 60 + x
    return total if ":" in (value or "") else parts[-1]


def small_image(url):
    """팟캐스트 커버는 3000px 원본이라 작은 크기로 바꿔 쓴다."""
    url = url.replace("http://", "https://")
    url = re.sub(r"/images/ic/\d+x\d+/", "/images/ic/480x480/", url)  # BBC
    url = re.sub(r"/resize/\d+/", "/resize/480/", url)                 # NPR (brightspot)
    return url


# ---------- 뉴스 듣기 ----------
def podcast(show, source, url, used):
    channel, items = feed(url)
    channel_image = attr(channel, "itunes:image", "href")
    for it in items:
        audio = attr(it, "enclosure", "url")
        key = "pod:" + (tag(it, "guid") or audio)
        if not audio or key in used:
            continue
        used.add(key)
        return {
            "type": "video", "media": "audio", "show": show, "title": clean(tag(it, "title")),
            "src": audio.replace("http://", "https://"),
            "image": small_image(attr(it, "itunes:image", "href") or channel_image),
            "duration": seconds(tag(it, "itunes:duration")),
            "date": iso_date(tag(it, "pubDate")),
            "source": tag(it, "link") or tag(channel, "link"), "sourceName": source,
            "credit": f"{clean(tag(channel, 'title'))} · {source}",
        }
    return None


# ---------- 헤드라인 ----------
def headlines(show, source, url, count, used):
    _, items = feed(url)
    out = []
    for it in items:
        link = tag(it, "link")
        key = "news:" + link
        if not link or key in used:
            continue
        used.add(key)
        image = attr(it, "media:thumbnail", "url") or attr(tag(it, "content:encoded"), "img", "src")
        out.append({
            "type": "link", "show": show, "title": clean(tag(it, "title")),
            "summary": clean(tag(it, "description")),
            "image": image.replace("/standard/240/", "/standard/480/"),
            "date": iso_date(tag(it, "pubDate")),
            "source": link, "sourceName": source,
            "credit": f"{source} · 원문은 {source} 사이트에서 읽을 수 있습니다",
        })
        if len(out) == count:
            break
    return out


def build(used):
    listening, reading = [], []
    for show, source, url in PODCASTS:
        try:
            p = podcast(show, source, url, used)
            if p:
                listening.append(p)
        except Exception as e:
            print("podcast failed:", show, e)
    for show, source, url, count in HEADLINES:
        try:
            reading += headlines(show, source, url, count, used)
        except Exception as e:
            print("headlines failed:", show, e)
    programs = listening + reading
    for i, p in enumerate(programs):
        p["id"] = i + 1
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
    programs = build(used)
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
        print(f"  {p['id']}. [{p.get('media', p['type'])}] {p['show']} — {p['title']}")


if __name__ == "__main__":
    main()
