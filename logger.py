import datetime

def log_interaction(query_type, user_query, model_used, response_text):
    """
    Записывает лог запроса и ответа в файл aggregator.log
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = (
        f"[{timestamp}] ТИП: {query_type.upper()} | МОДЕЛЬ: {model_used}\n"
        f"ЗАПРОС: {user_query}\n"
        f"ОТВЕТ: {response_text}\n"
        + "-" * 50 + "\n"
    )
    
    try:
        with open("aggregator.log", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"⚠️ Не удалось записать лог: {e}")