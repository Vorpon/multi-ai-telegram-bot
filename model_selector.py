from rich import print as rprint
from rich.table import Table

def choose_model_interactive(models_list):
    """
    Фильтрует список, убирая служебные и пакетные модели, 
    и выводит интерактивную табличку доступных моделей в терминале.
    """
    if not models_list:
        rprint("[red]❌ Список моделей пуст.[/red]")
        return None

    # Убираем batch, embed, а также узкие утилиты (summarize, extract)
    filtered_models = [
        m for m in models_list 
        if ":batch" not in m.lower() 
        and "embed" not in m.lower() 
        and "summarize" not in m.lower() 
        and "extract" not in m.lower()
    ]

    rprint("\n[bold cyan]📋 ДОСТУПНЫЕ ИНТЕРАКТИВНЫЕ МОДЕЛИ:[/bold cyan]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("№", style="dim", width=4)
    table.add_column("ID Модели", style="green")

    display_models = filtered_models[:15]
    for idx, model_id in enumerate(display_models, 1):
        table.add_row(str(idx), model_id)

    rprint(table)
    rprint("[dim]0. Оставить автоматический выбор[/dim]")
    
    choice = input("\nВведите номер модели для ручного переключения (или нажмите Enter для авто): ").strip()
    
    if choice.isdigit():
        idx = int(choice)
        if idx == 0:
            return None
        if 1 <= idx <= len(display_models):
            selected = display_models[idx - 1]
            rprint(f"[green]✔ Принудительно выбрана модель: {selected}[/green]\n")
            return selected
            
    rprint("[yellow]ℹ️ Продолжаем с автоматическим выбором модели.[/yellow]\n")
    return None