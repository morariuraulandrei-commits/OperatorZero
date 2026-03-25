"""
OperatorZero - Scraper
Colecteaza stiri din RSS feeds + canale publice Telegram de cybersecurity.
"""
import random
import re
import time
import logging

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# RSS FEEDS
# ──────────────────────────────────────────────
RSS_FEEDS = [
    {"name": "The Hacker News",    "url": "https://feeds.feedburner.com/TheHackersNews",          "emoji": "\U0001f4e1"},
    {"name": "Bleeping Computer",  "url": "https://www.bleepingcomputer.com/feed/",                "emoji": "\U0001f4bb"},
    {"name": "Krebs on Security",  "url": "https://krebsonsecurity.com/feed/",                     "emoji": "\U0001f575"},
    {"name": "Dark Reading",       "url": "https://www.darkreading.com/rss.xml",                   "emoji": "\U0001f30d"},
    {"name": "SecurityWeek",       "url": "https://feeds.feedburner.com/Securityweek",             "emoji": "\U0001f6e1"},
    {"name": "Naked Security",     "url": "https://nakedsecurity.sophos.com/feed/",                "emoji": "\U0001f512"},
    {"name": "Malwarebytes Labs",  "url": "https://blog.malwarebytes.com/feed/",                   "emoji": "\U0001f9f9"},
    {"name": "Exploit-DB",         "url": "https://www.exploit-db.com/rss.xml",                    "emoji": "\U0001f4a3"},
    {"name": "CISA Alerts",        "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml", "emoji": "\U0001f6a8"},
    {"name": "Graham Cluley",      "url": "https://grahamcluley.com/feed/",                        "emoji": "\U0001f4dd"},
    {"name": "Reddit r/netsec",    "url": "https://www.reddit.com/r/netsec/.rss",                  "emoji": "\U0001f47e"},
    {"name": "Reddit r/hacking",   "url": "https://www.reddit.com/r/hacking/.rss",                 "emoji": "\U0001f3af"},
    {"name": "Packet Storm",       "url": "https://rss.packetstormsecurity.com/files/",            "emoji": "\u26a1"},
    {"name": "Full Disclosure",    "url": "https://seclists.org/rss/fulldisclosure.rss",           "emoji": "\U0001f4e2"},
]

# ──────────────────────────────────────────────
# CANALE TELEGRAM PUBLICE DE CYBERSECURITY
# Accesate prin interfata web publica: t.me/s/canal
# ──────────────────────────────────────────────
TELEGRAM_CHANNELS = [
    {"name": "The Hacker News TG",   "channel": "thehackernews",        "emoji": "\U0001f4e1"},
    {"name": "Cyber Security News",  "channel": "cybersecuritynewss",   "emoji": "\U0001f6e1"},
    {"name": "Dark Web Informer",    "channel": "DarkWebInformer",       "emoji": "\U0001f578"},
    {"name": "CVE & Exploits",       "channel": "cve_exploits",          "emoji": "\U0001f4a3"},
    {"name": "Hacking & Security",   "channel": "hackingsecurity",       "emoji": "\U0001f3af"},
    {"name": "Malware Traffic",      "channel": "malware_traffic",       "emoji": "\U0001f9a0"},
    {"name": "CyberSecurity HQ",     "channel": "cybersecurityhq",       "emoji": "\U0001f512"},
    {"name": "InfoSec Today",        "channel": "infosectoday",          "emoji": "\U0001f30d"},
    {"name": "Threat Intel",         "channel": "threatintel",           "emoji": "\U0001f575"},
    {"name": "Zero Day Exploits",    "channel": "zerodayexploits",       "emoji": "\u26a1"},
    {"name": "Ransomware Monitor",   "channel": "ransomwaremonitor",     "emoji": "\U0001f512"},
    {"name": "Security Affairs",     "channel": "securityaffairs",       "emoji": "\U0001f4f0"},
    {"name": "Cyber Army",           "channel": "CyberArmyRomania",      "emoji": "\U0001f1f7\U0001f1f4"},
    {"name": "Hack The Box News",    "channel": "HackTheBoxOfficial",    "emoji": "\U0001f4e6"},
    {"name": "OSINT Romania",        "channel": "osintromania",          "emoji": "\U0001f50d"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def clean_html(text: str) -> str:
    """Elimina tag-uri HTML si curata textul."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:300]


def fetch_from_rss(feed_info: dict) -> list:
    """Preia articole dintr-un RSS feed."""
    articles = []
    try:
        feed = feedparser.parse(feed_info["url"])
        for entry in feed.entries[:5]:
            title = clean_html(entry.get("title", ""))
            url   = entry.get("link", "")
            desc  = clean_html(entry.get("summary", "") or entry.get("description", ""))
            if title and url:
                articles.append({
                    "title":       title,
                    "url":         url,
                    "description": desc,
                    "source":      feed_info["name"],
                    "emoji":       feed_info["emoji"],
                })
    except Exception as e:
        logger.warning("RSS error %s: %s", feed_info["name"], e)
    return articles


def fetch_from_telegram(channel_info: dict) -> list:
    """
    Preia mesaje din canalul public Telegram prin interfata web t.me/s/.
    Nu necesita credentiale API.
    """
    articles = []
    channel = channel_info["channel"]
    url = f"https://t.me/s/{channel}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return articles

        soup = BeautifulSoup(resp.text, "lxml")
        # Mesajele din canalul public
        messages = soup.select(".tgme_widget_message_wrap")

        for msg in messages[-8:]:  # ultimele 8 mesaje
            # Text mesaj
            text_el = msg.select_one(".tgme_widget_message_text")
            text = text_el.get_text(" ", strip=True) if text_el else ""

            # Link catre mesaj
            link_el = msg.select_one(".tgme_widget_message_date a")
            msg_url = link_el["href"] if link_el and link_el.get("href") else url

            # Link extern (daca exista in mesaj)
            ext_link = msg.select_one(".tgme_widget_message_text a")
            final_url = ext_link["href"] if ext_link and ext_link.get("href", "").startswith("http") else msg_url

            if text and len(text) > 20:
                # Titlu = primele 100 de caractere
                title = text[:100].strip()
                if len(text) > 100:
                    title += "..."
                desc = text[100:300].strip() if len(text) > 100 else ""
                articles.append({
                    "title":       title,
                    "url":         final_url,
                    "description": desc,
                    "source":      f"TG: {channel_info['name']}",
                    "emoji":       channel_info["emoji"],
                })
    except Exception as e:
        logger.warning("Telegram scrape error %s: %s", channel, e)
    return articles


def fetch_articles() -> list:
    """
    Agrega stiri din RSS feeds + canale Telegram.
    Returneaza lista amestecata, fara duplicate de URL.
    """
    all_articles = []
    seen_urls = set()

    # --- RSS feeds ---
    feeds_shuffled = RSS_FEEDS.copy()
    random.shuffle(feeds_shuffled)
    for feed in feeds_shuffled:
        arts = fetch_from_rss(feed)
        for a in arts:
            if a["url"] and a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                all_articles.append(a)
        time.sleep(0.2)

    # --- Canale Telegram ---
    tg_shuffled = TELEGRAM_CHANNELS.copy()
    random.shuffle(tg_shuffled)
    for ch in tg_shuffled:
        arts = fetch_from_telegram(ch)
        for a in arts:
            if a["url"] and a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                all_articles.append(a)
        time.sleep(0.3)

    random.shuffle(all_articles)
    logger.info("Articole gasite total: %d (RSS + Telegram)", len(all_articles))
    return all_articles
