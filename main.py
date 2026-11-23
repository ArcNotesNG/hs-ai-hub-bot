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
# FIXED: Old 2.0 is dead, use new 3.0
model = genai.GenerativeModel("gemini-2.5-flash")

app = Flask(__name__)

# CGPA state: user_id -> {"step":..., "total_courses":..., "current":..., "total_points":..., "total_units":...}
cgpa_users = {}

@app.route("/")
def home():
    return "H&S AI HUB Bot is running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to H&S AI HUB!\n\n"
        "Choose what you want:\n"
        "/cgpa - Calculate CGPA (easy step-by-step)\n"
        "/jamb - JAMB guide\n"
        "/course - Course advice\n"
        "/cutoff - Cut-off marks\n"
        "/nysc - NYSC guide\n"
        "/cv - Build CV\n"
        "/refer - Earn 500 naira\n"
        "/myreferrals - Check earnings\n"
        "/help - Help\n\n"
        "Or just type any question!"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tap /start to see all commands.\n\nFor CGPA, just tap /cgpa and I will guide you one by one.")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("H&S AI HUB - Your smart AI assistant built by H&S.")

# --- CGPA NEW EASY WAY ---
async def cgpa_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cgpa_users[user_id] = {"step": "ask_count", "total_courses": 0, "current": 1, "total_points": 0, "total_units": 0, "courses": []}
    await update.message.reply_text("📊 CGPA CALCULATOR\n\nHow many courses did you offer this semester? Just send the number.\nExample: 5")

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 REFER & EARN 500 NAIRA\n\nYour referral link:\nhttps://t.me/HSAIHUB_bot?start=ref_" + str(update.effective_user.id) + "\n\nShare it, when your friend joins you earn 500 naira. Check with /myreferrals")

async def myreferrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Your referrals: 0\nEarnings: ₦0\n\nShare your link with /refer to start earning!")

async def jamb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 JAMB GUIDE\n\nType your question about JAMB, e.g. 'What is JAMB cutoff for UNILAG?' and I will answer with AI.")

async def course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎓 COURSE ADVICE\n\nTell me your interests and JAMB score, e.g. 'I love science, JAMB 250, what course?'")

async def cutoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✂️ CUT-OFF MARKS\n\nType the school name, e.g. 'Cutoff for UNILAG' and I will tell you.")

async def nysc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎓 NYSC GUIDE\n\nAsk me anything about NYSC mobilization, camp, PPA, etc.")

async def cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📄 CV BUILDER\n\nSend me your name, course, skills and experience, and I will build a professional CV for you.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text.strip()

    # CGPA FLOW
    if user_id in cgpa_users:
        state = cgpa_users[user_id]
        grade_points = {'A':5, 'B':4, 'C':3, 'D':2, 'E':1, 'F':0}

        if state["step"] == "ask_count":
            try:
                n = int(user_text)
                if n <= 0 or n > 20:
                    await update.message.reply_text("Please send a number between 1 and 20")
                    return
                state["total_courses"] = n
                state["step"] = "ask_grade"
                await update.message.reply_text(f"Good! You have {n} courses.\n\nCourse 1: What GRADE did you get? Send A, B, C, D, E or F")
                return
            except:
                await update.message.reply_text("Please send only a number. Example: 5")
                return

        if state["step"] == "ask_grade":
            grade = user_text.upper()
            if grade not in grade_points:
                await update.message.reply_text("Please send only A, B, C, D, E or F")
                return
            state["temp_grade"] = grade
            state["step"] = "ask_unit"
            await update.message.reply_text(f"Course {state['current']}: Grade {grade} ✅\n\nHow many UNITS is this course? Example: 3")
            return

        if state["step"] == "ask_unit":
            try:
                unit = int(user_text)
                grade = state["temp_grade"]
                points = grade_points[grade] * unit
                state["total_points"] += points
                state["total_units"] += unit
                state["courses"].append(f"Course {state['current']}: {grade} ({unit} units) = {points} pts")
                if state["current"] >= state["total_courses"]:
                    cgpa = state["total_points"] / state["total_units"] if state["total_units"] else 0
                    msg = "📊 YOUR RESULT:\n\n" + "\n".join(state["courses"]) + f"\n\nTotal Units: {state['total_units']}\nTotal Points: {state['total_points']}\n\n🎓 CGPA: {cgpa:.2f} / 5.00"
                    if cgpa >= 4.5: msg += "\n\n🏆 First Class! Excellent!"
                    elif cgpa >= 3.5: msg += "\n\n🥈 Second Class Upper!"
                    elif cgpa >= 2.5: msg += "\n\n🥉 Second Class Lower!"
                    elif cgpa >= 1.5: msg += "\n\n📚 Third Class"
                    else: msg += "\n\n💪 Don't give up!"
                    await update.message.reply_text(msg)
                    del cgpa_users[user_id]
                    return
                else:
                    state["current"] += 1
                    state["step"] = "ask_grade"
                    await update.message.reply_text(f"Saved! ✅\n\nCourse {state['current']}: What GRADE? Send A/B/C/D/E/F")
                    return
            except:
                await update.message.reply_text("Please send only a number for units. Example: 3")
                return

    # NORMAL AI
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
    application.add_handler(CommandHandler("refer", refer))
    application.add_handler(CommandHandler("myreferrals", myreferrals))
    application.add_handler(CommandHandler("jamb", jamb))
    application.add_handler(CommandHandler("course", course))
    application.add_handler(CommandHandler("cutoff", cutoff))
    application.add_handler(CommandHandler("nysc", nysc))
    application.add_handler(CommandHandler("cv", cv))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("H&S AI HUB Bot is running...")
    application.run_polling()
