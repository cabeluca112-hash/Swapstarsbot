import sqlite3
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = "7555891461:AAGe6owoQ0pgcfBVY572-ccfnUBgbBGQA4M"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Connect to database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Create tables
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, stars INTEGER DEFAULT 0, referrer INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS withdrawals (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, stars INTEGER, wallet TEXT, status TEXT DEFAULT 'pending')")
conn.commit()

# /start handler with referral
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        referrer = int(args) if args.isdigit() else None
        cursor.execute("INSERT INTO users (user_id, stars, referrer) VALUES (?, 0, ?)", (user_id, referrer))
        conn.commit()
        if referrer:
            cursor.execute("UPDATE users SET stars = stars + 80 WHERE user_id = ?", (referrer,))
            conn.commit()
            await bot.send_message(referrer, f"You earned 80⭐ from a referral!")
    await message.answer("Welcome to SwapStars! Use /balance to check your stars.")

# /balance handler
@dp.message_handler(commands=["balance"])
async def balance(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT stars FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    stars = result[0] if result else 0
    await message.answer(f"⭐ Your balance: {stars} stars")

# /referrals handler
@dp.message_handler(commands=["referrals"])
async def referrals(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT COUNT(*) FROM users WHERE referrer=?", (user_id,))
    count = cursor.fetchone()[0]
    await message.answer(f"You have {count} referrals.")

# /withdraw handler
@dp.message_handler(commands=["withdraw"])
async def withdraw(message: types.Message):
    await message.answer("Send me your TON wallet address:")

    @dp.message_handler()
    async def handle_wallet(msg: types.Message):
        user_id = msg.from_user.id
        wallet = msg.text.strip()
        cursor.execute("SELECT stars FROM users WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
        if result and result[0] >= 1000:
            cursor.execute("INSERT INTO withdrawals (user_id, stars, wallet) VALUES (?, ?, ?)", (user_id, result[0], wallet))
            cursor.execute("UPDATE users SET stars = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            await msg.answer("✅ Withdrawal request submitted! Admin will review it.")
        else:
            await msg.answer("❌ You need at least 1000 stars to withdraw.")
