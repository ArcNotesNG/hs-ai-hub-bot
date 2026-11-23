# H&S AI HUB Bot - JSS1 to JOB - FREE VERSION
import os, sqlite3, logging, threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

def ask_ai(prompt):
    try:
        r = model.generate_content(
            f"You are H&S AI HUB, a friendly Nigerian student partner from JSS1 to JOB. "
            f"Help with course advice, JAMB, cut-off, CGPA, NYSC, CV, study. "
            f"Use simple English, Nigerian context, give clear steps, correct facts. "
            f"Question: {prompt}"
        )
        return r.text
    except Exception as e:
        return "Sorry, AI is busy now. Try again in 1 minute. 🙏"

app_flask = Flask(__name__)
@app_flask.route("/")
def home():
    return "H&S AI HUB Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

db = sqlite3.connect("hs_hub.db", check_same_thread=False)
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, referred_by INTEGER, balance INTEGER DEFAULT 0, referrals INTEGER DEFAULT 0)")
db.commit()

def get_user(user_id, username=None):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    u = cur.fetchone()
    if not u:
        cur.execute("INSERT INTO users (user_id, username) VALUES (?,?)", (user_id, username))
        db.commit()
    return u

logging.basicConfig(level=logging.INFO)

WELCOME = """
👋 Welcome to *H&S AI HUB* 🇳🇬
*JSS1 to JOB - Your Complete Student Partner*

🎯 Course Advisor & Cut-off Mark Checker
📚 Summarize handout to exam questions
🎓 CGPA & JAMB Calculator
⭐ NYSC Guide & CV Builder
💰 Refer & Earn ₦500 per friend to Opay, PalmPay & any bank

👇 Tap START to begin - From JSS1 to your first JOB!
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user(user.id, user.username)
    if context.args:
        try:
            referrer_id = int(context.args[0].replace("ref_", ""))
            if referrer_id != user.id:
                cur.execute("SELECT referred_by FROM users WHERE user_id=?", (user.id,))
                row = cur.fetchone()
                if row and row[0] is None:
                    cur.execute("UPDATE users SET referred_by=? WHERE user_id=?", (referrer_id, user.id))
                    cur.execute("UPDATE users SET balance=balance+500, referrals=referrals+1 WHERE user_id=?", (referrer_id,))
                    db.commit()
                    await context.bot.send_message(referrer_id, "🎉 You earned ₦500! Someone joined with your link. Use /myreferrals to check.")
        except: pass
    await update.message.reply_text(WELCOME, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎓 CGPA", callback_data="cgpa"), InlineKeyboardButton("📝 JAMB", callback_data="jamb")],
            [InlineKeyboardButton("🎯 Course", callback_data="course"), InlineKeyboardButton("✂️ Cut-off", callback_data="cutoff")],
            [InlineKeyboardButton("⭐ NYSC", callback_data="nysc"), InlineKeyboardButton("📄 CV", callback_data="cv")],
            [InlineKeyboardButton("💰 Earn ₦500", callback_data="refer")],
        ]))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "How to use H&S AI HUB:\n\n"
        "/start - Start\n/refer - Get your ₦500 referral link\n/myreferrals - Check earnings\n"
        "/cgpa - Example: /cgpa 3.5, 4.0, 2.8\n"
        "/jamb - Example: /jamb UNILAG Computer Science\n"
        "/course - Example: /course I like Biology, what course?\n"
        "/cutoff - Example: /cutoff UNILAG Medicine\n"
        "/nysc - NYSC guide\n"
        "/cv - Example: /cv My name is John, make CV for me\n\n"
        "Or just type any question!"
    )

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    link = f"https://t.me/HS_AI_HUB_Bot?start=ref_{uid}"
    await update.message.reply_text(f"💰 *Refer & Earn ₦500*\n\nYour link:\n`{link}`\n\nShare it. When your friend starts the bot, you get ₦500 instantly.\nWithdraw to Opay, PalmPay or any bank.\n\nUse /myreferrals to check balance.", parse_mode="Markdown")

async def myreferrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur.execute("SELECT balance, referrals FROM users WHERE user_id=?", (update.effective_user.id,))
    row = cur.fetchone() or (0,0)
    await update.message.reply_text(f"💰 *Your Referrals*\n\nFriends: {row[1]}\nBalance: ₦{row[0]}\n\nLink: https://t.me/HS_AI_HUB_Bot?start=ref_{update.effective_user.id}", parse_mode="Markdown")

async def cgpa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🎓 *CGPA Calculator*\n\nSend like this:\n/cgpa 3.5, 4.0, 2.8", parse_mode="Markdown"); return
    try:
        text = " ".join(context.args).replace(",", " ")
        gpas = [float(x) for x in text.split()]
        val = sum(gpas)/len(gpas)
        grade = "First Class 🎉" if val>=4.5 else "Second Class Upper" if val>=3.5 else "Second Class Lower" if val>=2.5 else "Third Class" if val>=1.5 else "Pass"
        await update.message.reply_text(f"🎓 *Your CGPA: {val:.2f}*\nSemesters: {len(gpas)}\nClass: {grade}\n\nKeep pushing! JSS1 to JOB!", parse_mode="Markdown")
    except:
        await update.message.reply_text("Send like: /cgpa 3.5, 4.0, 2.8")

async def ai_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, kind=""):
    q = " ".join(context.args) if context.args else ""
    examples = {
        "jamb": "📝 *JAMB Guide*\nSend: /jamb UNILAG Computer Science",
        "course": "🎯 *Course Advisor*\nSend: /course I like Biology and Chemistry, what course?",
        "cutoff": "✂️ *Cut-off Checker*\nSend: /cutoff UNILAG Medicine",
        "nysc": "⭐ *NYSC Guide*\nSend: /nysc How do I register for NYSC?",
        "cv": "📄 *CV Builder*\nSend: /cv My name is Ada, 200 level Computer Science, skills: Python. Make CV."
    }
    if not q:
        await update.message.reply_text(examples.get(kind, "Ask me anything!"), parse_mode="Markdown"); return
    await update.message.reply_text("Thinking... 🤔")
    ans = ask_ai(f"{kind} question: {q}")
    await update.message.reply_text(ans)

async def jamb(update: Update, context: ContextTypes.DEFAULT_TYPE): await ai_cmd(update, context, "jamb")
async def course(update: Update, context: ContextTypes.DEFAULT_TYPE): await ai_cmd(update, context, "course")
async def cutoff(update: Update, context: ContextTypes.DEFAULT_TYPE): await ai_cmd(update, context, "cutoff")
async def nysc(update: Update, context: ContextTypes.DEFAULT_TYPE): await ai_cmd(update, context, "nysc")
async def cv(update: Update, context: ContextTypes.DEFAULT_TYPE): await ai_cmd(update, context, "cv")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.startswith("/"): return
    await update.message.reply_text("Thinking... 🤔")
    ans = ask_ai(f"Student asks: {update.message.text}. If this is a handout/note, summarize it to exam questions and answers. If question, answer clearly.")
    await update.message.reply_text(ans)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("refer", refer))
    app.add_handler(CommandHandler("myreferrals", myreferrals))
    app.add_handler(CommandHandler("cgpa", cgpa))
    app.add_handler(CommandHandler("jamb", jamb))
    app.add_handler(CommandHandler("course", course))
    app.add_handler(CommandHandler("cutoff", cutoff))
    app.add_handler(CommandHandler("nysc", nysc))
    app.add_handler(CommandHandler("cv", cv))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("H&S AI HUB Bot is running...")
    app.run_polling()
