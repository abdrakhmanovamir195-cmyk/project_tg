"""
Семантический поиск фильмов по описанию с использованием эмбеддингов
Использует модель sentence-transformers (intfloat/multilingual-e5-small) и FAISS для быстрого поиска
"""

import os
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Отключаем попытки подключения к интернету для загрузки модели
os.environ["HF_HUB_OFFLINE"] = "1"


class SemanticMovieFinder:
    """
    Класс для поиска фильмов по описанию сюжета
    """

    def __init__(self):
        """Инициализация — загружаем модель для создания эмбеддингов"""
        print("🚀 Загрузка модели sentence-transformers...")

        # Загружаем модель ТОЛЬКО локально (из кэша)
        self.model = SentenceTransformer(
            'intfloat/multilingual-e5-small',
            local_files_only=True
        )

        print("✅ Модель загружена")

        self.df = None
        self.index = None
        self.embeddings = None

    def load_data(self, path="data/tmdb_5000_movies.csv"):
        """
        Загрузка датасета с фильмами

        Args:
            path: путь к CSV файлу с фильмами
        """
        print(f"📀 Загрузка данных из {path}...")
        self.df = pd.read_csv(path)

        # Оставляем нужные колонки
        self.df = self.df[['title', 'overview', 'genres']].copy()

        # Удаляем фильмы без описания
        before = len(self.df)
        self.df = self.df.dropna(subset=['overview'])
        after = len(self.df)

        print(f"✅ Загружено {after} фильмов (удалено {before - after} без описания)")

        # Очищаем текст (убираем лишние символы, приводим к нижнему регистру)
        self.df['overview'] = self.df['overview'].astype(str).str.lower()
        self.df['overview'] = self.df['overview'].str.replace(r'[^\w\s]', ' ', regex=True)

        return self.df

    def build_index(self, save_path="models/"):
        """
        Создание FAISS индекса для быстрого поиска

        Args:
            save_path: путь для сохранения модели
        """
        print("🔨 Создание эмбеддингов для всех фильмов...")

        # Получаем все описания
        descriptions = self.df['overview'].tolist()

        # Создаем эмбеддинги
        self.embeddings = self.model.encode(
            descriptions,
            show_progress_bar=True,
            batch_size=32
        )

        # Нормализуем эмбеддинги (для косинусной схожести)
        faiss.normalize_L2(self.embeddings)

        # Создаем FAISS индекс
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # IP = inner product (косинусная схожесть)
        self.index.add(self.embeddings.astype('float32'))

        print(f"✅ Индекс создан: {self.index.ntotal} векторов, размерность {dimension}")

        # Сохраняем модель
        os.makedirs(save_path, exist_ok=True)

        # Сохраняем FAISS индекс
        faiss.write_index(self.index, f"{save_path}/movie_index.faiss")

        # Сохраняем данные фильмов
        self.df.to_csv(f"{save_path}/movies_data.csv", index=False)

        # Сохраняем эмбеддинги
        np.save(f"{save_path}/embeddings.npy", self.embeddings)

        print(f"💾 Модель сохранена в {save_path}")

    def load_index(self, path="models/"):
        """
        Загрузка сохраненного индекса

        Args:
            path: путь к сохраненной модели
        """
        print("📂 Загрузка сохраненной модели...")

        # Загружаем FAISS индекс
        self.index = faiss.read_index(f"{path}/movie_index.faiss")

        # Загружаем данные фильмов
        self.df = pd.read_csv(f"{path}/movies_data.csv")

        # Загружаем эмбеддинги
        self.embeddings = np.load(f"{path}/embeddings.npy")

        print(f"✅ Модель загружена: {self.index.ntotal} фильмов")

    def search(self, query, top_k=5):
        """
        Поиск фильмов по описанию

        Args:
        query: текст запроса (описание сцены)
                    top_k: количество результатов

                Returns:
                    list: список найденных фильмов с оценками
                """
        # Создаем эмбеддинг запроса
        query_embedding = self.model.encode([query])

        # Нормализуем
        faiss.normalize_L2(query_embedding)

        # Ищем ближайшие фильмы
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)

        # Формируем результаты
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.df) and scores[0][i] > 0:
                results.append({
                    'title': self.df.iloc[idx]['title'],
                    'overview': self.df.iloc[idx]['overview'][:300],
                    'genres': self.df.iloc[idx]['genres'][:100] if pd.notna(self.df.iloc[idx]['genres']) else "",
                    'score': float(scores[0][i]),
                    'score_percent': round(float(scores[0][i]) * 100, 1)
                })

        return results

    # Если запускаем файл напрямую — тестируем
    if __name__ == "__main__":
        print("=" * 50)
        print("ТЕСТИРОВАНИЕ МОДЕЛИ ПОИСКА ФИЛЬМОВ")
        print("=" * 50)

        # Создаем экземпляр поисковика
        finder = SemanticMovieFinder()

        # Загружаем данные
        finder.load_data()

        # Создаем индекс
        finder.build_index()

        # Тестовые запросы
        test_queries = [
            "парень бежит по кукурузному полю",
            "space travel black hole",
            "мальчик видит мертвых людей"
        ]

        for query in test_queries:
            print(f"\n🔍 ЗАПРОС: {query}")
            print("-" * 40)

            results = finder.search(query, top_k=3)

            for i, movie in enumerate(results, 1):
                print(f"{i}. {movie['title']}")
                print(f"   Схожесть: {movie['score_percent']}%")
                print()

        print("=" * 50)
        print("✅ Тестирование завершено")