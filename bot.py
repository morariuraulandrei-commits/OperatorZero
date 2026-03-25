"""
OperatorZero - Telegram Cybersecurity Intelligence Bot
Colecteaza stiri din RSS + canale Telegram publice de cybersecurity.
Le trimite direct in chat-ul tau privat, la fiecare 5 minute.
Nu ai nevoie de canal propriu!
"""
import asyncio
import logging
import os
import sys

# Asigura existenta directorului data/
os.makedirs("data", exist_ok=True)

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
import database
import scraper

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Lista de chat-uri active (useri care au dat /start)
active_chats: set = set()
# Chat ID configurat manual (optional, din CHANNEL_ID env)
if config.CHANNEL_ID:
    active_chats.add(config.CHANNEL_ID)


def format_article(article: dict) -> str:
    """Formateaza un articol pentru Telegram MarkdownV2."""
    emoji  = article.get("emoji", "\U0001f4e1")
    source = article.get("source", "Unknown")
    title  = article.get("title", "No title")
    desc   = article.get("description", "")
    url    = article.get("url", "")

    def esc(text: str) -> str:
        for ch in ["_","*","[","]","(",")","`","~",">","#","+","-","=","|","{","}",".", "!"]:
            text = text.replace(ch, f"\\{ch}")
        return text

    lines = [f"{emoji} *{esc(source)}*", "", f"\U0001f4f0 *{esc(title)}*"]
    if desc:
        lines += ["", f"_{esc(desc[:200])}\\.\\.\\._ "]
    lines += ["", f"\U0001f517 [Citeste mai mult]({url})"]
    return "\n".join(lines)


async def post_news(bot: Bot, chat_id: str = None):
    """Preia stiri noi si le trimite in toate chat-urile active."""
    targets = {chat_id} if chat_id else active_chats
    if not targets:
        logger.warning("Niciun chat activ. Trimite /start botului pe Telegram!")
        return

    try:
        articles = scraper.fetch_articles()
        new_articles = [
            a for a in articles
            if a["url"] and not database.is_posted(config.DB_PATH, a["url"])
        ]
        to_post = new_articles[:config.ITEMS_PER_BATCH]
        if not to_post:
            logger.info("Nicio stire noua de postat.")
            return

        logger.info("Postez %d articole in %d chat(uri).", len(to_post), len(targets))
        for article in to_post:
            for target in list(targets):
                try:
                    await bot.send_message(
                        chat_id=target,
                        text=format_article(article),
                        parse_mode=ParseMode.MARKDOWN_V2,
                        disable_web_page_preview=False,
                    )
                    await asyncio.sleep(0.5)
                except TelegramError as te:
                    logger.error("Eroare Telegram catre %s: %s", target, te)
                except Exception as e:
                    logger.error("Eroare neasteptata: %s", e)
            database.mark_posted(config.DB_PATH, article["url"], article["title"], article["source"])
            await asyncio.sleep(1.0)
    except Exception as e:
        logger.error("Eroare in post_news: %s", e)


# ──────────────────────────────────────────────
# COMENZI BOT
# ──────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inregistreaza userul si trimite mesaj de bun venit."""
    chat_id = str(update.effective_chat.id)
    active_chats.add(chat_id)
    await update.message.reply_text(
        f"\U0001f916 *OperatorZero* \- Cybersecurity Intelligence Bot\n\n"
        f"Bun venit\! Vei primi *{config.ITEMS_PER_BATCH} stiri noi* la fiecare "
        f"*{config.FETCH_INTERVAL // 60} minute*, direct aici\.\n\n"
        f"\U0001f4e1 *Surse RSS:* {len(scraper.RSS_FEEDS)}\n"
        f"\U0001f4f2 *Canale Telegram:* {len(scraper.TELEGRAM_CHANNELS)}\n\n"
        f"Foloseste /fetch pentru o actualizare imediata\!",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    logger.info("Nou utilizator inregistrat: %s", chat_id)
    # Trimite primele stiri imediat
    await post_news(context.bot, chat_id=chat_id)


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Opreste trimiterile pentru acest chat."""
    chat_id = str(update.effective_chat.id)
    active_chats.discard(chat_id)
    await update.message.reply_text(
        "\u23f9 Oprit\. Nu vei mai primi stiri\. Trimite /start pentru a relua\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Afiseaza statusul botului."""
    stats = database.get_stats(config.DB_PATH)
    chat_id = str(update.effective_chat.id)
    activ = "\u2705 Activ" if chat_id in active_chats else "\u274c Inactiv \(trimite /start\)"
    await update.message.reply_text(
        f"\U0001f916 *Status OperatorZero*\n\n"
        f"Status: {activ}\n"
        f"\u23f0 Interval: {config.FETCH_INTERVAL // 60} min\n"
        f"\U0001f4e1 Surse RSS: {len(scraper.RSS_FEEDS)}\n"
        f"\U0001f4f2 Canale Telegram: {len(scraper.TELEGRAM_CHANNELS)}\n"
        f"\U0001f4ca Total articole postate: {stats['total']}\n"
        f"\U0001f465 Chat\-uri active: {len(active_chats)}",
        parse_mode=ParseMode.MARKDOWN_V2
    )


async def cmd_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forteaza o actualizare imediata."""
    chat_id = str(update.effective_chat.id)
    active_chats.add(chat_id)
    await update.message.reply_text(
        "\U0001f504 Caut stiri noi\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    await post_news(context.bot, chat_id=chat_id)
    await update.message.reply_text(
        "\u2705 Gata\\!",
        parse_mode=ParseMode.MARKDOWN_V2
    )


async def cmd_sources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Afiseaza lista de surse monitorizate."""
    rss_list = "\n".join([f"  \u2022 {f['emoji']} {f['name']}" for f in scraper.RSS_FEEDS])
    tg_list  = "\n".join([f"  \u2022 {c['emoji']} @{c['channel']}" for c in scraper.TELEGRAM_CHANNELS])
    await update.message.reply_text(
        f"*Surse RSS \({len(scraper.RSS_FEEDS)}\):*\n{rss_list}\n\n"
        f"*Canale Telegram \({len(scraper.TELEGRAM_CHANNELS)}\):*\n{tg_list}",
        parse_mode=ParseMode.MARKDOWN_V2
    )


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Afiseaza statistici."""
    stats = database.get_stats(config.DB_PATH)
    lines = [f"\U0001f4ca *Statistici OperatorZero*\n\nTotal articole postate: *{stats['total']}*\n"]
    for src, cnt in stats.get("top_sources", [])[:10]:
        lines.append(f"  \u2022 {src}: {cnt}")
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN_V2
    )


# ──────────────────────────────────────────────
# INITIALIZARE & MAIN
# ──────────────────────────────────────────────

async def post_init(application: Application):
    """Initializare dupa pornirea aplicatiei."""
    database.init_db(config.DB_PATH)
    scheduler = AsyncIOScheduler(timezone="Europe/Bucharest")
    scheduler.add_job(
        post_news,
        "interval",
        seconds=config.FETCH_INTERVAL,
        args=[application.bot],
        id="news_job",
        replace_existing=True
    )
    scheduler.start()
    logger.info(
        "OperatorZero pornit! RSS: %d surse | Telegram: %d canale | Interval: %ds",
        len(scraper.RSS_FEEDS), len(scraper.TELEGRAM_CHANNELS), config.FETCH_INTERVAL
    )


def main():
    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("stop",    cmd_stop))
    app.add_handler(CommandHandler("status",  cmd_status))
    app.add_handler(CommandHandler("fetch",   cmd_fetch))
    app.add_handler(CommandHandler("sources", cmd_sources))
    app.add_handler(CommandHandler("stats",   cmd_stats))
    logger.info("OperatorZero Bot pornit!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
