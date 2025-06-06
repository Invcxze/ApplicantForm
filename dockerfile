FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl libpq-dev build-essential

RUN curl --proto '=https' --tlsv1.2 -LsSf https://github.com/astral-sh/uv/releases/download/0.7.8/uv-installer.sh | sh

ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app/src

COPY pyproject.toml uv.lock ./

RUN uv sync

COPY . .

EXPOSE 8028
CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8028"]
