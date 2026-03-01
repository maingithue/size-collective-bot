import sqlite3
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

TOKEN = "8577067310:AAHvTEeHmefpUa25c-5Osz_kjCQVaagsX6M"

logging.basicConfig(level=logging.INFO)

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sizes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase TEXT,
    section TEXT,
    brigadier TEXT,
    width REAL,
    height REAL
)
""")
conn.commit()

BRIGADIERS = {
    "Ануар": "1122",
    "Тимур": "2233",
    "Николай": "3344",
    "Найм": "4455",
    "Рауан": "5566",
    "Дильмурат": "6677",
    "Даурен": "7788",
    "Адай": "8899",
    "Женис": "9900",
}

WATCHER_PASSWORD = "0000"

PHASES = {
    "Фаза 5": ["23","26","78","79","80"],
    "Фаза 3": ["34","35","36"],
    "Фаза 1": ["TSB","D-block","T-block"]
}

ROLE, NAME, PASSWORD, PHASE, SECTION, SIZE = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Бригадир"], ["Кесуші"], ["Бақылаушы"]]
    await update.message.reply_text(
        "Роль таңдаңыз:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return ROLE

async def role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data["role"] = text

    if text == "Бригадир":
        await update.message.reply_text("Атыңызды енгізіңіз:")
        return NAME
    elif text == "Бақылаушы":
        await update.message.reply_text("Пароль енгізіңіз:")
        return PASSWORD
    else:
        return await show_phases(update, context)

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in BRIGADIERS:
        context.user_data["name"] = text
        await update.message.reply_text("Пароль енгізіңіз:")
        return PASSWORD
    else:
        await update.message.reply_text("Мұндай бригадир жоқ!")
        return NAME

async def password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    role = context.user_data.get("role")

    if role == "Бригадир":
        if BRIGADIERS.get(context.user_data.get("name")) == text:
            return await show_phases(update, context)
        else:
            await update.message.reply_text("Қате пароль!")
            return PASSWORD

    if role == "Бақылаушы":
        if text == WATCHER_PASSWORD:
            return await show_stats(update, context)
        else:
            await update.message.reply_text("Қате пароль!")
            return PASSWORD

async def show_phases(update, context):
    keyboard = [[p] for p in PHASES.keys()]
    await update.message.reply_text(
        "Фаза таңдаңыз:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return PHASE

async def phase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phase"] = update.message.text
    keyboard = [[s] for s in PHASES[update.message.text]]
    await update.message.reply_text(
        "Участок таңдаңыз:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return SECTION

async def section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["section"] = update.message.text
    await update.message.reply_text("Размер енгізіңіз (80x75, 80x53):")
    return SIZE

async def size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    sizes = text.replace("\n", ",").split(",")

    total = 0
    for s in sizes:
        s = s.strip()
        if "x" in s:
            w, h = s.split("x")
            area = (float(w) * float(h)) / 10000
            total += area
            cursor.execute(
                "INSERT INTO sizes (phase, section, brigadier, width, height) VALUES (?,?,?,?,?)",
                (
                    context.user_data["phase"],
                    context.user_data["section"],
                    context.user_data.get("name",""),
                    float(w),
                    float(h),
                ),
            )
    conn.commit()
    await update.message.reply_text(f"Қосылды: {round(total,2)} м²")
    return SIZE

async def show_stats(update, context):
    cursor.execute("SELECT phase, section, COUNT(*) FROM sizes GROUP BY phase, section")
    rows = cursor.fetchall()
    text = "Статистика:\n"
    for r in rows:
        text += f"{r[0]} - {r[1]} : {r[2]} фасад\n"
    await update.message.reply_text(text)
    return ConversationHandler.END

app = ApplicationBuilder().token(TOKEN).build()

conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, role)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
        PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password)],
        PHASE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phase)],
        SECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, section)],
        SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, size)],
    },
    fallbacks=[],
)

app.add_handler(conv)
app.run_polling()
