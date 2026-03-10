import logging
import pytz
import os
import requests
from datetime import time
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
TIMEZONE = "Asia/Riyadh"
DAILY_HOUR = 9

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
user_data = {}

def get_latest_news(topic="Elon Musk AI technology"):
    url = f"https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
    r = requests.get(url)
    articles = r.json().get("articles", [])
    news = ""
    for a in articles[:5]:
        news += f"- {a['title']}\n"
    return news if news else "No news found"

def ask_ai(prompt):
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system="You are a Twitter growth expert in Tech and AI niche. Write viral English content only.",
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text

def gen_daily(topic="Elon Musk AI"):
    news = get_latest_news(topic)
    return ask_ai(f"""Latest news about "{topic}":
{news}
Create in ENGLISH ONLY:
🔥 3 ready-to-post tweets (under 280 chars each)
🧵 Thread idea (hook + 5 points + CTA)
💬 3 reply templates
📈 One growth tip""")

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id] = {"subscribed": True}
    await update.message.reply_text(
        "🤖 Welcome! Twitter Growth Bot with LIVE NEWS!\n\n"
        "/daily — Latest news + tweets\n"
        "/news [topic] — Search any topic\n"
        "/reply [tweet] — Pro replies\n"
        "/hooks — Viral hooks\n"
        "/thread [topic] — Full thread"
    )

async def daily_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args) if ctx.args else "Elon Musk AI technology"
    msg = await update.message.reply_text("⏳ Fetching latest news...")
    try:
        await msg.edit_text(gen_daily(topic))
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

async def news_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args) if ctx.args else "AI technology"
    msg = await update.message.reply_text("⏳ Searching news...")
    try:
        news = get_latest_news(topic)
        result = ask_ai(f"Latest news:\n{news}\n\nWrite 3 viral tweets based on these headlines in English only.")
        await msg.edit_text(f"📰 Latest on {topic}:\n\n{result}")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

async def reply_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tweet = " ".join(ctx.args)
    if not tweet:
        await update.message.reply_text("Send: /reply [tweet text]")
        return
    msg = await update.message.reply_text("⏳ Writing replies...")
    try:
        result = ask_ai(f'Write 3 killer English replies to: "{tweet}" Each under 200 chars.')
        await msg.edit_text(result)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

async def hooks_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Generating hooks...")
    try:
        result = ask_ai("Write 10 viral English tweet hooks for Tech & AI niche.")
        await msg.edit_text(result)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

async def thread_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args)
    if not topic:
        await update.message.reply_text("Send: /thread [topic]")
        return
    news = get_latest_news(topic)
    msg = await update.message.reply_text("⏳ Writing thread...")
    try:
        result = ask_ai(f'Latest news:\n{news}\n\nWrite a 7-tweet thread about "{topic}". 1/hook 2-6/value 7/CTA')
        await msg.edit_text(result)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

async def send_daily(ctx: ContextTypes.DEFAULT_TYPE):
    for chat_id, user in user_data.items():
        if user.get("subscribed"):
            try:
                await ctx.bot.send_message(chat_id=chat_id, text=f"🌅 Daily Twitter package:\n\n{gen_daily()}")
            except:
                pass

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("news", news_cmd))
    app.add_handler(CommandHandler("reply", reply_cmd))
    app.add_handler(CommandHandler("hooks", hooks_cmd))
    app.add_handler(CommandHandler("thread", thread_cmd))
    tz = pytz.timezone(TIMEZONE)
    app.job_queue.run_daily(send_daily, time=time(DAILY_HOUR, 0, tzinfo=tz))
    print("🤖 Bot is running!")
    app.run_polling()

if __name__ == "__main__":
    main()
