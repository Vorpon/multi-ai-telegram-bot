from openai import OpenAI
from config import OPENROUTER_API_KEY

def get_available_models():
    """Функция запрашивает и возвращает список доступных моделей"""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    
    try:
        models_response = client.models.list()
        # Собираем все ID моделей в список
        models_list = [model.id for model in models_response.data]
        return models_list
    except Exception as e:
        print(f"Ошибка при получении списка моделей: {e}")
        return []