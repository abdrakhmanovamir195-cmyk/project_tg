import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from semantic_search import SemanticMovieFinder

# --- 1. Настройки ---
# Отключаем информационные логи, оставляем только ошибки
logging.basicConfig(level=logging.WARNING)

# Загружаем токен бота из файла .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# --- 2. Данные твоего SOCKS5 прокси ---
PROXY_URL = 'socks5://206.123.156.207:5937'

# --- 3. Загрузка модели поиска фильмов ---
print("🚀 Загрузка модели...")
movie_finder = SemanticMovieFinder()
movie_finder.load_index("models/")
print(f"✅ Загружено {len(movie_finder.df)} фильмов")


# --- 4. Определение функций-обработчиков команд бота ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ответ на команду /start"""
    await update.message.reply_text(
        "🎬 *Movie Search Bot*\n\n"
        "Send me a scene description, and I'll find the movie!\n\n"
        "*Examples:*\n"
        "• `a boy sees dead people`\n"
        "• `a man runs through a cornfield`\n"
        "• `space travel through a black hole`\n\n"
        "*Commands:*\n"
        "/start — this message\n"
        "/help — help\n"
        "/about — about the bot",
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ответ на команду /help"""
    await update.message.reply_text(
        "📖 *How to use:*\n\n"
        "1. Send a description of a scene or plot\n"
        "2. The bot will return top 5 matching movies\n"
        "3. The more details, the better the result\n\n"
        "*Tip:* Write in English for best results.\n\n"
        "*Commands:*\n"
        "/start — welcome\n"
        "/help — this help\n"
        "/about — about the bot",
        parse_mode='Markdown'
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ответ на команду /about"""
    await update.message.reply_text(
        "🤖 *About this bot*\n\n"
        "This bot searches for movies by plot description.\n\n"
        "*Technology:*\n"
        "• Sentence Transformers (multilingual-e5-small)\n"
        "• FAISS for fast similarity search\n"
        "• Telegram Bot API\n\n"
        "*How it works:*\n"
        "1. All movie descriptions (4800+) are converted to vectors\n"
        "2. Your query is also converted to a vector\n"
        "3. The system finds the most similar movies\n\n"
        "*Dataset:* TMDB 5000 Movies\n\n"
        "© 2025 Educational Project",
        parse_mode='Markdown'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений (поиск фильма)"""
    query = update.message.text
    print(f"🔍 Search query: {query}")

    # Показываем, что бот печатает
    await update.message.chat.send_action(action="typing")

    try:
        # Ищем топ-5 фильмов
        results = movie_finder.search(query, top_k=5)

        if not results:
            await update.message.reply_text("😕 Nothing found. Try rephrasing your query.")
            return

        # Формируем ответ
        response = "🎬 *Search results:*\n\n"
        for i, movie in enumerate(results, 1):
            # Выбираем эмодзи в зависимости от процента схожести
            score = movie['score_percent']
            if score > 70:
                emoji = "🔥"
            elif score > 50:
                emoji = "👍"
            else:
                emoji = "📌"

            response += f"{emoji} *{i}. {movie['title']}* — *{score}%*\n"
            response += f"   _{movie['overview'][:100]}..._\n\n"

        response += "\n💡 *Tip:* Add more details to get better results!"
        await update.message.reply_text(response, parse_mode='Markdown')

    except Exception as e:
        print(f"❌ Error during search: {e}")
        await update.message.reply_text("⚠️ An error occurred. Please try again later.")


# --- 5. Запуск бота ---
print("🤖 Starting bot...")
# Создаем приложение с использованием прокси
app = Application.builder() \
    .token(TOKEN) \
    .proxy(PROXY_URL) \
    .get_updates_proxy(PROXY_URL) \
    .build()

# Регистрируем обработчики команд
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("about", about))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("✅ Bot is running. Press Ctrl+C to stop.")
app.run_polling()