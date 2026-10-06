# 1. Базовый образ: официальный python, версия 3.13, вариант slim
FROM python:3.13-slim-trixie
# 2. Установить uv: скопировать его бинарник из официального образа uv
#    (в доке uv это одна строка COPY с флагом --from)
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/
# 3. Рабочая папка, например /app
WORKDIR /app


# 4. Скопировать только pyproject.toml и uv.lock

COPY pyproject.toml .
COPY uv.lock .

# 5. Установить зависимости: uv sync
#    - без dev-зависимостей
#    - строго по lock-файлу, не меняя его
#    - БЕЗ установки самого проекта (кода ещё нет в образе!)

RUN uv sync --locked --no-install-project --no-dev


# 6. Скопировать папку src
COPY  src ./src
COPY README.md ./
# 7. Ещё раз uv sync с теми же флагами, но уже без "без проекта":
#    теперь код на месте, и uv установит сам проект

RUN uv sync --locked --no-dev

# 8. Добавить .venv/bin в PATH, чтобы uvicorn находился без uv run
ENV PATH="/app/.venv/bin:$PATH"

# 9. Создать обычного пользователя и переключиться на него
RUN useradd --system --no-create-home appuser 
USER appuser
# 10. EXPOSE 8000
EXPOSE 8000
# 11. CMD: uvicorn funding_pipeline.api.main:app на хосте 0.0.0.0, порт 8000
#     CMD пишется в виде JSON-списка: ["программа", "аргумент", ...]
CMD ["uvicorn", "funding_pipeline.api.main:app", "--host", "0.0.0.0", "--port", "8000"]