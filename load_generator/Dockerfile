FROM python:3.9-slim

WORKDIR /app

COPY load_generator.py .

RUN pip install --no-cache-dir requests

CMD ["python", "load_generator.py"]
