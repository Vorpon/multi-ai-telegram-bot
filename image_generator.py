from openai import OpenAI
from config import OPENROUTER_API_KEY
from filter_models import get_vision_models
from rich import print as rprint

def generate_image(prompt):
    """
    Генерирует концепт или возвращает специальный сигнал о необходимости подписки/пополнения.
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    
    available_models = get_vision_models()
    
    if not available_models:
        return "❌ Ошибка: не удалось найти подходящие модели."
        
    selected_model = None
    for model_id in available_models:
        if "gemini" in model_id.lower():
            selected_model = model_id
            break
            
    if not selected_model:
        selected_model = available_models[0]
        
    try:
        response = client.chat.completions.create(
            model=selected_model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Пользователь запросил картинку: '{prompt}'. "
                        "Опиши концепт этого изображения подробно, структурированно и красиво. "
                        "Используй следующие разделы: 1. Основной сюжет, 2. Цветовая палитра, 3. Детали и атмосфера."
                    )
                }
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        error_str = str(e)
        # Если ловим ошибку баланса (402), возвращаем специальный маркер для платной функции
        if "402" in error_str or "balance" in error_str.lower() or "credits" in error_str.lower():
            return "PREMIUM_REQUIRED"
        return f"❌ Произошла ошибка: {error_str}"