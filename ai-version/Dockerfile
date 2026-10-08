FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install fastapi uvicorn psycopg2-binary python-dotenv

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
