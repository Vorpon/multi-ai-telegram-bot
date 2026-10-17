def route_request(user_input):
    """
    Определяет тип задачи на основе текста пользователя:
    - 'image' -> генерация изображения
    - 'vision' -> анализ загруженной картинки
    - 'text' -> обычный текстовый запрос
    """
    text_lower = user_input.lower()
    
    # Ключевые слова для анализа картинок / фотографий
    vision_keywords = ["картинк", "фото", "анализ", "посмотри", "что на", "скриншот", ".jpg", ".png", ".jpeg"]
    
    # Ключевые слова для генерации изображений
    image_keywords = ["нарисуй", "создай картинку", "сгенерируй рисунок", "нарисуй мне"]
    
    if any(keyword in text_lower for keyword in image_keywords):
        return "image"
    elif any(keyword in text_lower for keyword in vision_keywords):
        return "vision"
    else:
        return "text"