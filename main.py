import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are H&S AI HUB - a professional Nigerian student assistant.
You help with: CGPA calculation, JAMB, Post-UTME, Cutoff marks, NYSC, CV writing, assignments, study tips, and general questions.
Be friendly, clear, professional. Use simple English. Use emojis small-small. If user asks CGPA, ask for grades and credits and calculate it."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *H&S AI HUB*!\n\nI'm your professional study assistant.\n\nI can help you with:\n✅ CGPA Calculation\n✅ JAMB / Cutoff / Post-UTME\n✅ NYSC Questions\n✅ CV Writing\n✅ Assignments & Study Tips\n\nJust type your question!",
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
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        print(f"Groq Error: {e}")
        await update.message.reply_text("Sorry, try again in a few seconds 🙏")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    port = int(os.environ.get("PORT", 10000))
    print(f"Starting webhook on port {port}...")
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
    )

if __name__ == "__main__":
    main()
