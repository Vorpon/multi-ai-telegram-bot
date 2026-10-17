import os
from openai import OpenAI
from config import OPENROUTER_API_KEY
from list_AI import get_available_models
from route import route_request
from image_generator import generate_image
from vision_analyzer import analyze_image_with_prompt
from model_selector import choose_model_interactive  # Импортируем выбор моделей
from logger import log_interaction                 # Импортируем логгер
from rich import print as rprint
from rich.panel import Panel

# Инициализируем клиента для текста
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

rprint("[bold green]🤖 AI-аггрегатор запущен и готов к работе![/bold green]")
rprint("[dim]Введите ваш вопрос, задачу или команду [/dim][bold cyan]/model[/bold cyan][dim] для выбора модели (для выхода — 'выход'):[/dim]\n")

# История диалога для текстовых запросов
chat_history = [
    {"role": "system", "content": "Ты — полезный и умный AI-ассистент, встроенный в терминальный мультимодальный агрегатор."}
]

# Переменная для принудительно выбранной пользователем модели (по умолчанию авто)
forced_model = None

while True:
    user_input = input("Вы: ")
    
    if user_input.lower() in ["выход", "exit", "quit"]:
        rprint("[yellow]До свидания! Возвращайтесь.[/yellow]")
        break
        
    if not user_input.strip():
        continue

    # Спец-команда для вызова интерактивного меню моделей
    if user_input.strip().lower() == "/model":
        all_models = get_available_models()
        forced_model = choose_model_interactive(all_models)
        continue

    # 1. Определяем тип запроса через роутер
    request_type = route_request(user_input)
    rprint(f"[dim][Роутер]: задача определена как {request_type.upper()}[/dim]")

    # ВЕТКА 1: Генерация / концепт изображения
    if request_type == "image":
        rprint("[cyan]👉 Направляем задачу на создание концепта изображения...[/cyan]")
        result = generate_image(user_input)
        print(result)
        
        # Записываем в лог
        log_interaction("image", user_input, "flux/concept", result)
        print("-" * 40 + "\n")
        
    # ВЕТКА 2: Анализ изображения (Vision)
    elif request_type == "vision":
        rprint("[cyan]👉 Запрос на анализ изображения. Пожалуйста, укажите путь к файлу картинки:[/cyan]")
        image_path = input("Путь к файлу: ").strip()
        image_path = image_path.strip('"').strip("'")
        
        if not os.path.exists(image_path):
            rprint(f"[bold red]❌ Ошибка: файл по пути '{image_path}' не найден.[/bold red]\n")
            continue
            
        rprint("[dim]ℹ️ [Система]: Запускаем анализ изображения...[/dim]")
        analysis_result = analyze_image_with_prompt(image_path, user_input)
        
        panel = Panel(
            analysis_result,
            title="[bold magenta]👁️ РЕЗУЛЬТАТ АНАЛИЗА ИЗОБРАЖЕНИЯ[/bold magenta]",
            border_style="magenta",
            expand=False
        )
        rprint(panel)
        
        # Записываем в лог
        log_interaction("vision", f"{user_input} [file: {image_path}]", "multimodal-vision", analysis_result)
        print("\n" + "-" * 40 + "\n")
        
    # ВЕТКА 3: Обычный текст
    else:
        rprint("[cyan]👉 Направляем задачу на текстовую модель...[/cyan]")
        
        # Если модель не выбрана вручную через /model, ищем автоматически
        if forced_model:
            selected_model = forced_model
            rprint(f"[dim][Система]: используется выбранная модель -> {selected_model}[/dim]")
        else:
            models = get_available_models()
            selected_model = None
            if models:
                for m in models:
                    if "moondream" not in m and ("chat" in m or "instruct" in m or "free" in m):
                        selected_model = m
                        break
                if not selected_model:
                    selected_model = models[0]
            else:
                selected_model = "deepseek/deepseek-chat"
                
            rprint(f"[dim][Система]: авто-выбор модели -> {selected_model}[/dim]")
            
        try:
            chat_history.append({"role": "user", "content": user_input})
            
            completion = client.chat.completions.create(
                model=selected_model,
                messages=chat_history,
                max_tokens=1500
            )
            
            assistant_response = completion.choices[0].message.content
            chat_history.append({"role": "assistant", "content": assistant_response})
            
            print("\n--- ОТВЕТ ОТ НЕЙРОСЕТИ ---")
            print(assistant_response)
            print("--------------------------\n")
            
            # Записываем взаимодействие в лог-файл aggregator.log
            log_interaction("text", user_input, selected_model, assistant_response)
            
        except Exception as e:
            rprint(f"[bold red]❌ Произошла ошибка при запросе: {e}[/bold red]\n")