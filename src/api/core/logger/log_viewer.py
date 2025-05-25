import streamlit as st
import pandas as pd
from pathlib import Path

def start_viewer():
    st.set_page_config(page_title="Лог-файлы", layout="wide")

    log_dir = Path(__file__).resolve().parent.parent / "loger/logs"
    log_file = log_dir / "debug.log"

    def load_logs():
        log_data = []
        if log_file.exists():
            with log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(" - ", maxsplit=4)

                    # Обработка строк с количеством частей, не равным 5
                    if len(parts) == 5:
                        timestamp, logger, level, message, location = parts

                        # Фильтрация строк с чувствительной информацией
                        if "access_token" in message or "token" in message:
                            message = "[TOKEN REDACTED]"

                        # Обработка ошибок SQL
                        if "OperationalError" in message:
                            message = "[SQL ERROR REDACTED]"

                        # Обработка ошибок валидации данных
                        if "validation errors" in message:
                            message = "[VALIDATION ERROR REDACTED]"

                        log_data.append([timestamp, level, message, location])
                    else:
                        st.warning(f"Строка лога не соответствует ожидаемому формату: {line}")
        else:
            st.warning(f"Файл {log_file} не найден.")
        return pd.DataFrame(log_data, columns=["Дата", "Уровень", "Сообщение", "Файл"])

    df = load_logs()

    if df.empty:
        st.info("Логи не загружены или файл пуст.")
    else:
        st.write("Загруженные данные:")
        st.write(df.head())  # Вывод первых строк для проверки структуры

    st.title("Просмотр логов 📜")

    log_levels = df["Уровень"].unique().tolist() if not df.empty else []
    selected_levels = st.multiselect("Фильтр по уровню:", log_levels, default=log_levels)

    filtered_df = df[df["Уровень"].isin(selected_levels)] if not df.empty else pd.DataFrame()

    # Подсветка по уровням (изменение цвета текста)
    def highlight_level(val):
        if val == 'CRITICAL':
            return 'color: purple'
        elif val == 'ERROR':
            return 'color: red'
        elif val == 'WARNING':
            return 'color: orange'
        elif val == 'INFO':
            return 'color: green'
        elif val == 'DEBUG':
            return 'color: white'
        return ''

    # Применяем стили к столбцу "Уровень"
    if not filtered_df.empty:
        styled_df = filtered_df.style.applymap(highlight_level, subset=["Уровень"])

        st.dataframe(styled_df, height=600)
    else:
        st.info("Нет данных для отображения по выбранному фильтру.")

    if st.button("🔄 Обновить логи"):
        st.cache_data.clear()  # Очистить кеш
        st.info("Для обновления страницы нажмите F5 или перезагрузите страницу вручную.")

if __name__ == "__main__":
    start_viewer()
