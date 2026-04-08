"""
Telegram-бот для поиска фильмов по описанию
"""

import os
import sys
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Добавляем родительскую папку в путь, чтобы импортировать нашу модель
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from semantic_search import SemanticMovieFinder

# Загружаем токен из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в файле .env")
    print("Создай файл .env и добавь строку: BOT_TOKEN=твой_токен")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальная переменная для модели
movie_finder = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_message = """
🎬 *Кино Поиск — бот для поиска фильмов по описанию!*

Я помогу тебе найти фильм, даже если ты не помнишь название.
Просто опиши сцену или сюжет, который запомнил.

*Примеры запросов:*
• парень бежит по кукурузному полю
• путешествие в космосе через черную дыру
• мальчик видит мертвых людей

*Команды:*
/start — показать это сообщение
/help — помощь
/about — о боте

Попробуй описать что-нибудь! 🎬
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📖 *Как пользоваться ботом:*

1. Просто отправь текстовое описание сцены или сюжета
2. Бот найдет топ-5 наиболее подходящих фильмов
3. Чем подробнее описание, тем точнее результат

*Советы:*
• Указывай ключевые детали (место действия, особые приметы)
• Пиши на русском или английском — бот понимает оба языка

*Примеры:*
• человек в железном костюме летает
• a man runs through a cornfield

*Команды:*
/start — приветствие
/help — эта справка
/about — о технологиях
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /about"""
    about_text = """
🤖 *О боте*

Это учебный проект по поиску фильмов по описанию сюжета.

*Технологии:*
• Sentence Transformers (multilingual-e5-small)
• FAISS для быстрого поиска
• Telegram Bot API

*Как работает:*
1. Все описания фильмов (4800+) преобразованы в векторы
2. Ваш запрос также преобразуется в вектор
3. Система находит самые похожие фильмы

*Датасет:* TMDB 5000 Movies

© 2025 Учебный проект
    """
    await update.message.reply_text(about_text, parse_mode='Markdown')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений — поиск фильмов"""
    query = update.message.text
    user = update.effective_user

    logger.info(f"Запрос от {user.username}: {query[:50]}")

    # Показываем, что бот печатает
    await update.message.chat.send_action(action="typing")

    # Отправляем сообщение о начале поиска
    searching_msg = await update.message.reply_text(
        f"🔍 Ищу фильмы по запросу: *{query[:50]}*...",
        parse_mode='Markdown'
    )

    try:
        # Ищем фильмы
        results = movie_finder.search(query, top_k=5)

        if not results:
            await searching_msg.edit_text(
                "😕 *Ничего не найдено*\n\n"
                "Попробуй переформулировать запрос или добавить больше деталей.\n\n"
                "💡 *Пример:* `мальчик видит мертвых людей`",
                parse_mode='Markdown'
            )
            return

        # Форматируем результаты
        response = "🎬 *Результаты поиска:*\n\n"

        for i, movie in enumerate(results, 1):
            score = movie['score_percent']
            if score > 70:
                emoji = "🔥"
            elif score > 50:
                emoji = "👍"
            elif score > 30:
                emoji = "🤔"
            else:
                emoji = "📌"

            response += f"{emoji} *{i}. {movie['title']}*\n"
            response += f"   📊 Схожесть: {score}%\n"
            response += f"   📝 {movie['overview'][:100]}...\n\n"

        await searching_msg.edit_text(response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        await searching_msg.edit_text(
            "⚠️ *Произошла ошибка*\n\nПожалуйста, попробуй позже.",
            parse_mode='Markdown'
        )


def main():
    """Запуск бота"""
    global movie_finder

    print("=" * 50)
    print("🤖 ЗАПУСК TELEGRAM-БОТА")
    print("=" * 50)

    # Загружаем модель
    print("🚀 Загрузка модели поиска...")
    movie_finder = SemanticMovieFinder()

    try:
        movie_finder.load_index("models/")
        print(f"✅ Модель загружена из индекса")
    except:
        print("⚠️ Индекс не найден, создаю заново...")
        movie_finder.load_data()
        movie_finder.build_index()

    print(f"✅ Загружено {len(movie_finder.df)} фильмов")

    # Создаем и запускаем бота
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен! Нажми Ctrl+C для остановки")
    print("=" * 50)

    app.run_polling()


if __name__ == "__main__":
    main()