import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

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

@app.route("/")
def home():
    return "H&S AI HUB Bot is Running ✅"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def main():
    # Delete old webhook so polling can work
    import asyncio
    from telegram import Bot
    async def delete_webhook():
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.delete_webhook(drop_pending_updates=True)
    asyncio.run(delete_webhook())

    threading.Thread(target=run_flask, daemon=True).start()

    telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot started with polling...")
    telegram_app.run_polling()

if __name__ == "__main__":
    main()
