import sqlite3
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

TOKEN = "8577067310:AAHvTEeHmefpUa25c-5Osz_kjCQVaagsX6M"

logging.basicConfig(level=logging.INFO)

# --- DATABASE ---
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    role TEXT,
    name TEXT
)
""")

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
    "Фаза 5": ["23","26","78","79","80","41","42","43","44","45","46","47","48","49","50","51","52","53","105","104","106","103","102","101","100","99","98","97","112","111","110","109","108","107"],
    "Фаза 3": ["34","35","36","37","38","39","40","41","42","43","44","45","46","47","48"],
    "Фаза 1": ["TSB","D-block","T-block"]
}

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Бригадир"], ["Кесуші"], ["Бақылаушы"]]
    await update.message.reply_text(
        "Роль таңдаңыз / Выберите роль",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )

# --- ROLE SELECT ---
async def role_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = update.message.text
    context.user_data["role"] = role
    
    if role == "Бригадир":
        await update.message.reply_text("Атыңызды енгізіңіз:")
    elif role == "Бақылаушы":
        await update.message.reply_text("Пароль енгізіңіз:")
    else:
        await show_phases(update, context)

# --- NAME CHECK ---
async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    if name in BRIGADIERS:
        context.user_data["name"] = name
        await update.message.reply_text("Пароль енгізіңіз:")
    else:
        await update.message.reply_text("Мұндай бригадир жоқ!")

# --- PASSWORD CHECK ---
async def password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    role = context.user_data.get("role")

    if role == "Бригадир":
        name = context.user_data.get("name")
        if BRIGADIERS.get(name) == password:
            await show_phases(update, context)
        else:
            await update.message.reply_text("Қате пароль!")
    elif role == "Бақылаушы":
        if password == WATCHER_PASSWORD:
            await show_stats(update, context)
        else:
            await update.message.reply_text("Қате пароль!")

# --- SHOW PHASES ---
async def show_phases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[phase] for phase in PHASES.keys()]
    await update.message.reply_text(
        "Фаза таңдаңыз:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )

# --- PHASE SELECT ---
async def phase_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phase = update.message.text
    context.user_data["phase"] = phase
    sections = PHASES.get(phase, [])
    keyboard = [[s] for s in sections]
    await update.message.reply_text(
        "Участок таңдаңыз:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )

# --- SECTION SELECT ---
async def section_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["section"] = update.message.text
    await update.message.reply_text("Размерлерді енгізіңіз (мысалы: 80x75, 80x53):")

# --- SIZE INPUT ---
async def size_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                    context.user_data.get("phase"),
                    context.user_data.get("section"),
                    context.user_data.get("name"),
                    float(w),
                    float(h),
                ),
            )
    conn.commit()
    await update.message.reply_text(f"Жалпы қосылды: {round(total,2)} м²")

# --- STATS ---
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT phase, section, COUNT(*) FROM sizes GROUP BY phase, section")
    rows = cursor.fetchall()
    text = "Статистика:\n"
    for r in rows:
        text += f"{r[0]} - {r[1]} : {r[2]} фасад\n"
    await update.message.reply_text(text)

# --- MAIN ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, role_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, password_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, phase_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, section_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, size_handler))

app.run_polling()
