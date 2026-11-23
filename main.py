import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# --- SETUP ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")  # Render gives this automatically

client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# Build Telegram app
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

SYSTEM_PROMPT = """You are H&S AI HUB - a professional Nigerian student assistant.
You help with: CGPA calculation, JAMB, Post-UTME, Cutoff marks, NYSC, CV writing, assignments, study tips, and general questions.
Be friendly, clear, professional. Use simple English. Use emojis small-small. If user asks CGPA, ask for grades and credits and calculate it.
Always be helpful like a professional tutor."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *H&S AI HUB*!\n\nI'm your professional study assistant.\n\nI can help you with:\n✅ CGPA Calculation\n✅ JAMB / Cutoff / Post-UTME\n✅ NYSC Questions\n✅ CV Writing\n✅ Assignments & Study Tips\n\nJust type your question and I will answer.\n\nExample: *Calculate my CGPA* or *What is JAMB cutoff for UNILAG?*",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.chat.send_action("typing")
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        print(f"Groq Error: {e}")
        await update.message.reply_text("Sorry, I'm having a small issue. Please try again in a few seconds 🙏")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route("/")
def home():
    return "H&S AI HUB Bot is Running ✅"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "ok"

if __name__ == "__main__":
    import asyncio
    async def setup():
        await telegram_app.initialize()
        if WEBHOOK_URL:
            await telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}")
        await telegram_app.start()
    asyncio.run(setup())
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
