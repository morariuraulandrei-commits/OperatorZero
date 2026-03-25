"""
OperatorZero - Telegram Cybersecurity Intelligence Bot
Posteaza automat 6 stiri de securitate cibernetica la fiecare 5 minute.
"""
import asyncio
import logging
import os
import sys

# Asigura existenta directorului data/ (pentru log si baza de date)
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

channel_id: str = config.CHANNEL_ID


def format_article(article: dict) -> str:
    emoji  = article.get("emoji", "\U0001f4e1")
    source = article.get("source", "Unknown")
    title  = article.get("title", "No title")
    desc   = article.get("description", "")
    url    = article.get("url", "")

    def esc(text: str) -> str:
        for ch in ["_","*","[","]","(",")","`","~",">","#","+","-","=","|","{","}",".",  "!"]:
            text = text.replace(ch, f"\\{ch}")
        return text

    lines = [f"{emoji} *{esc(source)}*", "", f"\U0001f4f0 *{esc(title)}*"]
    if desc:
        lines += ["", f"_{esc(desc[:200])}\\.\\.\\._ "]
    lines += ["", f"\U0001f517 [Citeste articolul]({url})"]
    return "\n".join(lines)


async def post_news(bot: Bot, chat_id: str = None):
    global channel_id
    target = chat_id or channel_id
    if not target:
        logger.warning("Nu am setat CHANNEL_ID. Foloseste /setchannel.")
        return
    try:
        articles = scraper.fetch_articles()
        new_articles = [
            a for a in articles
            if a["url"] and not database.is_posted(config.DB_PATH, a["url"])
        ]
        to_post = new_articles[:config.ITEMS_PER_BATCH]
        if not to_post:
            logger.info("Nicio stire noua.")
            return
        for article in to_post:
            try:
                await bot.send_message(
                    chat_id=target,
                    text=format_article(article),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    disable_web_page_preview=False,
                )
                database.mark_posted(config.DB_PATH, article["url"], article["title"], article["source"])
                await asyncio.sleep(1.5)
            except TelegramError as te:
                logger.error("Eroare Telegram: %s", te)
            except Exception as e:
                logger.error("Eroare neasteptata: %s", e)
    except Exception as e:
        logger.error("Eroare in post_news: %s", e)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"\U0001f916 *OperatorZero* - Cybersecurity Intelligence Bot\n\n"
        f"\U0001f4e1 *Surse:* {len(scraper.RSS_FEEDS)}\n"
        f"\u23f0 *Interval:* {config.FETCH_INTERVAL // 60} minute\n"
        f"\U0001f4f0 *Stiri/ciclu:* {config.ITEMS_PER_BATCH}\n\n"
        "\U0001f4cb *Comenzi:*\n"
        "/status - stare bot\n/setchannel @id - seteaza canal\n"
        "/fetch - actualizeaza manual\n/stats - statistici",
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = database.get_stats(config.DB_PATH)
    await update.message.reply_text(
        f"\u2705 *Bot:* Online\n\U0001f4e1 *Canal:* `{channel_id or 'Nesetat'}`\n"
        f"\u23f0 *Interval:* {config.FETCH_INTERVAL // 60} min\n"
        f"\U0001f4e1 *Surse RSS:* {len(scraper.RSS_FEEDS)}\n"
        f"\U0001f4ca *Total postate:* {stats['total']}",
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_setchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global channel_id
    if not context.args:
        await update.message.reply_text("\u26a0\ufe0f Utilizare: `/setchannel @canal`", parse_mode=ParseMode.MARKDOWN)
        return
    channel_id = context.args[0]
    await update.message.reply_text(f"\u2705 Canal setat: `{channel_id}`", parse_mode=ParseMode.MARKDOWN)


async def cmd_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\U0001f504 Actualizare in curs\\.\\.\\.", parse_mode=ParseMode.MARKDOWN_V2)
    await post_news(context.bot)
    await update.message.reply_text("\u2705 Gata\\!", parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = database.get_stats(config.DB_PATH)
    lines = [f"\U0001f4ca *Statistici OperatorZero*\n\nTotal postate: *{stats['total']}*"]
    for src, cnt in stats.get("top_sources", []):
        lines.append(f"  \u2022 {src}: {cnt}")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def post_init(application: Application):
    database.init_db(config.DB_PATH)
    scheduler = AsyncIOScheduler(timezone="Europe/Bucharest")
    scheduler.add_job(post_news, "interval", seconds=config.FETCH_INTERVAL,
                      args=[application.bot], id="news_job", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler pornit - interval %ds canal '%s'", config.FETCH_INTERVAL, config.CHANNEL_ID or "nesetat")


def main():
    app = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("status",     cmd_status))
    app.add_handler(CommandHandler("setchannel", cmd_setchannel))
    app.add_handler(CommandHandler("fetch",      cmd_fetch))
    app.add_handler(CommandHandler("stats",      cmd_stats))
    logger.info("OperatorZero Bot pornit!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
