from openai import OpenAI
from config import OPENROUTER_API_KEY

def get_vision_models():
    """
    Получает и фильтрует список моделей с OpenRouter,
    оставляя только те, что могут работать с изображениями (vision).
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    
    try:
        print("[Система]: Запрашиваем список моделей для анализа изображений...")
        models_response = client.models.list()
        
        # Список ключевых слов, указывающих, что модель умеет работать с картинками
        image_keywords = ["vision", "image", "moondream", "llava", "gpt-4o"]
        
        vision_models = []
        for model in models_response.data:
            m_id = model.id.lower()
            # Если в ID есть ключевое слово, добавляем модель в список
            if any(keyword in m_id for keyword in image_keywords):
                vision_models.append(model.id)
                
        # Для теста выведем первые 5 найденных моделей в консоль
        if vision_models:
            print(f"[Система]: Найдено vision-моделей: {len(vision_models)}")
            for i, model_id in enumerate(vision_models[:5]):
                print(f"  {i+1}. {model_id}")
            return vision_models
        else:
            print("[Система]: Vision-модели не найдены.")
            return []

    except Exception as e:
        print(f"❌ Ошибка при получении списка vision-моделей: {e}")
        return []