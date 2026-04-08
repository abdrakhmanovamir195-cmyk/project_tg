from semantic_search import SemanticMovieFinder

print("1. Создаём экземпляр...")
finder = SemanticMovieFinder()

print("2. Загружаем индекс...")
finder.load_index("models/")

print(f"3. Успех! Загружено {len(finder.df)} фильмов")
print("4. Проверяем поиск...")
results = finder.search("мальчик видит мертвых людей", top_k=1)
print(f"5. Результат: {results[0]['title']} — {results[0]['score_percent']}%")