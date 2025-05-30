FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl libpq-dev build-essential

RUN curl --proto '=https' --tlsv1.2 -LsSf https://github.com/astral-sh/uv/releases/download/0.7.8/uv-installer.sh | sh

ENV PATH="/root/.local/bin:${PATH}"
RUN ls -l /app/src
WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync

COPY . .

WORKDIR /app/src

EXPOSE 8028
CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8028"]
RUN ls -la /app/src