import feedparser
import requests
import logging
import random
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    {"name": "The Hacker News",    "url": "https://feeds.feedburner.com/TheHackersNews",           "emoji": "🔴"},
    {"name": "Bleeping Computer",  "url": "https://www.bleepingcomputer.com/feed/",                 "emoji": "💻"},
    {"name": "Krebs on Security",  "url": "https://krebsonsecurity.com/feed/",                      "emoji": "🔐"},
    {"name": "Dark Reading",       "url": "https://www.darkreading.com/rss.xml",                    "emoji": "🌑"},
    {"name": "SecurityWeek",       "url": "https://feeds.feedburner.com/Securityweek",              "emoji": "📡"},
    {"name": "Naked Security",     "url": "https://nakedsecurity.sophos.com/feed/",                 "emoji": "🛡️"},
    {"name": "Malwarebytes Labs", "url": "https://blog.malwarebytes.com/feed/",                    "emoji": "🦠"},
    {"name": "Exploit-DB",        "url": "https://www.exploit-db.com/rss.xml",                     "emoji": "💣"},
    {"name": "CISA Alerts",       "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",  "emoji": "🏛️"},
    {"name": "Graham Cluley",     "url": "https://grahamcluley.com/feed/",                         "emoji": "🕵️"},
    {"name": "Threatpost",        "url": "https://threatpost.com/feed/",                           "emoji": "⚠️"},
    {"name": "Reddit /r/netsec",  "url": "https://www.reddit.com/r/netsec/.rss",                   "emoji": "📰"},
    {"name": "Reddit /r/malware", "url": "https://www.reddit.com/r/Malware/.rss",                  "emoji": "🐛"},
    {"name": "Reddit /r/hacking", "url": "https://www.reddit.com/r/hacking/.rss",                  "emoji": "⚡"},
    {"name": "Reddit r/cybersec", "url": "https://www.reddit.com/r/cybersecurity/.rss",            "emoji": "🔒"},
    {"name": "Packet Storm",      "url": "https://packetstormsecurity.com/feeds/",                 "emoji": "🌩️"},
    {"name": "CXSecurity",        "url": "https://cxsecurity.com/cxsecurity.xml",                  "emoji": "🚨"},
    {"name": "Full Disclosure",   "url": "https://seclists.org/rss/fulldisclosure.rss",            "emoji": "📣"},
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _clean_html(text: str) -> str:
    if not text:
        return ""
    try:
        soup = BeautifulSoup(text, "lxml")
        return soup.get_text(separator=" ").strip()
    except Exception:
        return text[:300]


def fetch_from_feed(feed_info: dict) -> list:
    articles = []
    try:
        feed = feedparser.parse(feed_info["url"], request_headers=HEADERS)
        for entry in feed.entries[:15]:
            url = entry.get("link", "")
            if not url:
                continue
            title = entry.get("title", "Fara titlu").strip()
            summary = _clean_html(
                entry.get("summary", entry.get("description", ""))
            )[:250]
            articles.append({
                "title":       title,
                "url":         url,
                "source":      feed_info["name"],
                "emoji":       feed_info["emoji"],
                "description": summary,
                "published":   entry.get("published", ""),
            })
    except Exception as e:
        logger.warning("Eroare la feed %s: %s", feed_info["name"], e)
    return articles


def fetch_articles() -> list:
    feeds = RSS_FEEDS.copy()
    random.shuffle(feeds)
    all_articles = []
    for feed_info in feeds:
        articles = fetch_from_feed(feed_info)
        all_articles.extend(articles)
    logger.info("Total articole gasite: %d", len(all_articles))
    return all_articles
