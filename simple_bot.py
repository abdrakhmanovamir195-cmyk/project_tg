import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from semantic_search import SemanticMovieFinder

# --- 1. НАСТРОЙКИ ---
logging.basicConfig(level=logging.WARNING)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# --- ПРОКСИ (вписан прямо в код) ---
os.environ["ALL_PROXY"] = "socks5://185.245.41.242:1080"

# --- 2. ЗАГРУЗКА МОДЕЛИ ---
print("🚀 Загрузка модели...")
movie_finder = SemanticMovieFinder()
movie_finder.load_index("models/")
print(f"✅ Загружено {len(movie_finder.df)} фильмов")

# --- 3. ФУНКЦИИ БОТА ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Movie Search Bot*\n\n"
        "Просто напиши описание сцены, и я найду фильм!\n\n"
        "*Примеры:*\n"
        "• `мальчик видит мертвых людей`\n"
        "• `a man runs through a cornfield`",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Как пользоваться:*\n\n"
        "1. Напиши описание сцены\n"
        "2. Бот найдёт 5 похожих фильмов",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    print(f"🔍 Поиск: {query}")

    await update.message.chat.send_action(action="typing")

    try:
        results = movie_finder.search(query, top_k=5)

        if not results:
            await update.message.reply_text("😕 Ничего не найдено.")
            return

        response = "🎬 *Результаты:*\n\n"
        for i, movie in enumerate(results, 1):
            response += f"{i}. *{movie['title']}* — *{movie['score_percent']}%*\n"
            response += f"   _{movie['overview'][:100]}..._\n\n"

        await update.message.reply_text(response, parse_mode='Markdown')

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        await update.message.reply_text("⚠️ Ошибка. Попробуй позже.")

# --- 4. ЗАПУСК БОТА ---
print("🤖 Запуск бота...")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("✅ Бот запущен. Нажми Ctrl+C для остановки.")
app.run_polling()