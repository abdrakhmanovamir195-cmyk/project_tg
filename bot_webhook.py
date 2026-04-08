import os
import logging
from flask import Flask, request, jsonify
from semantic_search import SemanticMovieFinder

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

print("🚀 Загрузка модели...")
movie_finder = SemanticMovieFinder()
movie_finder.load_index("models/")
print(f"✅ Загружено {len(movie_finder.df)} фильмов")

def send_telegram_message(chat_id, text, parse_mode='Markdown'):
    import requests
    token = os.environ.get('BOT_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка: {e}")

@app.route(f'/webhook/{os.environ.get("BOT_TOKEN")}', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        if not update or 'message' not in update:
            return jsonify({'status': 'ok'}), 200
        message = update['message']
        chat_id = message['chat']['id']
        user_text = message.get('text')
        if not user_text:
            return jsonify({'status': 'ok'}), 200
        if user_text == '/start':
            response_text = "🎬 Бот работает! Отправь описание сцены."
        else:
            results = movie_finder.search(user_text, top_k=5)
            if not results:
                response_text = "😕 Ничего не найдено."
            else:
                response_text = "🎬 *Результаты:*\n\n"
                for i, movie in enumerate(results, 1):
                    response_text += f"{i}. *{movie['title']}* — *{movie['score_percent']}%*\n"
        send_telegram_message(chat_id, response_text)
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/')
def index():
    return "Bot is running!"