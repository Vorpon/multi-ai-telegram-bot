import base64
from openai import OpenAI
from config import OPENROUTER_API_KEY
from filter_models import get_vision_models
from rich import print as rprint

def encode_image_to_base64(image_path):
    """Кодирует локальное изображение в формат base64 для отправки в API"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return None

def analyze_image_with_prompt(image_path, user_prompt):
    """
    Отправляет изображение и текстовый промт мультимодальной модели через OpenRouter.
    """
    # Правильное кодирование в base64
    try:
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        return f"❌ Не удалось открыть файл изображения по пути: {image_path}. Ошибка: {e}"

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    
    # Получаем список vision-моделей
    available_models = get_vision_models()
    
    selected_model = None
    for model_id in available_models:
        if "gemini" in model_id.lower() or "flash" in model_id.lower():
            selected_model = model_id
            break
            
    if not selected_model and available_models:
        selected_model = available_models[0]
    elif not selected_model:
        selected_model = "google/gemini-2.5-flash" # Резервный надежный вариант
        
    rprint(f"[dim]ℹ️ [Система]: Используем мультимодальную модель -> {selected_model}[/dim]")
    
    try:
        response = client.chat.completions.create(
            model=selected_model,
            max_tokens=1500, # <-- Ограничиваем аппетиты модели, чтобы укладываться в лимиты бесплатного баланса!
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": user_prompt if user_prompt else "Опиши подробно, что изображено на этой картинке."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )
        
        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Ошибка при анализе изображения моделью: {e}"