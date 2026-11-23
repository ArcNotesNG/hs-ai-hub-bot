import os
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

app = Flask(__name__)

# Store users waiting for CGPA input
waiting_for_cgpa = set()

@app.route("/")
def home():
    return "H&S AI HUB Bot is running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to H&S AI HUB!\n\n"
        "I'm your AI assistant. Ask me anything!\n\n"
        "Commands:\n"
        "/start - Start bot\n"
        "/help - Help\n"
        "/about - About us\n"
        "/cgpa - Calculate CGPA"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Just type any question and I'll answer with AI! 🤖\n\nOr use /cgpa to calculate your CGPA")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("H&S AI HUB - Your smart AI assistant built by H&S.")

async def cgpa_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    waiting_for_cgpa.add(user_id)
    await update.message.reply_text(
        "📊 CGPA CALCULATOR\n\n"
        "Send your courses like this, one per line:\n\n"
        "A 3\n"
        "B 2\n"
        "A 3\n"
        "C 2\n\n"
        "Grade + Credit unit\n\n"
        "Grades: A=5, B=4, C=3, D=2, E=1, F=0\n\n"
        "Send now!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text.strip()

    # If user is in CGPA mode
    if user_id in waiting_for_cgpa:
        waiting_for_cgpa.remove(user_id)
        try:
            grade_points = {'A':5, 'B':4, 'C':3, 'D':2, 'E':1, 'F':0}
            total_points = 0
            total_units = 0
            lines = user_text.split('\n')
            result_lines = []
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 2:
                    grade = parts[0].upper()
                    unit = int(parts[1])
                    if grade in grade_points:
                        total_points += grade_points[grade] * unit
                        total_units += unit
                        result_lines.append(f"{grade} - {unit} units = {grade_points[grade]*unit} points")
            if total_units == 0:
                await update.message.reply_text("No valid courses found. Try /cgpa again")
                return
            cgpa = total_points / total_units
            msg = "📊 YOUR RESULT:\n\n" + "\n".join(result_lines) + f"\n\nTotal Units: {total_units}\nTotal Points: {total_points}\n\n🎓 CGPA: {cgpa:.2f} / 5.00"
            if cgpa >= 4.5:
                msg += "\n\n🏆 First Class! Excellent!"
            elif cgpa >= 3.5:
                msg += "\n\n🥈 Second Class Upper! Great!"
            elif cgpa >= 2.5:
                msg += "\n\n🥉 Second Class Lower! Keep pushing!"
            elif cgpa >= 1.5:
                msg += "\n\n📚 Third Class - You can do better!"
            else:
                msg += "\n\n💪 Don't give up!"
            await update.message.reply_text(msg)
            return
        except Exception as e:
            await update.message.reply_text(f"Format error. Try /cgpa again. Send like:\nA 3\nB 2")
            return

    await update.message.reply_text("Thinking... 🤔")
    try:
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text[:4000])
    except Exception as e:
        await update.message.reply_text(f"Sorry, error: {e}")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    threading.Thread(target=run_flask, daemon=True).start()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("cgpa", cgpa_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("H&S AI HUB Bot is running...")
    application.run_polling()
