"""Helper script to create .env file."""
import os

lines = [
    "# LuminaLib Environment Configuration",
    "APP_NAME=LuminaLib",
    "APP_VERSION=1.0.0",
    "APP_ENV=development",
    "DEBUG=true",
    "HOST=0.0.0.0",
    "PORT=8000",
    "POSTGRES_USER=luminalib",
    "POSTGRES_PASSWORD=luminalib_secret",
    "POSTGRES_DB=luminalib",
    "POSTGRES_HOST=db",
    "POSTGRES_PORT=5432",
    "DATABASE_URL=postgresql+asyncpg://luminalib:luminalib_secret@db:5432/luminalib",
    "JWT_SECRET_KEY=change-me-to-a-long-random-string-in-production",
    "JWT_ALGORITHM=HS256",
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60",
    "STORAGE_BACKEND=local",
    "LOCAL_STORAGE_PATH=/app/storage/books",
    "S3_ENDPOINT_URL=http://minio:9000",
    "S3_ACCESS_KEY=minioadmin",
    "S3_SECRET_KEY=minioadmin",
    "S3_BUCKET_NAME=luminalib-books",
    "S3_REGION=us-east-1",
    "LLM_PROVIDER=ollama",
    "OLLAMA_BASE_URL=http://ollama:11434",
    "OLLAMA_MODEL=llama3",
    "OPENAI_API_KEY=sk-change-me",
    "OPENAI_MODEL=gpt-4o-mini",
    "CELERY_BROKER_URL=redis://redis:6379/0",
    "CELERY_RESULT_BACKEND=redis://redis:6379/0",
    "RECOMMENDATION_MIN_BORROWS=1",
    "RECOMMENDATION_TOP_N=10",
]

base = os.path.dirname(os.path.abspath(__file__))
content = "\n".join(lines) + "\n"
for fname in [".env", ".env.example"]:
    path = os.path.join(base, fname)
    with open(path, "w") as f:
        f.write(content)
    print(f"Created {path}")
