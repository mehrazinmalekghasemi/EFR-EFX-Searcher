FROM python:3.12-slim
WORKDIR /app
COPY instance.py fast_search.py main.py ./
CMD ["python", "main.py", "--all", "--workers", "1"]
